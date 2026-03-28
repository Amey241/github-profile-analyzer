"""
analysis/deep_metrics.py
Advanced data metrics like Bus Factor, Invisible Work, and Streak Intelligence.
"""

from datetime import datetime, timedelta
import pandas as pd
from utils.sanitize import safe_float, safe_int

def estimate_bus_factor(repos: list[dict]) -> dict:
    """
    Estimate the 'Bus Factor' (risk of project knowledge being centralized).
    """
    factors = []
    for r in repos:
        if not r.get("bus_factor_ready"):
            continue
        # Use full-history share if available (provided by fetcher)
        user_share = safe_float(r.get("user_share_all_time", 0), 0)
        n_contribs = max(safe_int(r.get("contributor_count", 1), 1), 1)
        
        # Heuristic for project sustainability:
        # If one person does 80%+ work (all time), factor is 1 (high risk)
        if user_share > 80:
            factor = 1
        elif user_share > 50:
            factor = 2
        else:
            # Scale factor based on number of contributors
            factor = 3 + min(n_contribs // 3, 7)
            
        factors.append({
            "repo": r["name"],
            "factor": factor,
            "user_share": round(user_share, 1),
            "n_contribs": n_contribs
        })
    
    if not factors:
        return {"factors": [], "avg_factor": 0, "risk": "Not enough data", "repos_analyzed": 0}
        
    avg_factor = sum(f["factor"] for f in factors) / len(factors)
    risk = "High 🔴" if avg_factor < 1.5 else "Medium 🟡" if avg_factor < 3 else "Low 🟢"
    
    return {"factors": factors, "avg_factor": round(avg_factor, 1), "risk": risk, "repos_analyzed": len(factors)}

def calculate_streaks(commits: list[dict]) -> dict:
    """
    Calculate commit streaks.
    """
    if not commits:
        return {"current": 0, "longest": 0}

    date_strings = []
    for commit in commits:
        raw_date = commit.get("date") or commit.get("timestamp")
        if not raw_date:
            continue
        raw_date = str(raw_date)
        normalized = raw_date.split("T")[0].split(" ")[0]
        if normalized:
            date_strings.append(normalized)

    dates = sorted(list(set(date_strings)), reverse=True)
    if not dates:
        return {"current": 0, "longest": 0}

    # Current streak
    current = 0
    today = datetime.now().date()
    # Check if first commit is within 1 day of today
    last_commit_date = datetime.strptime(dates[0], "%Y-%m-%d").date()
    if (today - last_commit_date).days <= 1:
        current = 1
        for i in range(len(dates) - 1):
            d1 = datetime.strptime(dates[i], "%Y-%m-%d").date()
            d2 = datetime.strptime(dates[i+1], "%Y-%m-%d").date()
            if (d1 - d2).days == 1:
                current += 1
            else:
                break
    
    # Longest streak
    longest = 0
    temp = 1
    for i in range(len(dates) - 1):
        d1 = datetime.strptime(dates[i], "%Y-%m-%d").date()
        d2 = datetime.strptime(dates[i+1], "%Y-%m-%d").date()
        if (d1 - d2).days == 1:
            temp += 1
        else:
            longest = max(longest, temp)
            temp = 1
    longest = max(longest, temp)
    
    return {"current": current, "longest": longest}

def invisible_work_audit(user_data: dict) -> dict:
    """
    Highlight PR reviews, issues, and discussions.
    """
    prs = safe_int(user_data.get("prs_authored", 0), 0)
    issues = safe_int(user_data.get("issues_authored", 0), 0)
    reviews = safe_int(user_data.get("pr_reviews_count", 0), 0)
    issue_comments = safe_int(user_data.get("issue_comments_count", 0), 0)
    return {
        "prs": prs,
        "issues": issues,
        "reviews": reviews,
        "issue_comments": issue_comments,
        "total_impact": (prs * 3) + (reviews * 2) + issues + issue_comments,
        "invisible_pct": round(((reviews + issues + issue_comments) / max(prs + reviews + issues + issue_comments, 1)) * 100),
        "is_empty": (prs + issues + reviews + issue_comments) == 0
    }

def ghost_repo_audit(repos: list[dict]) -> list:
    """
    Detect zombie repos (no activity for 1 year).
    """
    ghosts = []
    one_year_ago = datetime.now() - timedelta(days=365)
    for r in repos:
        updated_at = datetime.strptime(r["updated_at"][:19], "%Y-%m-%d %H:%M:%S")
        if updated_at < one_year_ago:
            ghosts.append({
                "name": r["name"],
                "last_updated": r["updated_at"][:10],
                "stars": r["stars"]
            })
    return sorted(ghosts, key=lambda x: x["stars"], reverse=True)
