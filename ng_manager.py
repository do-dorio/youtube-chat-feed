import json
import base64
import os
import sys

FILTER_FILE = "filters.json"

def load_filters():
    if not os.path.exists(FILTER_FILE):
        return {"ng_words": {"hidden": [], "monitor": []}}
    with open(FILTER_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_filters(data):
    with open(FILTER_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def add_ng_word(mode):
    print(f"追加したい {mode} NGワードを入力してください（表示されません）:")
    try:
        import getpass
        word = getpass.getpass("")
    except Exception:
        word = input(">> ")

    filters = load_filters()
    ng_words = filters.setdefault("ng_words", {})
    if mode == "hidden":
        encoded = base64.b64encode(word.encode("utf-8")).decode("utf-8")
        if encoded in ng_words.get("hidden", []):
            print("⚠️ すでに登録されています。")
            return
        ng_words.setdefault("hidden", []).append(encoded)
    elif mode == "monitor":
        if word in ng_words.get("monitor", []):
            print("⚠️ すでに登録されています。")
            return
        ng_words.setdefault("monitor", []).append(word)
    else:
        print("❌ 不正なモードです。")
        return

    save_filters(filters)
    print("✅ NGワードを追加しました。")

def remove_ng_word(mode):
    print(f"削除したい {mode} NGワードを入力してください（表示されません）:")
    try:
        import getpass
        word = getpass.getpass("")
    except Exception:
        word = input(">> ")

    filters = load_filters()
    ng_words = filters.setdefault("ng_words", {})
    if mode == "hidden":
        encoded = base64.b64encode(word.encode("utf-8")).decode("utf-8")
        if encoded not in ng_words.get("hidden", []):
            print("⚠️ 登録されていません。")
            return
        ng_words["hidden"].remove(encoded)
    elif mode == "monitor":
        if word not in ng_words.get("monitor", []):
            print("⚠️ 登録されていません。")
            return
        ng_words["monitor"].remove(word)
    else:
        print("❌ 不正なモードです。")
        return

    save_filters(filters)
    print("✅ NGワードを削除しました。")

def list_ng_words():
    filters = load_filters()
    hidden = filters.get("ng_words", {}).get("hidden", [])
    monitor = filters.get("ng_words", {}).get("monitor", [])

    print("🚫 非表示NGワード（base64伏せ済）:")
    for i, _ in enumerate(hidden, 1):
        print(f"  {i}. *****")

    print("👁️ 確認対象NGワード:")
    for i, word in enumerate(monitor, 1):
        print(f"  {i}. {word}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python ng_manager.py [add|remove] [hidden|monitor]  または list")
        sys.exit(1)

    command = sys.argv[1].lower()
    if command == "list":
        list_ng_words()
    else:
        mode = sys.argv[2].lower()
        if command == "add":
            add_ng_word(mode)
        elif command == "remove":
            remove_ng_word(mode)
        else:
            print("Usage: python ng_manager.py [add|remove] [hidden|monitor] または list")