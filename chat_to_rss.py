import json
import shutil
import os
from datetime import datetime
from xml.sax.saxutils import escape

INPUT_JSON = "latest_chat_filtered.json"
OUTPUT_RSS = "chat_feed.xml"
OUTPUT_DIR = "docs"

with open(INPUT_JSON, "r", encoding="utf-8") as f:
    chats = json.load(f)

if not chats:
    print("⚠️ フィルター結果が0件のため、RSSは生成されませんでした。")
    exit()

rss_items = []
for chat in chats:
    timestamp = int(chat.get("time_in_seconds", 0))
    dt = datetime.utcfromtimestamp(timestamp)
    dt_str = dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    link = f"https://www.youtube.com/watch?v={chat['videoId']}&t={max(timestamp - 30, 0)}s"
    content = escape(chat.get("message", ""))
    title = f"{chat.get('videoTitle', '動画')} @ {timestamp // 60}分{timestamp % 60}秒"

    rss_items.append(f"""
    <item>
      <title>{escape(title)}</title>
      <link>{escape(link)}</link>
      <description>{content}</description>
      <pubDate>{dt_str}</pubDate>
    </item>
    """)

rss_feed = f"""
<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
  <channel>
    <title>YouTube Chat Feed</title>
    <link>https://www.youtube.com</link>
    <description>Latest filtered chat from YouTube</description>
    {''.join(rss_items)}
  </channel>
</rss>
"""

with open(OUTPUT_RSS, "w", encoding="utf-8") as f:
    f.write(rss_feed)

print(f"✅ RSSフィードを {OUTPUT_RSS} に書き出しました")

# GitHub Pages 用に docs にコピー
os.makedirs(OUTPUT_DIR, exist_ok=True)
dest_path = os.path.join(OUTPUT_DIR, OUTPUT_RSS)
shutil.copyfile(OUTPUT_RSS, dest_path)
print(f"✅ GitHub Pages 用に {dest_path} にコピーしました")
