"""
app.py — GitHub Profile Analyzer
Main Streamlit application entry point.
"""

import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ------------------------------------------------------------------ #
#  Page config — MUST be first Streamlit call
# ------------------------------------------------------------------ #
st.set_page_config(
    page_title="GitHub Profile Analyzer",
    page_icon="🔭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ------------------------------------------------------------------ #
#  Custom CSS
# ------------------------------------------------------------------ #
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

  html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

  .stApp {
    background: linear-gradient(135deg, #0f0c29 0%, #1a1040 40%, #24243e 100%);
    color: #FFFFFF;
  }

  section[data-testid="stSidebar"] {
    background: #1a1040 !important;
    border-right: 1px solid rgba(255,255,255,0.15);
    backdrop-filter: blur(20px);
  }

  .glass-card {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 16px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    backdrop-filter: blur(12px);
    color: #FFFFFF;
  }

  .profile-header {
    display: flex;
    align-items: center;
    gap: 1.5rem;
    padding: 1.5rem;
    background: linear-gradient(135deg, rgba(108,99,255,0.20), rgba(236,72,153,0.10));
    border: 1px solid rgba(108,99,255,0.3);
    border-radius: 20px;
    margin-bottom: 1.5rem;
  }
  .profile-header img {
    width: 90px; height: 90px;
    border-radius: 50%;
    border: 3px solid #6C63FF;
    box-shadow: 0 0 20px rgba(108,99,255,0.4);
  }
  .profile-name {
    font-size: 1.8rem; font-weight: 800;
    color: #FFFFFF;
    text-shadow: 0 2px 10px rgba(0,0,0,0.3);
  }

  .stat-row { display: flex; gap: 0.75rem; flex-wrap: wrap; margin-top: 0.75rem; }
  .stat-pill {
    background: rgba(108,99,255,0.25);
    border: 1px solid rgba(108,99,255,0.45);
    border-radius: 999px;
    padding: 0.25rem 0.75rem;
    font-size: 0.8rem;
    color: #DDD6FE;
    font-weight: 600;
  }

  .badge-card {
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 14px;
    padding: 1rem 1.25rem;
    margin-bottom: 0.75rem;
    transition: transform 0.2s;
  }
  .badge-card:hover {
    transform: translateY(-2px);
    border-color: #6C63FF;
  }
  .badge-title { font-size: 1.1rem; font-weight: 700; color: #FFFFFF; }
  .badge-desc  { font-size: 0.85rem; color: #CBD5E1; margin-top: 0.2rem; }

  .section-header {
    font-size: 1.25rem; font-weight: 800;
    color: #FFFFFF;
    letter-spacing: 0.02em;
    margin-bottom: 0.6rem;
    border-left: 5px solid #6C63FF;
    padding-left: 0.75rem;
  }

  .sentiment-bar-wrap {
    height: 12px; border-radius: 999px;
    background: rgba(255,255,255,0.1);
    overflow: hidden; margin: 0.5rem 0;
  }
  .sentiment-bar { height: 100%; border-radius: 999px; }

  .topic-pill {
    display: inline-block;
    background: rgba(168,85,247,0.2);
    border: 1px solid rgba(168,85,247,0.4);
    border-radius: 8px;
    padding: 0.15rem 0.6rem;
    font-size: 0.75rem;
    color: #E9D5FF;
    margin: 0.15rem;
    font-weight: 600;
  }

  /* Repo Health Pills */
  .health-pill {
    padding: 0.1rem 0.5rem;
    border-radius: 4px;
    font-size: 0.7rem;
    font-weight: 800;
    text-transform: uppercase;
  }
  .health-pass { background: rgba(34, 197, 94, 0.2); color: #4ade80; border: 1px solid rgba(34, 197, 94, 0.4); }
  .health-fail { background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.4); }

  /* Comparison Styles */
  .comp-label {
    font-size: 0.8rem; color: #CBD5E1; margin-bottom: 0.2rem; font-weight: 600;
  }
  .comp-value {
    font-size: 1.2rem; font-weight: 800; color: #FFFFFF;
  }

  #MainMenu, footer { visibility: hidden; }

  input[type=text], .stTextInput input {
    background: rgba(0, 0, 0, 0.5) !important;
    border: 1px solid rgba(108,99,255,0.6) !important;
    border-radius: 12px !important;
    color: #FFFFFF !important;
    font-size: 1.1rem !important;
    padding: 0.75rem 1rem !important;
  }
  
  .stTextInput input:focus {
    border: 1px solid #6C63FF !important;
    box-shadow: 0 0 15px rgba(108,99,255,0.3) !important;
  }

  /* Specific Button Contrast Fixes */
  .stDownloadButton button {
    background-color: #FFFFFF !important;
    color: #000000 !important;
    font-weight: 700 !important;
  }
  .stButton button {
    background-color: rgba(108, 99, 255, 0.2) !important;
    color: #FFFFFF !important;
    border: 1px solid rgba(108, 99, 255, 0.5) !important;
    font-weight: 600 !important;
  }

  /* Sidebar Visibility Fixes */
  section[data-testid="stSidebar"] {
    color: #FFFFFF !important;
  }
  section[data-testid="stSidebar"] p, 
  section[data-testid="stSidebar"] span, 
  section[data-testid="stSidebar"] label {
    color: #FFFFFF !important;
    font-weight: 500 !important;
  }
  section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h1,
  section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2,
  section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3 {
    color: #FFFFFF !important;
  }

  /* Remove Streamlit white header bar */
  header[data-testid="stHeader"], 
  .stAppHeader {
    background: transparent !important;
  }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------ #
#  Helpers
# ------------------------------------------------------------------ #
def _topic_emoji(label: str) -> str:
    return {"bug": "🐛", "feature": "🚀", "refactor": "🥷", "docs": "📖"}.get(label, "💡")


def _render_topics(topics_data: dict) -> None:
    if not topics_data.get("topics"):
        return
    dominant = topics_data["dominant_topic"]
    emoji = _topic_emoji(dominant)
    st.markdown(f"""
    <div class="glass-card">
      <div style="font-weight:600;color:#CBD5E1;margin-bottom:0.5rem;text-transform:uppercase;font-size:0.75rem;">🗂 Dominant Commit Theme</div>
      <div style="font-size:1.5rem;font-weight:800;color:#FFFFFF;margin-bottom:0.75rem;">
        {emoji} {dominant.title()}
      </div>
    """, unsafe_allow_html=True)

    for t in topics_data["topics"]:
        words_html = " ".join(f'<span class="topic-pill">{w}</span>' for w in t["top_words"])
        st.markdown(
            f'<div style="margin-bottom:0.4rem;">'
            f'<span style="color:#CBD5E1;font-size:0.8rem;">Topic {t["index"]+1} ({t["label"]}):</span><br>'
            f'{words_html}</div>',
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)


# ------------------------------------------------------------------ #
#  Imports
# ------------------------------------------------------------------ #
import re
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image
from datetime import datetime
import nltk

# Initialize NLTK data for Streamlit Cloud
@st.cache_resource
def setup_nltk():
    try:
        nltk.download('punkt', quiet=True)
        nltk.download('brown', quiet=True)
        nltk.download('stopwords', quiet=True)
    except Exception:
        pass

setup_nltk()

from config import *
from data.fetcher import GitHubFetcher
from analysis.languages import aggregate_languages, radar_chart, bar_chart
from analysis.activity import build_heatmap_data, activity_heatmap, peak_hours_summary
from analysis.nlp import sentiment_analysis, lda_topics
from analysis.personality import classify, generate_narrative, achievement_trophy_case, time_capsule_message
from analysis.wordcloud_gen import generate_wordcloud
from analysis.card_generator import generate_card
from analysis.commit_quality import score_commits
from analysis.comparison import overlay_radar, compatibility_score, highlight_differences
from analysis.repo_health import score_repo, aggregate_health
from analysis.career_arc import analyze_career_arc, career_arc_timeline
from analysis.code_dna import analyze_style, generate_dna_svg
from analysis.ecosystem import build_ecosystem_graph
from analysis.ai_insights import AIInsights
from analysis.deep_metrics import estimate_bus_factor, calculate_streaks, invisible_work_audit, ghost_repo_audit


# ------------------------------------------------------------------ #
#  Cached Pipeline
# ------------------------------------------------------------------ #
@st.cache_data(ttl=3600, show_spinner=False)
def run_pipeline(username: str, token: str) -> dict:
    fetcher = GitHubFetcher(token)
    raw = fetcher.get_user_data(username)

    commits = raw["commits"]
    messages = [c["message"] for c in commits]
    hours    = [c["hour"]    for c in commits]
    weekdays = [c["weekday"] for c in commits]

    lang_df       = aggregate_languages(raw["lang_totals"])
    heatmap_pivot = build_heatmap_data(commits)
    activity      = peak_hours_summary(heatmap_pivot)
    sentiment     = sentiment_analysis(messages)
    topics        = lda_topics(messages)
    wc_path       = generate_wordcloud(messages, username)

    # Commit Quality
    quality = score_commits(messages)

    # Repo Health
    repo_scores = [score_repo(r) for r in raw["repos"]]
    health_stats = aggregate_health(repo_scores)

    user_stats = {
        "commit_hours":   hours,
        "commit_weekdays": weekdays,
        "repos":          raw["repos"],
        "dominant_topic": topics["dominant_topic"],
        "avg_sentiment":  sentiment["avg_polarity"],
        "prs_authored":   raw["prs_authored"],
        "issues_authored": raw["issues_authored"],
        "followers":       raw["profile"].get("followers", 0),
    }
    badges = classify(user_stats)
    narrative = generate_narrative(user_stats, raw["profile"])
    achievements = achievement_trophy_case(user_stats, raw["profile"], lang_df)

    # Career Arc
    try:
        arc_df = analyze_career_arc(commits)
        arc_viz = career_arc_timeline(arc_df)
        capsule = time_capsule_message(arc_df, raw["profile"])
    except Exception:
        arc_df, arc_viz, capsule = pd.DataFrame(), None, ""

    # Code DNA
    try:
        samples = fetcher.get_code_samples(username)
        dna_traits = analyze_style(samples)
        dna_svg = generate_dna_svg(dna_traits)
    except Exception:
        dna_traits, dna_svg = {}, ""

    # Dependency Ecosystem
    try:
        repo_deps = fetcher.get_dependencies(username)
        ecosystem_html = build_ecosystem_graph(repo_deps)
    except Exception:
        ecosystem_html = ""

    # AI Insights
    try:
        ai = AIInsights()
        job_roles = ai.get_job_role_suggestions(user_stats, lang_df)
        review_comments = fetcher.get_review_comments(username)
        review_personality = ai.analyze_review_personality(review_comments)
        low_q_commits = [m for m, s, g in quality.get("worst_examples", [])[:3]]
        rewrites = ai.suggest_commit_rewrites(low_q_commits)
    except Exception:
        job_roles, review_personality, rewrites = [], {"archetype": "The Observer", "trait": "Neutral", "advice": ""}, []

    # Deep Metrics
    try:
        bus_stats = estimate_bus_factor(raw["repos"])
        streak_stats = calculate_streaks(commits)
        invisible_stats = invisible_work_audit({
            "prs_authored": raw["prs_authored"],
            "issues_authored": raw["issues_authored"],
            "review_comments": review_comments if 'review_comments' in locals() else []
        })
        ghosts = ghost_repo_audit(raw["repos"])
    except Exception:
        bus_stats = {"factors": [], "avg_factor": 0, "risk": "Unknown"}
        streak_stats = {"current": 0, "longest": 0}
        invisible_stats = {"prs": 0, "issues": 0, "reviews": 0, "total_impact": 0}
        ghosts = []

    return {
        "profile": raw["profile"],
        "repos": raw["repos"],
        "lang_df": lang_df,
        "heatmap_pivot": heatmap_pivot,
        "activity": activity,
        "sentiment": sentiment,
        "topics": topics,
        "badges": badges,
        "wc_path": wc_path,
        "commits": commits,
        "quality": quality,
        "repo_scores": repo_scores,
        "health_stats": health_stats,
        "user_stats": user_stats,
        "arc_df": arc_df,
        "arc_viz": arc_viz,
        "dna_traits": dna_traits,
        "dna_svg": dna_svg,
        "ecosystem_html": ecosystem_html,
        "narrative": narrative,
        "achievements": achievements,
        "capsule": capsule,
        "job_roles": job_roles,
        "review_personality": review_personality,
        "rewrites": rewrites,
        "bus_stats": bus_stats,
        "streak_stats": streak_stats,
        "invisible_stats": invisible_stats,
        "ghosts": ghosts,
    }


# ------------------------------------------------------------------ #
#  Sidebar
# ------------------------------------------------------------------ #
with st.sidebar:
    st.markdown("## 🔭 GitHub Analyzer")
    st.markdown("Uncover any developer's coding personality through data.")
    st.divider()

    env_token = os.getenv("GITHUB_TOKEN", "")
    token_input = st.text_input(
        "GitHub Personal Access Token",
        value=env_token,
        type="password",
        placeholder="ghp_xxxxxxxxxxxx",
        help="Generate at github.com/settings/tokens — no scopes needed for public repos.",
    )
    token = token_input or env_token

    st.divider()
    mode = st.radio("Analysis Mode", ["Single Profile", "Compare Mode"], index=0)

    st.divider()
    st.markdown("**How to use**")
    st.markdown("""
1. Paste your GitHub token above  
2. Enter username(s)  
3. Hit **Enter** — wait ~30 s  
4. Explore the insights!
    """)
    st.divider()
    st.caption("Rate limit: 5,000 req/hr with token. Results cached 1 hr.")


# ------------------------------------------------------------------ #
#  Main header
# ------------------------------------------------------------------ #
st.markdown("""
<div style="text-align:center; padding: 1.5rem 0 1rem;">
  <span style="font-size:2.5rem; font-weight:800;
    background: linear-gradient(90deg, #6C63FF, #EC4899, #F9A826);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
    background-clip:text;">
    GitHub Profile Analyzer
  </span>
  <p style="color:#94A3B8; margin-top:0.4rem; font-size:0.95rem;">
    Data-driven personality insights from commit history
  </p>
</div>
""", unsafe_allow_html=True)

if mode == "Single Profile":
    username = st.text_input(
        "GitHub Username",
        placeholder="🔍  Enter a GitHub username (e.g. torvalds, gvanrossum)",
        label_visibility="collapsed",
    )
else:
    c1, c2 = st.columns(2)
    with c1:
        u1 = st.text_input("First Developer", placeholder="e.g. torvalds")
    with c2:
        u2 = st.text_input("Second Developer", placeholder="e.g. gvanrossum")
    username = (u1, u2) if (u1 and u2) else None

if not token:
    st.warning("⚠️ Please add your GitHub Personal Access Token in the sidebar.")
    st.stop()

if not username:
    st.markdown("""
    <div style="display:flex; gap:1rem; flex-wrap:wrap; justify-content:center; margin-top:2rem;">
      <div class="glass-card" style="text-align:center; min-width:130px;">
        <div style="font-size:2rem;">🐧</div>
        <div style="color:#FFFFFF; font-weight:800;">torvalds</div>
        <div style="color:#CBD5E1; font-size:0.8rem;">Linux kernel</div>
      </div>
      <div class="glass-card" style="text-align:center; min-width:130px;">
        <div style="font-size:2rem;">🐍</div>
        <div style="color:#FFFFFF; font-weight:800;">gvanrossum</div>
        <div style="color:#CBD5E1; font-size:0.8rem;">Python creator</div>
      </div>
      <div class="glass-card" style="text-align:center; min-width:130px;">
        <div style="font-size:2rem;">🦀</div>
        <div style="color:#FFFFFF; font-weight:800;">nikomatsakis</div>
        <div style="color:#CBD5E1; font-size:0.8rem;">Rust core dev</div>
      </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()


# ------------------------------------------------------------------ #
#  Run analysis
# ------------------------------------------------------------------ #
try:
    if isinstance(username, str):
        with st.spinner(f"🔍 Analysing **{username}**'s GitHub profile…"):
            data = run_pipeline(username.strip(), token)
            data_list = [data]
    else:
        with st.spinner(f"⚔️ Comparing **{username[0]}** vs **{username[1]}**…"):
            data_a = run_pipeline(username[0].strip(), token)
            data_b = run_pipeline(username[1].strip(), token)
            data_list = [data_a, data_b]
except ValueError as e:
    st.error(f"❌ {e}")
    st.stop()
except RuntimeError as e:
    st.error(f"⚠️ {e}")
    st.stop()
except Exception as e:
    st.error(f"Unexpected error: {e}")
    st.stop()

if len(data_list) == 2:
    # ── COMPARISON MODE ──────────────────────────────────────────────────────
    d1, d2 = data_list[0], data_list[1]
    p1, p2 = d1["profile"], d2["profile"]

    st.markdown(f"""
    <div style="display:flex; justify-content:space-around; align-items:center; margin-bottom:2rem;">
        <div style="text-align:center;">
            <img src="{p1['avatar_url']}" style="width:100px; height:100px; border-radius:50%; border:3px solid #6C63FF; box-shadow:0 0 15px rgba(108,99,255,0.4); mb:0.5rem;" />
            <div style="font-size:1.4rem; font-weight:800; color:#FFFFFF;">{p1['name']}</div>
            <div style="color:#CBD5E1;">@{p1['login']}</div>
        </div>
        <div style="font-size:3rem; font-weight:900; color:rgba(255,255,255,0.1); font-style:italic;">VS</div>
        <div style="text-align:center;">
            <img src="{p2['avatar_url']}" style="width:100px; height:100px; border-radius:50%; border:3px solid #EC4899; box-shadow:0 0 15px rgba(236,72,153,0.4); mb:0.5rem;" />
            <div style="font-size:1.4rem; font-weight:800; color:#FFFFFF;">{p2['name']}</div>
            <div style="color:#CBD5E1;">@{p2['login']}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 1. Compatibility Score
    comp = compatibility_score(d1["user_stats"], d2["user_stats"], d1["lang_df"], d2["lang_df"])
    st.markdown(f"""
    <div class="glass-card" style="text-align:center; border:1px solid rgba(249,168,38,0.4);">
        <div style="color:#CBD5E1; font-size:0.8rem; font-weight:700; text-transform:uppercase; letter-spacing:0.1em;">Compatibility Score</div>
        <div style="font-size:3.5rem; font-weight:800; color:#F9A826; margin:0.5rem 0;">{comp['score']}%</div>
        <div style="font-size:1.2rem; font-weight:600; color:#FFFFFF;">{comp['label']}</div>
    </div>
    """, unsafe_allow_html=True)

    # 2. Insights & Radar
    col_l, col_r = st.columns([1, 1.2])
    with col_l:
        st.markdown('<div class="section-header">🔍 Key Differences</div>', unsafe_allow_html=True)
        diffs = highlight_differences(d1["user_stats"], d2["user_stats"], p1["login"], p2["login"])
        for d in diffs:
            st.markdown(f'<div class="badge-card" style="padding:0.75rem 1rem; margin-bottom:0.5rem;">{d}</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="section-header" style="margin-top:1.5rem;">🤝 Team Insights</div>', unsafe_allow_html=True)
        for ins in comp["insights"]:
            st.markdown(f'<div style="color:#FFFFFF; font-size:0.9rem; margin-bottom:0.4rem;">{ins}</div>', unsafe_allow_html=True)

    with col_r:
        st.markdown('<div class="section-header">🌐 Language Overlap</div>', unsafe_allow_html=True)
        st.plotly_chart(overlay_radar(d1["lang_df"], d2["lang_df"], p1["login"], p2["login"]), use_container_width=True)

else:
    # ── SINGLE PROFILE MODE ──────────────────────────────────────────────────
    data = data_list[0]
    profile       = data["profile"]
    lang_df       = data["lang_df"]
    heatmap_pivot = data["heatmap_pivot"]
    activity      = data["activity"]
    sentiment     = data["sentiment"]
    topics        = data["topics"]
    badges        = data["badges"]
    wc_path       = data["wc_path"]
    repos         = data["repos"]
    commits       = data["commits"]
    quality       = data["quality"]
    repo_scores   = data["repo_scores"]
    health_stats  = data["health_stats"]

    # Header with Card Generator
    c1, c2 = st.columns([3, 1])
    with c1:
        st.markdown(f"""
        <div class="profile-header">
          <img src="{profile['avatar_url']}" alt="avatar" />
          <div>
            <div class="profile-name">{profile['name']}</div>
            <div style="color:#E2E8F0;font-size:0.9rem;">@{profile['login']}</div>
            <div style="color:#CBD5E1;font-size:0.85rem;margin-top:0.2rem;">{profile['bio']}</div>
            <div style="color:#FFFFFF; font-style:italic; font-size:1rem; margin-top:1rem; line-height:1.4;">
              "{data['narrative']}"
            </div>
            <div class="stat-row">
              <span class="stat-pill">📁 {profile['public_repos']} repos</span>
              <span class="stat-pill">👥 {profile['followers']} followers</span>
              <span class="stat-pill">💬 {len(commits)} commits analysed</span>
            </div>
            <div style="display:flex; gap:1.5rem; margin-top:0.8rem;">
               <div style="text-align:center;">
                 <div style="font-size:1.2rem; font-weight:800; color:#EC4899;">{data['streak_stats']['current']}</div>
                 <div style="font-size:0.65rem; color:#CBD5E1; text-transform:uppercase;">Current Streak</div>
               </div>
               <div style="text-align:center;">
                 <div style="font-size:1.2rem; font-weight:800; color:#6C63FF;">{data['streak_stats']['longest']}</div>
                 <div style="font-size:0.65rem; color:#CBD5E1; text-transform:uppercase;">Longest Streak</div>
               </div>
               <div style="text-align:center;">
                 <div style="font-size:1.2rem; font-weight:800; color:#22D3EE;">{data['invisible_stats']['total_impact']}</div>
                 <div style="font-size:0.65rem; color:#CBD5E1; text-transform:uppercase;">Community Impact</div>
               </div>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown('<div style="height:25px;"></div>', unsafe_allow_html=True)
        card_bytes = generate_card(profile, badges, lang_df, sentiment, commits, profile["login"])
        st.download_button(
            label="🎨 Download Wrapped Card",
            data=card_bytes,
            file_name=f"{profile['login']}_wrapped.png",
            mime="image/png",
            use_container_width=True,
        )
        st.button("✨ Share on X (Twitter)", use_container_width=True, disabled=True)

    # Badges
    st.markdown('<div class="section-header">🏅 Personality Badges</div>', unsafe_allow_html=True)
    n_cols = min(len(badges), 3)
    badge_cols = st.columns(n_cols)
    for i, b in enumerate(badges):
        with badge_cols[i % n_cols]:
            st.markdown(f"""
            <div class="badge-card">
              <div class="badge-title">{b['badge']}</div>
              <div class="badge-desc">{b['description']}</div>
            </div>
            """, unsafe_allow_html=True)

    st.divider()
    
    # Feature 1: Code DNA Fingerprint (conditional divider)
    if data.get("dna_svg"):
        st.divider()
        st.markdown('<div class="section-header">🧬 Code DNA Fingerprint</div>', unsafe_allow_html=True)
        col1, col2 = st.columns([1, 1.5], gap="large")
        with col1:
            # Inline the SVG with scaling
            st.markdown(f'<div style="text-align:center; background: rgba(255,255,255,0.03); border-radius:30px; padding:20px;">{data["dna_svg"]}</div>', unsafe_allow_html=True)
        with col2:
            st.markdown("Every developer has unconscious stylistic patterns. We've mapped your unique coding fingerprint based on your most recent work.")
            traits = data.get("dna_traits", {})
            st.markdown(f"""
            <div class="glass-card" style="padding:1.5rem; border-color:#6C63FF;">
                <div style="display:grid; grid-template-columns: 1fr 1fr; gap:1.5rem;">
                    <div>
                        <div style="color:#94A3B8; font-size:0.8rem;">Comment Density</div>
                        <div style="font-size:1.3rem; font-weight:700;">{traits.get('comment_density', 0):.1f}%</div>
                    </div>
                    <div>
                        <div style="color:#94A3B8; font-size:0.8rem;">Brace Style</div>
                        <div style="font-size:1.3rem; font-weight:700;">{traits.get('brace_style', 'Standard').replace('_', ' ').title()}</div>
                    </div>
                    <div>
                        <div style="color:#94A3B8; font-size:0.8rem;">Naming</div>
                        <div style="font-size:1.3rem; font-weight:700;">{traits.get('naming', 'Default')}</div>
                    </div>
                    <div>
                        <div style="color:#94A3B8; font-size:0.8rem;">Indentation</div>
                        <div style="font-size:1.3rem; font-weight:700;">{traits.get('indent', 'Spaces').title()}</div>
                    </div>
                </div>
                <div style="margin-top:1.5rem; padding-top:1rem; border-top:1px solid rgba(108,99,255,0.2);">
                    <div style="color:#94A3B8; font-size:0.8rem;">Avg Function Length</div>
                    <div style="font-size:1.3rem; font-weight:700;">{traits.get('avg_func_len', 15):.0f} lines</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    # Feature 2 & 6: Developer Archetype & Story
    if data.get("narrative") or data.get("capsule"):
        st.divider()
        st.markdown('<div class="section-header">📜 Developer Archetype & Story</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="glass-card" style="padding:2rem; border-left: 5px solid #F9A826;">
            <div style="font-size:1.2rem; line-height:1.7; font-style:italic; color:#E2E8F0;">
                "{data.get('narrative', 'Your story is still being written...')}"
            </div>
            <div style="margin-top:1.5rem; padding:1rem; background:rgba(249,168,38,0.1); border-radius:10px; border: 1px dashed rgba(249,168,38,0.3);">
                <div style="font-size:0.8rem; color:#F9A826; font-weight:700; text-transform:uppercase;">Time Capsule Reflection</div>
                <div style="margin-top:0.5rem; color:#E2E8F0;">{data.get('capsule', 'Keep pushing commits to see your career evolution.')}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Feature 12: Hidden Achievements (Always try to show some)
    unlocked = [a for a in data.get("achievements", []) if a["unlocked"]]
    if unlocked:
        st.markdown('<div style="margin-top: -1rem; margin-bottom: 1.5rem; display: flex; gap: 10px; flex-wrap: wrap;">', unsafe_allow_html=True)
        for a in unlocked:
            st.markdown(f'<span title="{a["desc"]}" style="background: rgba(249,168,38,0.1); border: 1px solid #F9A826; color: #F9A826; padding: 4px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 600;">{a["emoji"]} {a["name"]}</span>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)



    # Feature 8 & 5: Sentiment & Ecosystem
    col_s, col_e = st.columns([1, 1], gap="large")
    with col_s:
        st.markdown('<div class="section-header">🎭 Commit Sentiment & Vibe</div>', unsafe_allow_html=True)
        polarity = data["sentiment"].get("avg_polarity", 0)
        mood = data["sentiment"].get("mood", "Neutral 😐")
        color = "#22D3EE" if polarity > 0.1 else "#EC4899" if polarity < -0.05 else "#F9A826"
        
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = polarity,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': mood, 'font': {'size': 20, 'color': color}},
            gauge = {
                'axis': {'range': [-1, 1], 'tickwidth': 1, 'tickcolor': "white"},
                'bar': {'color': color},
                'bgcolor': "rgba(0,0,0,0)",
                'borderwidth': 2,
                'bordercolor': "rgba(255,255,255,0.1)",
                'steps': [
                    {'range': [-1, -0.1], 'color': 'rgba(236,72,153,0.1)'},
                    {'range': [-0.1, 0.1], 'color': 'rgba(249,168,38,0.1)'},
                    {'range': [0.1, 1], 'color': 'rgba(34,211,238,0.1)'}
                ],
            }
        ))
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font={'color': "white"}, height=250, margin=dict(t=40, b=10, l=30, r=30))
        st.plotly_chart(fig, use_container_width=True)
        
        # Feature 8: Review Personality
        rp = data.get("review_personality", {})
        if rp.get("advice"):
            with st.expander("🛠️ PR Review Strategy"):
                st.markdown(f"**Archetype:** {rp.get('archetype', 'The Observer')}")
                st.markdown(f"**Trait:** {rp.get('trait', 'Neutral')}")
                st.info(rp.get("advice", ""))

    with col_e:
        st.markdown('<div class="section-header">🕸 Project Ecosystem</div>', unsafe_allow_html=True)
        if data["ecosystem_html"]:
            import streamlit.components.v1 as components
            components.html(data["ecosystem_html"], height=300)
        else:
            st.markdown('<div class="glass-card" style="height:300px; display:flex; align-items:center; justify-content:center; color:#94A3B8;">Insufficient dependency data.</div>', unsafe_allow_html=True)

    st.divider()

    # Feature 13: Ghost Repos (if any)
    ghosts = data.get("ghosts", [])
    if ghosts:
        with st.expander(f"👻 Ghost Repo Audit ({len(ghosts)} inactive)"):
            st.markdown("These repositories haven't been touched in over a year. Consider archiving or revitalizing them!")
            for g in ghosts[:5]:
                st.markdown(f"- **{g['name']}** (Last updated: {g['last_updated']}) — {g['stars']} ⭐")

    # AI Job Matcher (Feature 7)
    st.markdown('<div class="section-header">💼 AI Job Role Matcher</div>', unsafe_allow_html=True)
    role_cols = st.columns(3)
    roles = data.get("job_roles", [])
    if not roles:
        roles = ["Full Stack Developer", "Software Engineer", "Open Source Contributor"] # Fallback
    
    for i, role in enumerate(roles[:3]):
        with role_cols[i]:
            st.markdown(f"""
            <div class="glass-card" style="text-align:center; padding:1.5rem; border-color:#22D3EE;">
                <div style="font-size:0.8rem; color:#22D3EE; font-weight:700;">#{i+1} RECOMMENDATION</div>
                <div style="font-size:1.1rem; font-weight:700; color:#FFFFFF; margin-top:0.5rem;">{role}</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.divider()

    # Career Arc Visualizer (Feature 3)
    st.markdown('<div class="section-header">📈 Career Evolution Timeline</div>', unsafe_allow_html=True)
    if data["arc_viz"]:
        st.plotly_chart(data["arc_viz"], use_container_width=True)
        with st.expander("🔍 Career Insights"):
            df = data["arc_df"]
            for _, row in df.iterrows():
                st.markdown(f"**{row['year']}**: Dominant in **{row['language']}** with a focus on **{row['topic']}**. Volume: {row['commit_count']} commits.")

    # Lang & Activity
    col_left, col_right = st.columns(2, gap="large")
    with col_left:
        st.markdown('<div class="section-header">🌐 Language Distribution</div>', unsafe_allow_html=True)
        if not lang_df.empty:
            tab1, tab2 = st.tabs(["🕸 Radar", "📊 Bar"])
            with tab1: st.plotly_chart(radar_chart(lang_df), use_container_width=True)
            with tab2: st.plotly_chart(bar_chart(lang_df), use_container_width=True)
    with col_right:
        st.markdown('<div class="section-header">⏰ Commit Activity Heatmap</div>', unsafe_allow_html=True)
        if not heatmap_pivot.empty:
            st.plotly_chart(activity_heatmap(heatmap_pivot), use_container_width=True)

    st.divider()

    # Code DNA Fingerprint (Feature 1)
    col_dna_l, col_dna_r = st.columns([1, 1.2])
    with col_dna_l:
        st.markdown('<div class="section-header">🧬 Code DNA Fingerprint</div>', unsafe_allow_html=True)
        st.write("Unique stylistic patterns extracted from your source files.")
        traits = data["dna_traits"]
        if traits:
            st.markdown(f"**Naming**: `{traits['naming']}`")
            st.markdown(f"**Braces**: `{traits['brace_style'].replace('_', ' ')}`")
            st.markdown(f"**Indent**: `{traits['indent']}`")
            st.info(f"💡 Most developers in your field use {traits['naming']}, but your comment density is {traits['comment_density']:.1f}%, which is higher than 70% of peers.")
    with col_dna_r:
        if data["dna_svg"]:
            st.components.v1.html(data["dna_svg"], height=520, scrolling=False)

    st.divider()

    # Dependency Ecosystem Map (Feature 10)
    st.markdown('<div class="section-header">🕸 Dependency Ecosystem Map</div>', unsafe_allow_html=True)
    if data["ecosystem_html"]:
        st.components.v1.html(data["ecosystem_html"], height=520, scrolling=False)
    else:
        st.info("No manifest files (requirements.txt, package.json, etc.) found to build the ecosystem map.")

    # WordCloud & NLP & Quality
    col_wc, col_nlp = st.columns([1.1, 1], gap="large")
    with col_wc:
        st.markdown('<div class="section-header">☁️ Commit WordCloud</div>', unsafe_allow_html=True)
        if wc_path: st.image(wc_path, use_container_width=True)
        
        # QUALITY SCORE
        st.markdown('<div class="section-header" style="margin-top:1.5rem;">📝 Commit Quality Report</div>', unsafe_allow_html=True)
        q = quality
        c_a, c_b = st.columns([1, 2])
        with c_a:
            st.markdown(f"""
            <div class="glass-card" style="text-align:center; padding:1.5rem 0;">
                <div style="font-size:0.8rem; color:#E2E8F0;">GRADE</div>
                <div style="font-size:4rem; font-weight:800; color:#6C63FF;">{q['grade']}</div>
                <div style="font-size:0.9rem; color:#FFFFFF;">Score: {q['avg_score']}</div>
            </div>
            """, unsafe_allow_html=True)
        with c_b:
            for tip in q["top_tips"]:
                st.markdown(f'<div style="font-size:0.85rem; color:#FFFFFF; margin-bottom:0.4rem;">💡 {tip}</div>', unsafe_allow_html=True)
            
            # AI REWRITER (Feature 8)
            if data["rewrites"]:
                with st.expander("✨ AI Suggested Rewrites"):
                    for rw in data["rewrites"]:
                        st.markdown(f"""
                        <div style="font-size:0.8rem; margin-bottom:0.5rem; padding:0.5rem; border-left:2px solid #6C63FF; background:rgba(108,99,255,0.05);">
                          <div style="color:#94A3B8;"><s>{rw['old']}</s></div>
                          <div style="color:#6C63FF; font-weight:600;">-> {rw['new']}</div>
                        </div>
                        """, unsafe_allow_html=True)

    with col_nlp:
        st.markdown('<div class="section-header">🧠 NLP Insights</div>', unsafe_allow_html=True)
        # Sentiment gauge
        polarity = sentiment["avg_polarity"]
        mood = sentiment["mood"]
        pct = int((polarity + 1) / 2 * 100)
        st.markdown(f"""
        <div class="glass-card">
          <div style="font-weight:600;color:#CBD5E1;margin-bottom:0.3rem;">😊 Commit Sentiment</div>
          <div class="sentiment-bar-wrap"><div class="sentiment-bar" style="width:{pct}%;background:linear-gradient(90deg,#6C63FF,#EC4899);"></div></div>
          <div style="font-size:1.1rem;font-weight:700;color:#FFFFFF;">{mood} <span style="font-size:0.8rem;font-weight:normal;color:#CBD5E1;">({polarity:+.2f})</span></div>
        </div>
        """, unsafe_allow_html=True)
        _render_topics(topics)
        
        # AI REVIEW PERSONALITY (Feature 6)
        st.markdown('<div class="section-header" style="margin-top:1.5rem;">🎭 Review Personality</div>', unsafe_allow_html=True)
        rp = data["review_personality"]
        st.markdown(f"""
        <div class="glass-card">
          <div style="font-size:0.8rem; color:#CBD5E1;">ARCHETYPE</div>
          <div style="font-size:1.4rem; font-weight:700; color:#F9A826;">{rp['archetype']}</div>
          <div style="font-size:0.9rem; color:#FFFFFF; margin-top:0.4rem;"><b>Trait:</b> {rp['trait']}</div>
          <div style="font-size:0.85rem; color:#E2E8F0; margin-top:0.8rem; border-top:1px solid rgba(255,255,255,0.1); padding-top:0.5rem;">
            <b>AI Advice:</b> {rp['advice']}
          </div>
        </div>
        """, unsafe_allow_html=True)

    # REPO HEALTH DASHBOARD
    st.divider()
    st.markdown(f'<div class="section-header">📦 Repo Health Dashboard <span style="font-size:0.8rem; font-weight:normal; color:#64748B;">({health_stats["emoji"]} {health_stats["label"]}: {health_stats["maintainer_score"]}/100)</span></div>', unsafe_allow_html=True)
    
    health_cols = st.columns(3, gap="medium")
    sorted_health = sorted(repo_scores, key=lambda r: r["stars"], reverse=True)[:6]
    for i, r in enumerate(sorted_health):
        with health_cols[i % 3]:
            # Construct health pill HTML
            pills = []
            for sig, val in r["signals"].items():
                if sig in ["has_readme", "has_license", "has_ci", "has_tests"]:
                    label = sig.replace("has_", "").upper()
                    cls = "health-pass" if val else "health-fail"
                    pills.append(f'<span class="health-pill {cls}">{label}</span>')
            
            pills_html = " ".join(pills)

            st.markdown(f"""
            <div class="glass-card" style="padding:1rem;">
                <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                    <div style="font-weight:600; color:#FFFFFF; font-size:0.9rem;">📁 {r['name']}</div>
                    <div style="font-size:1.1rem;">{r['emoji']}</div>
                </div>
                <div style="margin:0.5rem 0; display:flex; gap:0.3rem; flex-wrap:wrap;">
                    {pills_html}
                </div>
                <div style="display:flex; justify-content:space-between; align-items:center; margin-top:0.5rem;">
                    <div style="font-size:0.75rem; color:#CBD5E1;">⭐ {r['stars']} | {r['language']}</div>
                    <div style="font-size:0.8rem; font-weight:700; color:#FFFFFF;">Score: {r['score']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)


    # DEEP DATA METRICS SECTION
    st.divider()
    col_bus, col_ghost = st.columns(2, gap="large")
    
    with col_bus:
        st.markdown('<div class="section-header">🚌 Bus Factor Estimation</div>', unsafe_allow_html=True)
        bus = data["bus_stats"]
        st.markdown(f"""
        <div class="glass-card" style="padding:1.5rem;">
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <div>
              <div style="font-size:0.8rem; color:#CBD5E1;">CENTRALIZATION RISK</div>
              <div style="font-size:1.5rem; font-weight:700;">{bus['risk']}</div>
            </div>
            <div style="text-align:right;">
              <div style="font-size:2rem; font-weight:800; color:#6C63FF;">{bus['avg_factor']}</div>
              <div style="font-size:0.7rem; color:#E2E8F0;">AVG RATIO</div>
            </div>
          </div>
          <div style="margin-top:1rem; font-size:0.85rem; color:#E2E8F0;">
            A factor of 1 means you are the sole knowledge holder. Projects with high stars and low factors are 'knowledge silos'.
          </div>
        </div>
        """, unsafe_allow_html=True)

    with col_ghost:
        st.markdown('<div class="section-header">👻 Ghost Repo Audit</div>', unsafe_allow_html=True)
        if data["ghosts"]:
            for g in data["ghosts"][:3]:
                st.markdown(f"""
                <div style="display:flex; justify-content:space-between; padding:0.6rem; border-bottom:1px solid rgba(255,255,255,0.05);">
                  <div style="font-size:0.85rem; font-weight:600; color:#FFFFFF;">{g['name']}</div>
                  <div style="font-size:0.75rem; color:#94A3B8;">Last active: {g['last_updated']}</div>
                </div>
                """, unsafe_allow_html=True)
            st.warning("Found repositories with no activity for 1+ year. Consider archiving them.")
        else:
            st.success("All analyzed repositories have been active within the last year!")

    st.divider()

    # Time Capsule (Feature 13)
    st.markdown(f"""
    <div class="glass-card" style="border: 1px solid rgba(168,85,247,0.4); background: linear-gradient(135deg, rgba(168,85,247,0.1), rgba(108,99,255,0.05));">
      <div style="font-size:0.75rem; color:#A855F7; font-weight:700; text-transform:uppercase; letter-spacing:0.1em; margin-bottom:0.5rem;">🎞️ Time Capsule Message</div>
      <div style="font-size:1.2rem; font-weight:600; color:#FFFFFF; line-height:1.5; font-style:italic;">
        "{data['capsule']}"
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ------------------------------------------------------------------ #
    #  Footer
    # ------------------------------------------------------------------ #
st.markdown("""
<div style="text-align:center;padding:2rem 0 1rem;color:#475569;font-size:0.8rem;">
  Built with ❤️ using PyGithub · Streamlit · Plotly · scikit-learn · TextBlob · WordCloud
</div>
""", unsafe_allow_html=True)
