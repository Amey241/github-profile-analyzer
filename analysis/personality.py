"""
analysis/personality.py
Rule-based personality badge classifier.
"""
from utils.sanitize import safe_float, safe_int

from config import (
    NIGHT_OWL_THRESHOLD,
    DOC_LOVER_THRESHOLD,
    PROLIFIC_COMMITTER_THRESHOLD,
    WEEKEND_WARRIOR_THRESHOLD,
)


def classify(user_stats: dict) -> list[dict]:
    """
    user_stats keys expected:
      commit_hours: list[int]
      commit_weekdays: list[str]
      repos: list[dict]  (each has 'has_readme', 'commit_count')
      dominant_topic: str
      avg_sentiment: float
      prs_authored: int
      issues_authored: int

    Returns list of {badge, label, description} dicts.
    """
    badges = []
    commits = user_stats.get("commit_hours", [])
    weekdays = user_stats.get("commit_weekdays", [])
    repos = user_stats.get("repos", [])
    dominant_topic = user_stats.get("dominant_topic", "unknown")
    avg_sentiment = user_stats.get("avg_sentiment", 0.0)
    prs = user_stats.get("prs_authored", 0)
    issues = user_stats.get("issues_authored", 0)

    n = len(commits)
    n_repos = len(repos)

    # ---- Night Owl ----
    if n > 0:
        night = sum(1 for h in commits if 0 <= h <= 4)
        if night / n > NIGHT_OWL_THRESHOLD:
            badges.append({
                "badge": "🦉 Night Owl",
                "label": "Night Owl",
                "description": f"{night/n*100:.0f}% of commits happen between midnight and 4 AM.",
            })

    # ---- Weekend Warrior ----
    if weekdays:
        wknd = sum(1 for d in weekdays if d in ("Saturday", "Sunday"))
        if wknd / len(weekdays) > WEEKEND_WARRIOR_THRESHOLD:
            badges.append({
                "badge": "⚡ Weekend Warrior",
                "label": "Weekend Warrior",
                "description": f"{wknd/len(weekdays)*100:.0f}% of commits happen on weekends.",
            })

    # ---- Refactoring Ninja ----
    if dominant_topic == "refactor":
        badges.append({
            "badge": "🥷 Refactoring Ninja",
            "label": "Refactoring Ninja",
            "description": "Commit messages are dominated by cleanup, restructuring, and renaming.",
        })

    # ---- Documentation Lover ----
    if n_repos > 0:
        doc_repos = sum(1 for r in repos if r.get("has_readme"))
        if doc_repos / n_repos > DOC_LOVER_THRESHOLD:
            badges.append({
                "badge": "📖 Documentation Lover",
                "label": "Documentation Lover",
                "description": f"{doc_repos}/{n_repos} repos have a README file.",
            })

    # ---- Prolific Committer ----
    if n_repos > 0:
        avg_commits = sum(safe_float(r.get("commit_count", 0), 0) for r in repos) / n_repos
        if avg_commits > PROLIFIC_COMMITTER_THRESHOLD:
            badges.append({
                "badge": "🔥 Prolific Committer",
                "label": "Prolific Committer",
                "description": f"Averages {avg_commits:.0f} commits per repo.",
            })

    # ---- Bug Hunter ----
    if dominant_topic == "bug":
        badges.append({
            "badge": "🐛 Bug Hunter",
            "label": "Bug Hunter",
            "description": "Most commit messages are focused on fixing bugs and crashes.",
        })

    # ---- Feature Builder ----
    if dominant_topic == "feature":
        badges.append({
            "badge": "🚀 Feature Builder",
            "label": "Feature Builder",
            "description": "Commit history is full of 'add', 'implement', and 'create' — a maker's mindset.",
        })

    # ---- Open Source Contributor ----
    if prs > 50:
        badges.append({
            "badge": "🌍 Open Source Hero",
            "label": "Open Source Hero",
            "description": f"Has authored {prs} pull requests across GitHub.",
        })

    # ---- Issue Tracker ----
    if issues > 100:
        badges.append({
            "badge": "🎯 Issue Tracker",
            "label": "Issue Tracker",
            "description": f"Has filed {issues} issues — a thorough quality-minded developer.",
        })

    # ---- Zen Coder (very positive sentiment) ----
    if avg_sentiment > 0.20:
        badges.append({
            "badge": "🧘 Zen Coder",
            "label": "Zen Coder",
            "description": "Commit messages are overwhelmingly upbeat and positive.",
        })

    # Fallback
    if not badges:
        badges.append({
            "badge": "💻 Dedicated Developer",
            "label": "Dedicated Developer",
            "description": "A consistent, steady contributor to open source.",
        })

    return badges

