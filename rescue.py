import streamlit as st
import requests
from datetime import datetime, timedelta

# =========================
# CONFIG
# =========================
API_KEY = "AIzaSyBnmylzZY6Up8JLXMokflSP3jGsIX0mCH4"

YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_VIDEO_URL = "https://www.googleapis.com/youtube/v3/videos"
YOUTUBE_CHANNEL_URL = "https://www.googleapis.com/youtube/v3/channels"

MAX_RESULTS = 5
MAX_SUBSCRIBERS = 3000

# =========================
# STREAMLIT UI
# =========================
st.title("🐾 YouTube Viral Topics – Animal Rescue")

st.subheader("🔑 Keywords")
keywords_input = st.text_area(
    "Enter keywords (one per line):",
    placeholder="example:\nwildlife rescue\nanimal rescue\ndog rescue",
    height=200
)

# Build keyword list (required)
KEYWORDS = [k.strip() for k in keywords_input.splitlines() if k.strip()]
KEYWORDS = list(dict.fromkeys(KEYWORDS))  # remove duplicates

days = st.number_input(
    "Enter Days to Search (1–30):",
    min_value=1,
    max_value=30,
    value=7
)

if st.button("Fetch Data"):

    if not KEYWORDS:
        st.warning("Please enter at least one keyword to start.")
        st.stop()

    start_date = (datetime.utcnow() - timedelta(days=int(days))).isoformat("T") + "Z"
    all_results = []

    for keyword in KEYWORDS:
        st.write(f"🔍 Searching: **{keyword}**")

        try:
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

            video_stats = requests.get(
                YOUTUBE_VIDEO_URL,
                params={"part": "statistics", "id": ",".join(video_ids), "key": API_KEY},
                timeout=15
            ).json()

            channel_stats = requests.get(
                YOUTUBE_CHANNEL_URL,
                params={"part": "statistics", "id": ",".join(channel_ids), "key": API_KEY},
                timeout=15
            ).json()

            video_stat_map = {
                v["id"]: v["statistics"] for v in video_stats.get("items", [])
            }
            channel_stat_map = {
                c["id"]: c["statistics"] for c in channel_stats.get("items", [])
            }

            for v in videos:
                vid = v["id"]["videoId"]
                cid = v["snippet"]["channelId"]

                views = int(video_stat_map.get(vid, {}).get("viewCount", 0))
                subs = int(channel_stat_map.get(cid, {}).get("subscriberCount", 0))

                if subs <= MAX_SUBSCRIBERS and views > 0:
                    all_results.append({
                        "Keyword": keyword,
                        "Title": v["snippet"]["title"],
                        "Description": v["snippet"]["description"][:200],
                        "URL": f"https://www.youtube.com/watch?v={vid}",
                        "Views": views,
                        "Subscribers": subs
                    })

        except Exception as e:
            st.warning(f"Error with keyword '{keyword}': {e}")

    # =========================
    # OUTPUT
    # =========================
    if all_results:
        all_results.sort(key=lambda x: x["Views"], reverse=True)
        st.success(f"Found {len(all_results)} results!")

        for r in all_results:
            st.markdown(
                f"""
**🎬 Title:** {r['Title']}  
**🔑 Keyword:** {r['Keyword']}  
**👁 Views:** {r['Views']:,}  
**👥 Subscribers:** {r['Subscribers']:,}  
**🔗 URL:** [Watch Video]({r['URL']})  

_{r['Description']}_  
---
"""
            )
    else:
        st.warning("No suitable low-subscriber videos found.")
