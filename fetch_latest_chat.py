import requests
import json
import os
from datetime import datetime, timezone
from chat_downloader import ChatDownloader

# ========== 設定 ==========
API_KEY = os.environ.get("API_KEY");
CHANNEL_ID = "UC-hM6YJuNYVAmUWxeIr9FeA"  # チャンネルID
KEYWORDS = ["草"]
NG_WORDS = ["草原"]
OUTPUT_FILE = "latest_chat_filtered.json"
# ==========================

YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"

def fetch_upload_playlist_id(channel_id):
    url = f"{YOUTUBE_API_BASE}/channels?part=contentDetails&id={channel_id}&key={API_KEY}"
    res = requests.get(url).json()
    return res["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

def fetch_latest_video_id_and_title(playlist_id):
    url = f"{YOUTUBE_API_BASE}/playlistItems"
    params = {
        "part": "snippet",
        "playlistId": playlist_id,
        "maxResults": 1,
        "key": API_KEY
    }
    res = requests.get(url, params=params).json()
    snippet = res["items"][0]["snippet"]
    video_id = snippet["resourceId"]["videoId"]
    title = snippet["title"]
    return video_id, title

def download_and_filter_chat(video_id, title):
    try:
        chat = ChatDownloader().get_chat(f"https://www.youtube.com/watch?v={video_id}")
        filtered = []
        for message in chat:
            msg = message.get("message", "")
            if not msg:
                continue
            if any(kw in msg for kw in KEYWORDS):
                if any(ng in msg for ng in NG_WORDS):
                    continue
                message["videoId"] = video_id
                message["videoTitle"] = title
                filtered.append(message)
        print(f"✅ {video_id}: {len(filtered)} 件フィルター通過")
        return filtered
    except Exception as e:
        print(f"❌ {video_id} 失敗: {e}")
        return []

def main():
    print("📺 最新動画のチャットを取得中...")
    playlist_id = fetch_upload_playlist_id(CHANNEL_ID)
    video_id, title = fetch_latest_video_id_and_title(playlist_id)

    filtered = download_and_filter_chat(video_id, title)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(filtered, f, ensure_ascii=False, indent=2)

    print(f"\n🎉 完了：{len(filtered)}件のチャットを {OUTPUT_FILE} に保存しました。")

if __name__ == "__main__":
    main()