import requests
import base64
import json
import os
import argparse
from datetime import datetime, timedelta, timezone
from chat_downloader import ChatDownloader

def load_filters(path="filters.json"):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 検索対象キーワード
    keywords = data.get("keywords", [])

    # NGワード群（hidden: base64, monitor: 平文）
    ng_section = data.get("ng_words", {})
    hidden = [base64.b64decode(b).decode("utf-8") for b in ng_section.get("hidden", [])]
    monitor = ng_section.get("monitor", [])

    # 統合NGワード（検索対象とは絶対に混ざらないように分離）
    ng_words = hidden + monitor

    return keywords, ng_words

# ========== 設定 ==========
API_KEY = os.environ.get("API_KEY")
KEYWORDS, NG_WORDS = load_filters()
CHANNELS_FILE = "channels.json"
OUTPUT_FILE = "latest_chat_filtered.json"
PROCESSED_FILE = "processed_videos.json"
YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"
# ==========================

def load_channels():
    with open(CHANNELS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def load_processed_ids():
    if os.path.exists(PROCESSED_FILE):
        with open(PROCESSED_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()

def save_processed_ids(processed_ids):
    with open(PROCESSED_FILE, "w", encoding="utf-8") as f:
        json.dump(list(processed_ids), f, ensure_ascii=False, indent=2)

def fetch_upload_playlist_id(channel_id):
    url = f"{YOUTUBE_API_BASE}/channels?part=contentDetails&id={channel_id}&key={API_KEY}"
    res = requests.get(url).json()
    return res["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

def fetch_recent_video_ids(playlist_id):
    now = datetime.now(timezone.utc)
    yesterday = now - timedelta(days=1)
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
            if published_dt >= yesterday:
                video_id = snippet["resourceId"]["videoId"]
                title = snippet["title"]
                results.append((video_id, title, published_at))
        next_page_token = res.get("nextPageToken")
        if not next_page_token:
            break
    return results

def is_live_streamed(video_id):
    url = f"{YOUTUBE_API_BASE}/videos?part=liveStreamingDetails&id={video_id}&key={API_KEY}"
    res = requests.get(url).json()
    item = res.get("items", [None])[0]
    if not item:
        return False
    details = item.get("liveStreamingDetails", {})
    return bool(details.get("actualEndTime"))

def download_and_filter_chat(video_id, title, published_at):
    try:
        print("📥 チャットダウンロード開始", video_id)
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
                message["videoPublishedAt"] = published_at
                filtered.append(message)
        print(f"✅ フィルタ完了 {video_id}: {len(filtered)} 件通過")
        return filtered
    except Exception as e:
        print(f"❌ {video_id} 失敗: {e}")
        return []

def main():
    all_filtered = []
    channels = load_channels()
    processed_ids = load_processed_ids()
    new_processed_ids = set()

    for channel_id in channels:
        print(f"\n🎯 チャンネル: {channel_id}")
        try:
            playlist_id = fetch_upload_playlist_id(channel_id)
            videos = fetch_recent_video_ids(playlist_id)

            for video_id, title, published_at in videos:
                if video_id in processed_ids:
                    print(f"⏭️ 既に処理済み: {video_id}")
                    continue
                if is_live_streamed(video_id):
                    print(f"▶ ライブ配信済み動画検出: {video_id}")
                    filtered = download_and_filter_chat(video_id, title, published_at)
                    all_filtered.extend(filtered)
                    new_processed_ids.add(video_id)
        except Exception as e:
            print(f"⚠️ チャンネル処理失敗: {channel_id} - {e}")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_filtered, f, ensure_ascii=False, indent=2)

    # 最新24時間の動画IDのみ記録として上書き
    save_processed_ids(new_processed_ids)

    print(f"\n🎉 完了：{len(all_filtered)}件のチャットを {OUTPUT_FILE} に保存しました。")

if __name__ == "__main__":
    main()