"""
data/fetcher.py — GitHub Data Integration
Fetches profile, repos, and commits using PyGithub with parallel processing.
"""

import os
import json
import re
import time
import threading
from datetime import datetime, timezone, timedelta
from github import Github, GithubException, RateLimitExceededException
from concurrent.futures import ThreadPoolExecutor, as_completed

from config import (
    CACHE_DIR, CACHE_TTL_HOURS, REPO_COMMIT_CAP,
    MANIFEST_FILES, BUS_FACTOR_RETRIES, BUS_FACTOR_SLEEP,
    API_WORKERS, MAX_REPOS_TO_ANALYZE, TOTAL_COMMIT_CAP,
    MAX_FILES_PER_REPO_DNA, MAX_REPOS_FOR_CONTRIBUTOR_STATS
)
from utils.sanitize import safe_float, safe_int

class GitHubFetcher:
    def __init__(self, token: str):
        self.g = Github(token, per_page=100) if token else Github(per_page=100)
        self.lock = threading.Lock()
        self.total_commits_fetched = 0

    @staticmethod
    def _to_int(value, default: int = 0) -> int:
        return safe_int(value, default)

    @staticmethod
    def _to_float(value, default: float = 0.0) -> float:
        return safe_float(value, default)

    def get_rate_limit(self):
        """Return rate limit info for the UI."""
        try:
            rate = self.g.get_rate_limit().core
            return {
                "remaining": rate.remaining,
                "limit": rate.limit,
                "reset": rate.reset.strftime("%H:%M:%S")
            }
        except:
            return None

    def _get_stats_contributors_with_retry(self, repo):
        """GitHub computes stats async; retry if it returns None."""
        for _ in range(BUS_FACTOR_RETRIES):
            try:
                stats = repo.get_stats_contributors()
                if stats: return stats
            except: pass
            time.sleep(BUS_FACTOR_SLEEP)
        return []

    def _get_recent_repos(self, user, limit: int):
        """
        Fetch only the most recently pushed public repos without materializing the
        user's entire repository list.
        """
        repos = []
        try:
            repo_pages = user.get_repos(type="public", sort="pushed", direction="desc")
        except TypeError:
            repo_pages = user.get_repos(type="public")

        for repo in repo_pages:
            repos.append(repo)
            if len(repos) >= limit:
                break
        return repos

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
        return self._normalize_cached_data(data)

    def _save_cache(self, username: str, data: dict):
        path = self._cache_path(username)
        data["_cached_at"] = datetime.now(timezone.utc).isoformat()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

    def _normalize_cached_data(self, data: dict) -> dict:
        profile = data.get("profile", {})
        for key in ("public_repos", "followers", "following"):
            profile[key] = self._to_int(profile.get(key, 0))

        normalized_repos = []
        for repo in data.get("repos", []):
            normalized_repo = dict(repo)
            for key in ("stars", "forks", "commit_count", "contributor_count", "open_issues_count"):
                normalized_repo[key] = self._to_int(normalized_repo.get(key, 0))
            normalized_repo["user_share_all_time"] = self._to_float(normalized_repo.get("user_share_all_time", 0.0))
            normalized_repo["bus_factor_ready"] = bool(normalized_repo.get("bus_factor_ready", False))
            normalized_repos.append(normalized_repo)
        data["repos"] = normalized_repos

        normalized_commits = []
        for commit in data.get("commits", []):
            normalized_commit = dict(commit)
            normalized_commit["hour"] = self._to_int(normalized_commit.get("hour", 0))
            timestamp = str(normalized_commit.get("timestamp", "") or normalized_commit.get("date", ""))
            normalized_commit["timestamp"] = timestamp
            normalized_commit["date"] = timestamp
            if "year" not in normalized_commit and len(timestamp) >= 4 and timestamp[:4].isdigit():
                normalized_commit["year"] = int(timestamp[:4])
            normalized_commits.append(normalized_commit)
        data["commits"] = normalized_commits

        data["lang_totals"] = {
            str(lang): self._to_int(value)
            for lang, value in data.get("lang_totals", {}).items()
        }
        data["issues_authored"] = self._to_int(data.get("issues_authored", 0))
        data["prs_authored"] = self._to_int(data.get("prs_authored", 0))
        data["pr_reviews_count"] = self._to_int(data.get("pr_reviews_count", 0))
        data["issue_comments_count"] = self._to_int(data.get("issue_comments_count", 0))
        return data

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
            target_repos = self._get_recent_repos(user, MAX_REPOS_TO_ANALYZE)
        except RateLimitExceededException:
            raise RuntimeError("GitHub rate limit exceeded.")

        self.total_commits_fetched = 0

        def process_repo(repo, index):
            repo_commits = []
            repo_samples = []
            repo_deps = []
            try:
                # 1. Commits (author specific, capped)
                # Check global cap before starting commit loop
                with self.lock:
                    can_fetch_commits = self.total_commits_fetched < TOTAL_COMMIT_CAP
                
                if can_fetch_commits:
                    commits_iter = repo.get_commits(author=username)
                    for commit in commits_iter[:REPO_COMMIT_CAP]:
                        with self.lock:
                            if self.total_commits_fetched >= TOTAL_COMMIT_CAP:
                                break
                            self.total_commits_fetched += 1
                        
                        ts = commit.commit.author.date
                        repo_commits.append({
                            "message": (commit.commit.message or "").split("\n")[0],
                            "timestamp": str(ts),
                            "date": str(ts),
                            "year": ts.year if ts else None,
                            "hour": ts.hour if ts else 0,
                            "weekday": ts.strftime("%A") if ts else "Monday",
                            "repo_lang": repo.language or "Unknown"
                        })

                # 2. Languages & Basic Stats
                raw_langs = repo.get_languages()
                langs = {}
                for lang, value in raw_langs.items():
                    coerced = self._to_int(value, None)
                    if coerced is None:
                        continue
                    langs[lang] = coerced
                
                # 3. SINGLE-PASS CONTENT PEEK
                root_files = []
                try: 
                    root_files = repo.get_contents("")
                except: pass

                has_readme = any(f.name.lower().startswith("readme") for f in root_files)
                has_license = any(f.name.lower().startswith("license") for f in root_files)
                has_ci = any(f.name == ".github" or f.name == ".travis.yml" or f.name == "circle.yml" for f in root_files)
                
                # Extract DNA Samples & Manifests
                code_exts = [".py", ".js", ".ts", ".java", ".cpp", ".go", ".rs", ".rb", ".php"]
                for f in root_files:
                    if f.type == "file":
                        if len(repo_samples) < MAX_FILES_PER_REPO_DNA:
                            if any(f.name.endswith(ext) for ext in code_exts):
                                try:
                                    repo_samples.append({
                                        "repo": repo.name, "path": f.path,
                                        "content": f.decoded_content.decode("utf-8"),
                                        "lang": repo.language
                                    })
                                except: pass
                        if f.name in MANIFEST_FILES:
                            try:
                                content = f.decoded_content.decode("utf-8")
                                if f.name == "package.json":
                                    js = json.loads(content)
                                    repo_deps.extend(js.get("dependencies", {}).keys())
                                elif f.name == "requirements.txt":
                                    repo_deps.extend(re.findall(r"^([a-zA-Z0-9\-_]+)", content, re.MULTILINE))
                                else:
                                    repo_deps.extend(re.findall(r"['\"]([^'\"]+)['\"]", content))
                            except: pass

                recently_active = False
                if repo.pushed_at:
                    recently_active = (datetime.now(timezone.utc) - repo.pushed_at.replace(tzinfo=timezone.utc)).days < 90

                # 4. Bus Factor & Issues
                total_stats = []
                if index < MAX_REPOS_FOR_CONTRIBUTOR_STATS:
                    total_stats = self._get_stats_contributors_with_retry(repo)
                user_share = 0
                contributor_count = 0
                if total_stats:
                    contributor_count = sum(1 for c in total_stats if self._to_int(getattr(c, "total", 0), 0) > 0)
                    total_commits_all = sum(self._to_int(getattr(c, "total", 0), 0) for c in total_stats)
                    if total_commits_all > 0:
                        user_stat = next(
                            (
                                c for c in total_stats
                                if c.author and getattr(c.author, "login", "").lower() == username.lower()
                            ),
                            None
                        )
                        if user_stat:
                            user_share = (self._to_int(getattr(user_stat, "total", 0), 0) / total_commits_all) * 100

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
                        "low_open_issues": repo.open_issues_count < 10,
                        "user_share_all_time": user_share,
                        "contributor_count": contributor_count,
                        "bus_factor_ready": bool(total_stats and contributor_count > 0),
                        "commit_count": len(repo_commits)
                    },
                    "commits": repo_commits,
                    "languages": langs,
                    "samples": repo_samples,
                    "deps": repo_deps
                }
            except:
                return None

        repos_data = []
        all_commits = []
        all_samples = []
        all_deps = {}
        lang_totals = {}

        # Parallelize repo processing
        with ThreadPoolExecutor(max_workers=API_WORKERS) as executor:
            futures = [executor.submit(process_repo, r, i) for i, r in enumerate(target_repos)]
            for future in as_completed(futures):
                res = future.result()
                if res:
                    repos_data.append(res["repo_data"])
                    all_commits.extend(res["commits"])
                    all_samples.extend(res["samples"])
                    if res["deps"]:
                        all_deps[res["repo_data"]["name"]] = res["deps"]
                    for l, v in res["languages"].items():
                        lang_totals[l] = lang_totals.get(l, 0) + v

        # PRs & Issues (Robust totalCount)
        issues_authored = 0
        prs_authored = 0
        pr_reviews_count = 0
        issue_comments_count = 0
        try:
            issue_search = self.g.search_issues(f"author:{username} is:issue is:public")
            prs_search = self.g.search_issues(f"author:{username} is:pr is:public")
            reviews_search = self.g.search_issues(f"reviewed-by:{username} is:pr is:public")
            comments_search = self.g.search_issues(f"commenter:{username} is:issue is:public")
            issues_authored = issue_search.totalCount
            prs_authored = prs_search.totalCount
            pr_reviews_count = reviews_search.totalCount
            issue_comments_count = comments_search.totalCount
        except: pass

        return {
            "profile": profile,
            "repos": repos_data,
            "commits": all_commits,
            "lang_totals": lang_totals,
            "issues_authored": issues_authored,
            "prs_authored": prs_authored,
            "pr_reviews_count": pr_reviews_count,
            "issue_comments_count": issue_comments_count,
            "all_samples": all_samples,
            "all_deps": all_deps
        }

    def get_code_samples(self, username: str, limit: int = 5) -> list:
        """Fetch raw code samples recursively in parallel."""
        samples = []
        try:
            user = self.g.get_user(username)
            repos = self._get_recent_repos(user, 5)
            
            def fetch_from_repo(repo):
                repo_samples = []
                exts = [".py", ".js", ".ts", ".java", ".cpp", ".c", ".go", ".rb", ".rs", ".php", ".swift"]
                try:
                    contents = repo.get_contents("")
                    depth = 0
                    while contents and len(repo_samples) < MAX_FILES_PER_REPO_DNA and depth < 20:
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

            with ThreadPoolExecutor(max_workers=API_WORKERS) as executor:
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
            repos = self._get_recent_repos(user, 15)
            
            def fetch_deps(repo):
                deps = []
                # Use expanded list from config
                manifest_names = MANIFEST_FILES
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
