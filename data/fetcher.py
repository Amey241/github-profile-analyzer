"""
data/fetcher.py — GitHub Data Integration
Fetches profile, repos, and commits using PyGithub with parallel processing.
"""

import os
import json
import re
from datetime import datetime, timezone, timedelta
from github import Github, GithubException, RateLimitExceededException
from concurrent.futures import ThreadPoolExecutor, as_completed

from config import CACHE_DIR, CACHE_TTL_HOURS, LDA_MAX_COMMITS

class GitHubFetcher:
    def __init__(self, token: str):
        self.g = Github(token, per_page=100)

    # ------------------------------------------------------------------ #
    #  Cache helpers
    # ------------------------------------------------------------------ #
    def _cache_path(self, username: str) -> str:
        os.makedirs(CACHE_DIR, exist_ok=True)
        return os.path.join(CACHE_DIR, f"{username}.json")

    def _load_cache(self, username: str):
        path = self._cache_path(username)
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        cached_at = datetime.fromisoformat(data.get("_cached_at", "2000-01-01"))
        age_hours = (datetime.now(timezone.utc) - cached_at.replace(tzinfo=timezone.utc)).total_seconds() / 3600
        if age_hours > CACHE_TTL_HOURS:
            return None
        return data

    def _save_cache(self, username: str, data: dict):
        path = self._cache_path(username)
        data["_cached_at"] = datetime.now(timezone.utc).isoformat()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

    # ------------------------------------------------------------------ #
    #  Public entry point
    # ------------------------------------------------------------------ #
    def get_user_data(self, username: str) -> dict:
        """Return rich dict for *username*. Uses cache if fresh."""
        cached = self._load_cache(username)
        if cached:
            return cached

        data = self._fetch(username)
        self._save_cache(username, data)
        return data

    # ------------------------------------------------------------------ #
    #  Fetching
    # ------------------------------------------------------------------ #
    def _fetch(self, username: str) -> dict:
        try:
            user = self.g.get_user(username)
        except GithubException as e:
            if e.status == 404:
                raise ValueError(f"GitHub user '{username}' not found.")
            raise RuntimeError(f"GitHub API error: {e.data.get('message', str(e))}")

        profile = {
            "login": user.login,
            "name": user.name or user.login,
            "bio": user.bio or "",
            "avatar_url": user.avatar_url,
            "public_repos": user.public_repos,
            "followers": user.followers,
            "following": user.following,
            "created_at": str(user.created_at),
            "location": user.location or "",
            "blog": user.html_url,
        }

        repos_data = []
        all_commits = []
        lang_totals = {}

        try:
            repos = sorted(list(user.get_repos(type="public")), key=lambda r: r.pushed_at, reverse=True)
        except RateLimitExceededException:
            raise RuntimeError("GitHub rate limit exceeded.")

        # Limit to top 30 repos for performance
        target_repos = repos[:30]

        def process_repo(repo, index):
            repo_commits = []
            try:
                # 1. Commits (capped)
                # Ensure we only fetch author's commits
                commits_iter = repo.get_commits(author=username)
                for commit in commits_iter[:REPO_COMMIT_CAP]:
                    author_info = commit.commit.author
                    if author_info and author_info.date:
                        ts = author_info.date
                        repo_commits.append({
                            "message": (commit.commit.message or "").split("\n")[0],
                            "timestamp": str(ts),
                            "hour": ts.hour,
                            "weekday": ts.strftime("%A"),
                            "year": ts.year,
                            "repo_lang": repo.language or "Unknown"
                        })
                
                # 2. Languages
                langs = repo.get_languages()
                
                # 3. Health Signals
                has_readme = False
                try: repo.get_contents("README.md"); has_readme = True
                except: pass
                
                has_license = False
                try: repo.get_license(); has_license = True
                except: pass
                
                has_ci = False
                if index < 15:
                    try: repo.get_contents(".github/workflows"); has_ci = True
                    except: pass
                
                recently_active = False
                if repo.pushed_at:
                    recently_active = (datetime.now(timezone.utc) - repo.pushed_at.replace(tzinfo=timezone.utc)).days < 90

                contributor_count = 1
                try: contributor_count = repo.get_contributors().totalCount
                except: pass

                return {
                    "repo_data": {
                        "name": repo.name,
                        "language": repo.language or "Unknown",
                        "stars": repo.stargazers_count,
                        "forks": repo.forks_count,
                        "updated_at": str(repo.updated_at),
                        "has_readme": has_readme,
                        "has_license": has_license,
                        "has_ci": has_ci,
                        "recently_active": recently_active,
                        "contributor_count": contributor_count,
                        "user_contribution_count": len(repo_commits),
                        "commit_count": repo.get_commits().totalCount if index < 10 else len(repo_commits)
                    },
                    "commits": repo_commits,
                    "languages": langs
                }
            except:
                return None

        # Parallelize repo processing
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(process_repo, r, i) for i, r in enumerate(target_repos)]
            for future in as_completed(futures):
                res = future.result()
                if res:
                    repos_data.append(res["repo_data"])
                    all_commits.extend(res["commits"])
                    for l, v in res["languages"].items():
                        lang_totals[l] = lang_totals.get(l, 0) + v

        # PRs & Issues (Directly from search)
        issues_authored = 0
        prs_authored = 0
        try:
            issues_authored = self.g.search_issues(f"author:{username} is:issue").totalCount
            prs_authored = self.g.search_issues(f"author:{username} is:pr").totalCount
        except: pass

        return {
            "profile": profile,
            "repos": repos_data,
            "commits": all_commits,
            "lang_totals": lang_totals,
            "issues_authored": issues_authored,
            "prs_authored": prs_authored,
        }

    def get_code_samples(self, username: str, limit: int = 5) -> list:
        """Fetch raw code samples recursively in parallel."""
        samples = []
        try:
            user = self.g.get_user(username)
            repos = sorted(user.get_repos(type="public"), key=lambda r: r.pushed_at, reverse=True)[:5]
            
            def fetch_from_repo(repo):
                repo_samples = []
                exts = [".py", ".js", ".ts", ".java", ".cpp", ".c", ".go", ".rb", ".rs", ".php", ".swift"]
                try:
                    contents = repo.get_contents("")
                    depth = 0
                    while contents and len(repo_samples) < 2 and depth < 20:
                        item = contents.pop(0)
                        depth += 1
                        if item.type == "dir" and item.name not in ["node_modules", ".git", "vendor", "dist", "env", "venv"]:
                            try: contents.extend(repo.get_contents(item.path))
                            except: pass
                        elif any(item.name.endswith(ext) for ext in exts):
                            try:
                                repo_samples.append({
                                    "repo": repo.name,
                                    "path": item.path,
                                    "content": item.decoded_content.decode("utf-8"),
                                    "lang": repo.language
                                })
                            except: pass
                except: pass
                return repo_samples

            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(fetch_from_repo, r) for r in repos]
                for future in as_completed(futures):
                    samples.extend(future.result())
                    if len(samples) >= limit: break
        except: pass
        return samples[:limit]

    def get_review_comments(self, username: str, limit: int = 20) -> list:
        """Fetch PR review comments."""
        comments = []
        try:
            query = f"commenter:{username} is:pr"
            issues = self.g.search_issues(query)
            for issue in issues[:10]:
                if issue.pull_request:
                    try:
                        pr = issue.as_pull_request()
                        for review in pr.get_reviews():
                            if review.user and review.user.login == username and review.body:
                                comments.append(review.body)
                                if len(comments) >= limit: return comments
                    except: continue
        except: pass
        return comments

    def get_dependencies(self, username: str, limit: int = 15) -> dict:
        """Fetch and parse manifest files recursively in parallel."""
        repo_deps = {}
        try:
            user = self.g.get_user(username)
            repos = sorted(user.get_repos(type="public"), key=lambda r: r.pushed_at, reverse=True)[:15]
            
            def fetch_deps(repo):
                deps = []
                manifest_names = ["requirements.txt", "package.json", "Gemfile", "go.mod"]
                try:
                    contents = repo.get_contents("")
                    depth = 0
                    while contents and len(deps) < 20 and depth < 30:
                        item = contents.pop(0)
                        depth += 1
                        if item.type == "dir" and item.name not in ["node_modules", ".git", "vendor", "dist", "env", "venv"]:
                            try: contents.extend(repo.get_contents(item.path))
                            except: pass
                        elif item.name in manifest_names:
                            try:
                                content = item.decoded_content.decode("utf-8")
                                if item.name == "package.json":
                                    js = json.loads(content)
                                    deps.extend(js.get("dependencies", {}).keys())
                                    deps.extend(js.get("devDependencies", {}).keys())
                                elif item.name == "requirements.txt":
                                    deps.extend(re.findall(r"^([a-zA-Z0-9\-_]+)", content, re.MULTILINE))
                                else:
                                    deps.extend(re.findall(r"['\"]([^'\"]+)['\"]", content))
                            except: pass
                except: pass
                return repo.name, list(set(deps))

            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(fetch_deps, r) for r in repos]
                for future in as_completed(futures):
                    name, dlist = future.result()
                    if dlist: repo_deps[name] = dlist
        except: pass
        return repo_deps