def generate_narrative(user_stats: dict, profile: dict) -> str:
    """
    Generate a 3-sentence narrative about the developer.
    """
    name = profile.get("name") or profile.get("login")
    commits = user_stats.get("commit_hours", [])
    n_commits = len(commits)
    
    # Sentence 1: Archetype and Volume
    night = sum(1 for h in commits if 0 <= h <= 4)
    time_pref = "nocturnal" if (n_commits > 0 and night / n_commits > 0.3) else "disciplined" if n_commits > 0 else "occasional"
    
    topics = user_stats.get("dominant_topic", "general")
    archetype = {"bug": "bug hunter", "feature": "builder", "refactor": "craftsperson", "docs": "clarity seeker"}.get(topics, "developer")
    
    created_at = profile.get("created_at", "2020")
    year = created_at[:4] if created_at else "recent years"
    
    s1 = f"{name} is a {time_pref} {archetype} who has quietly shipped {n_commits} commits since {year}."

    # Sentence 2: Habits and Tone
    weekdays = user_stats.get("commit_weekdays", [])
    wknd = sum(1 for d in weekdays if d in ("Saturday", "Sunday"))
    habit = "spending most weekends refactoring" if wknd / (len(weekdays) or 1) > 0.4 else "maintaining a steady weekday rhythm"
    
    sent = user_stats.get("avg_sentiment", 0.0)
    tone = "unusually calm" if sent > 0.1 else "pragmatic" if sent > -0.1 else "intense"
    s2 = f"They are known for {habit}, with a commit tone that is {tone}."

    # Sentence 3: Impact/Focus
    repos = user_stats.get("repos", [])
    n_repos = len(repos)
    doc_repos = sum(1 for r in repos if r.get("has_readme"))
    doc_pct = int(doc_repos / n_repos * 100) if n_repos > 0 else 0
    focus = "humans first" if doc_pct > 70 else "execution first"
    s3 = f"They write for {focus} — {doc_pct}% of repos have READMEs."

    return f"{s1} {s2} {s3}"

def achievement_trophy_case(user_stats: dict, profile: dict, lang_df: any) -> list[dict]:
    """
    Define and unlock hidden achievements.
    Returns list of {id, name, emoji, description, unlocked: bool}.
    """
    achievements = [
        {"id": "moonlighter", "name": "Moonlighter", "emoji": "🌙", "desc": "500+ commits between midnight and 4am", "unlocked": False},
        {"id": "summit_seeker", "name": "Summit Seeker", "emoji": "🏔️", "desc": "Repo with 1000+ stars", "unlocked": False},
        {"id": "polyglot", "name": "Polyglot", "emoji": "🗣️", "desc": "7+ languages used meaningfully", "unlocked": False},
        {"id": "clean_slate", "name": "Clean Slate", "emoji": "🧹", "desc": "Refactor topic dominates 40%+ of commits", "unlocked": False},
        {"id": "correspondent", "name": "The Correspondent", "emoji": "📬", "desc": "200+ issue comments authored", "unlocked": False},
    ]
    
    commits = user_stats.get("commit_hours", [])
    night = sum(1 for h in commits if 0 <= h <= 4)
    if night >= 500: achievements[0]["unlocked"] = True
    
    repos = user_stats.get("repos", [])
    if any(safe_int(r.get("stars", 0), 0) >= 1000 for r in repos): achievements[1]["unlocked"] = True
    
    if len(lang_df) >= 7: achievements[2]["unlocked"] = True
    
    if user_stats.get("dominant_topic") == "refactor": achievements[3]["unlocked"] = True # Simplified check
    
    if safe_int(user_stats.get("issues_authored", 0), 0) >= 200: achievements[4]["unlocked"] = True

    return achievements

def time_capsule_message(arc_df: any, profile: dict) -> str:
    """
    Cinematic message based on career evolution.
    """
    if arc_df.empty:
        return "You're just getting started on your journey. Keep building!"

    first_year_row = arc_df.iloc[0]
    last_year_row = arc_df.iloc[-1]
    
    first_year = first_year_row["year"]
    last_year = last_year_row["year"]
    
    if first_year == last_year:
        return f"In {first_year}, you began your journey with {first_year_row['language']}. The future is wide open."

    msg = f"In {first_year}, you wrote your first analyzed commits in {first_year_row['language']}."
    if first_year_row['sentiment'] < 0:
        msg += " You seemed frustrated back then."
    
    msg += f" By {last_year}, you had evolved into a {last_year_row['language']} specialist with a focus on {last_year_row['topic']}."
    
    if last_year_row['sentiment'] > first_year_row['sentiment']:
        msg += " The bet paid off — your tone is noticeably calmer now."
    
    return msg
