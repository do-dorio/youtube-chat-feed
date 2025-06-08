import json
import base64
import shutil
import os
from datetime import datetime, timedelta
from xml.sax.saxutils import escape

INPUT_JSON = "latest_chat_filtered.json"
OUTPUT_RSS = "chat_feed.xml"
OUTPUT_DIR = "docs"

def load_filters(path="filters.json"):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    labels = data.get("labels", {})
    return labels

# ========== ラベル設定 ==========


LONG_MSG_THRESHOLD = 20  # 長文とみなす文字数    
KEYWORD_LABELS = load_filters()

# ========== チャット読み込み ==========
with open(INPUT_JSON, "r", encoding="utf-8") as f:
    chats = json.load(f)

if not chats:
    print("⚠️ フィルター結果が0件のため、RSSは生成されませんでした。")
    exit()

rss_items = []
for chat in chats:
    msg = chat.get("message", "")
    timestamp = int(chat.get("time_in_seconds", 0))

    # 日時取得（動画の公開時刻 + チャット相対時間）
    published_at = chat.get("videoPublishedAt")
    if published_at:
        base_dt = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
        dt = base_dt + timedelta(seconds=timestamp)
    else:
        dt = datetime.utcfromtimestamp(timestamp)

    dt_str = dt.strftime("%a, %d %b %Y %H:%M:%S +0000")  # RSS用フォーマット

    # ----- タイトルの前置きフラグ -----
    flags = []
    if len(msg) >= LONG_MSG_THRESHOLD:
        flags.append("長文")
    for keyword, label in KEYWORD_LABELS.items():
        if keyword in msg and label not in flags:
            flags.append(label)

    prefix = " ".join(flags) + ": " if flags else ""
    title = f"{prefix}{chat.get('videoTitle', '動画')} @ {timestamp // 60}分{timestamp % 60}秒"

    link = f"https://www.youtube.com/watch?v={chat['videoId']}&t={max(timestamp - 30, 0)}s"
    thumbnail_url = f"https://i.ytimg.com/vi/{chat['videoId']}/hqdefault.jpg"
    content = escape(msg)
    description = f"""
    <img src=\"{thumbnail_url}\" width=\"320\"><br>
    {content}
    """

    rss_items.append(
    f'<item>'
    f'<title>{escape(title)}</title>'
    f'<link>{escape(link)}</link>'
    f'<description><![CDATA[{description}]]></description>'
    f'<pubDate>{dt_str}</pubDate>'
    f'</item>'
    )

rss_feed = (
    '<?xml version="1.0" encoding="UTF-8" ?>'
    '<rss version="2.0">'
    '<channel>'
    '<title>YouTube Chat Feed</title>'
    '<link>https://www.youtube.com</link>'
    '<description>Latest filtered chat from YouTube</description>'
    + ''.join(rss_items) +
    '</channel>'
    '</rss>'
)

with open(OUTPUT_RSS, "w", encoding="utf-8") as f:
    f.write(rss_feed)

print(f"✅ RSSフィードを {OUTPUT_RSS} に書き出しました")

# GitHub Pages 用に docs にコピー
os.makedirs(OUTPUT_DIR, exist_ok=True)
dest_path = os.path.join(OUTPUT_DIR, OUTPUT_RSS)
shutil.copyfile(OUTPUT_RSS, dest_path)
print(f"✅ GitHub Pages 用に {dest_path} にコピーしました")
