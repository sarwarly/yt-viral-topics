import streamlit as st
import requests
from datetime import datetime, timedelta, timezone
import math

# =========================
# CONFIG
# =========================
API_KEY = "AIzaSyBnmylzZY6Up8JLXMokflSP3jGsIX0mCH4"

YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_VIDEO_URL = "https://www.googleapis.com/youtube/v3/videos"
YOUTUBE_CHANNEL_URL = "https://www.googleapis.com/youtube/v3/channels"

MAX_RESULTS = 5               # per keyword
MAX_SUBSCRIBERS = 20000       # breakout range
MIN_VIRAL_RATIO = 10          # views / subs
MAX_VIDEO_AGE_DAYS = 7        # freshness window

# =========================
# STREAMLIT UI
# =========================
st.title("🐾 YouTube Viral Finder – Animal Rescue")

st.subheader("🔑 Keywords")
keywords_input = st.text_area(
    "Enter keywords (one per line):",
    placeholder="example:\nwildlife rescue\nanimal rescue\ndog rescue",
    height=200
)

KEYWORDS = [k.strip() for k in keywords_input.splitlines() if k.strip()]
KEYWORDS = list(dict.fromkeys(KEYWORDS))  # deduplicate

days = st.number_input(
    "Search videos published in last N days:",
    min_value=1,
    max_value=30,
    value=7
)

if st.button("Find Viral Videos"):

    if not KEYWORDS:
        st.warning("Please enter at least one keyword.")
        st.stop()

    start_date = (
        datetime.now(timezone.utc) - timedelta(days=int(days))
    ).isoformat().replace("+00:00", "Z")

    all_results = []

    for keyword in KEYWORDS:
        st.write(f"🔍 Searching: **{keyword}**")

        try:
            # -------- SEARCH --------
            search_params = {
                "part": "snippet",
                "q": keyword,
                "type": "video",
                "order": "viewCount",
                "publishedAfter": start_date,
                "maxResults": MAX_RESULTS,
                "key": API_KEY,
            }

            search_res = requests.get(
                YOUTUBE_SEARCH_URL, params=search_params, timeout=15
            ).json()

            videos = search_res.get("items", [])
            if not videos:
                continue

            video_ids = [v["id"]["videoId"] for v in videos]
            channel_ids = [v["snippet"]["channelId"] for v in videos]

            # -------- VIDEO STATS --------
            video_stats = requests.get(
                YOUTUBE_VIDEO_URL,
                params={
                    "part": "statistics",
                    "id": ",".join(video_ids),
                    "key": API_KEY
                },
                timeout=15
            ).json()

            # -------- CHANNEL STATS --------
            channel_stats = requests.get(
                YOUTUBE_CHANNEL_URL,
                params={
                    "part": "statistics",
                    "id": ",".join(channel_ids),
                    "key": API_KEY
                },
                timeout=15
            ).json()

            video_stat_map = {
                v["id"]: v["statistics"]
                for v in video_stats.get("items", [])
            }

            channel_stat_map = {
                c["id"]: c["statistics"]
                for c in channel_stats.get("items", [])
            }

            now = datetime.now(timezone.utc)

            # -------- ANALYSIS --------
            for v in videos:
                vid = v["id"]["videoId"]
                cid = v["snippet"]["channelId"]

                views = int(video_stat_map.get(vid, {}).get("viewCount", 0))
                subs = int(channel_stat_map.get(cid, {}).get("subscriberCount", 0))

                if subs <= 0 or views <= 0:
                    continue

                published_at = datetime.fromisoformat(
                    v["snippet"]["publishedAt"].replace("Z", "+00:00")
                )
                days_old = max((now - published_at).days, 1)

                # Core viral metrics
                views_to_subs = views / subs
                views_per_day = views / days_old
                viral_score = views_to_subs * math.log(views_per_day + 1)

                # -------- FILTERING --------
                if (
                    subs <= MAX_SUBSCRIBERS
                    and views_to_subs >= MIN_VIRAL_RATIO
                    and days_old <= MAX_VIDEO_AGE_DAYS
                ):
                    all_results.append({
                        "Keyword": keyword,
                        "Title": v["snippet"]["title"],
                        "URL": f"https://www.youtube.com/watch?v={vid}",
                        "Views": views,
                        "Subscribers": subs,
                        "Days Old": days_old,
                        "Views/Subs": round(views_to_subs, 2),
                        "Views/Day": int(views_per_day),
                        "Viral Score": round(viral_score, 2),
                    })

        except Exception as e:
            st.warning(f"Error with keyword '{keyword}': {e}")

    # =========================
    # OUTPUT
    # =========================
    if all_results:
        all_results.sort(key=lambda x: x["Viral Score"], reverse=True)

        st.success(f"🔥 Found {len(all_results)} viral opportunities")

        for r in all_results:
            st.markdown(
                f"""
**🎬 {r['Title']}**  
**🔑 Keyword:** {r['Keyword']}  
**👁 Views:** {r['Views']:,}  
**👥 Subscribers:** {r['Subscribers']:,}  
**⏱ Days Old:** {r['Days Old']}  
**⚡ Views/Subs:** {r['Views/Subs']}  
**🚀 Views/Day:** {r['Views/Day']:,}  
**🔥 Viral Score:** {r['Viral Score']}  
**🔗 URL:** [Watch Video]({r['URL']})  
---
"""
            )
    else:
        st.warning("No strong viral signals found. Try different keywords or fewer days.")
