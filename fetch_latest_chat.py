import requests
import json
import os
import argparse
from datetime import datetime, timedelta, timezone
from chat_downloader import ChatDownloader

# ========== 設定 ==========
API_KEY = os.environ.get("API_KEY")
KEYWORDS = ["草"]
NG_WORDS = ["草原"]
OUTPUT_FILE = "all_chats_filtered.json"
DEFAULT_CHANNEL_ID = "UC6ixLgVB4D6ucEXb4VhZ-PA"
# ==========================

YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"

def fetch_upload_playlist_id(channel_id):
    url = f"{YOUTUBE_API_BASE}/channels?part=contentDetails&id={channel_id}&key={API_KEY}"
    res = requests.get(url).json()
    print("【DEBUG: API応答】", res)
    return res["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

def fetch_video_ids_and_titles(playlist_id, start_date=None, end_date=None):
    results = []
    next_page_token = None
    while True:
        url = f"{YOUTUBE_API_BASE}/playlistItems"
        params = {
            "part": "snippet",
            "playlistId": playlist_id,
            "maxResults": 50,
            "pageToken": next_page_token,
            "key": API_KEY
        }
        res = requests.get(url, params=params).json()
        for item in res.get("items", []):
            snippet = item["snippet"]
            published_at = snippet["publishedAt"]
            published_dt = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
            if start_date and end_date:
                if not (start_date <= published_dt <= end_date):
                    continue
            video_id = snippet["resourceId"]["videoId"]
            title = snippet["title"]
            results.append((video_id, title))
        next_page_token = res.get("nextPageToken")
        if not next_page_token or (start_date is None and len(results) > 0):
            break
    return results[:3] if start_date else results[:1]  # GitHubは最新1件のみ

def download_and_filter_chat(video_id, title):
    try:
        print("📥 チャットダウンロード開始", video_id)
        chat = ChatDownloader().get_chat(f"https://www.youtube.com/watch?v={video_id}")
        print("✅ チャット取得完了", video_id)
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
        print(f"✅ フィルタ完了 {video_id}: {len(filtered)} 件通過")
        return filtered
    except Exception as e:
        print(f"❌ {video_id} 失敗: {e}")
        return []

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--channel", default=os.environ.get("CHANNEL_ID", DEFAULT_CHANNEL_ID), help="チャンネルID（UC〜）")
    parser.add_argument("--start", help="開始日 (YYYY-MM-DD)", required=False)
    parser.add_argument("--end", help="終了日 (YYYY-MM-DD)", required=False)
    args = parser.parse_args()

    print("📺 チャンネルのアップロードプレイリストを取得中...")
    playlist_id = fetch_upload_playlist_id(args.channel)

    # 開始日・終了日があればローカルモード
    if args.start and args.end:
        start_date = datetime.fromisoformat(args.start).replace(tzinfo=timezone.utc)
        end_date = datetime.fromisoformat(args.end).replace(tzinfo=timezone.utc) + timedelta(days=1)
        print(f"🔎 動画一覧を取得中（期間: {args.start}〜{args.end}）...")
        videos = fetch_video_ids_and_titles(playlist_id, start_date, end_date)
    else:
        print("🆕 GitHubモード：最新動画1件を取得中...")
        videos = fetch_video_ids_and_titles(playlist_id)

    print(f"🎞 対象動画数: {len(videos)}")
    all_filtered = []
    for video_id, title in videos:
        filtered = download_and_filter_chat(video_id, title)
        all_filtered.extend(filtered)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_filtered, f, ensure_ascii=False, indent=2)

    print(f"\n🎉 完了：{len(all_filtered)}件のチャットを {OUTPUT_FILE} に保存しました。")

if __name__ == "__main__":
    main()