#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
千葉恵里さんに関する新着情報を取得し、まだ通知していないものだけ
Discord Webhook 経由で自分のサーバー/チャンネルに通知するスクリプト。

- 情報源は SOURCES に列挙した RSS フィード（Google Newsのキーワード検索 + 個別サイトのRSS）
- 通知済みの記事は seen.json に記録し、次回以降は重複通知しない
- GitHub Actions から定期実行され、seen.json の更新は自動コミットされる想定
"""

import os
import json
import hashlib
import sys
import feedparser
import requests

# ============================================================
# 設定
# ============================================================

KEYWORD = "千葉恵里"

# 情報源のRSSフィード一覧。
# 1) Google Newsのキーワード検索RSS(ニュース記事全般をカバー)
# 2) 個別サイトの公式RSS(あれば追加。無い場合は削除してOK)
SOURCES = [
    {
        "name": "AKB48 Official Blog",
        "url": "https://rssblog.ameba.jp/akihabara48/rss20.xml",
        # このブログはAKB48メンバー全員の共同ブログなので、
        # タイトル or 本文抜粋に「千葉恵里」を含む記事だけを通知対象にする
        "filter_keyword": KEYWORD,
    },
    # 他に見てほしい公式ブログ・サイトのRSSがあればここに追加してください
    # {
    #     "name": "サイト名",
    #     "url": "https://example.com/feed",
    #     "filter_keyword": None,  # そのサイト全体が対象ならNone、キーワード絞込が必要ならKEYWORDなど
    # },
]

STATE_FILE = os.path.join(os.path.dirname(__file__), "seen.json")

# Discord Webhook URL (環境変数 / GitHub Secrets から取得)
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

MAX_NOTIFY_PER_RUN = 20  # 1回の実行で通知する最大件数(通知しすぎ防止の安全弁)


# ============================================================
# 処理本体
# ============================================================

def load_seen():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()


def save_seen(seen):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(seen), f, ensure_ascii=False, indent=2)


def entry_id(entry, source_name):
    """記事を一意に識別するIDを作る(linkが無い場合はtitleでハッシュ化)"""
    base = entry.get("link") or entry.get("title", "")
    raw = f"{source_name}:{base}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def fetch_new_entries(seen):
    new_items = []
    for src in SOURCES:
        try:
            feed = feedparser.parse(src["url"])
        except Exception as e:
            print(f"[WARN] {src['name']} の取得に失敗: {e}", file=sys.stderr)
            continue

        for entry in feed.entries:
            keyword = src.get("filter_keyword")
            if keyword:
                haystack = (entry.get("title", "") + " " + entry.get("summary", ""))
                if keyword not in haystack:
                    continue  # このソースの対象キーワードを含まない記事はスキップ

            eid = entry_id(entry, src["name"])
            if eid in seen:
                continue
            new_items.append(
                {
                    "id": eid,
                    "source": src["name"],
                    "title": entry.get("title", "(タイトルなし)"),
                    "link": entry.get("link", ""),
                    "published": entry.get("published", ""),
                }
            )
    return new_items


def send_discord_message(text):
    if not DISCORD_WEBHOOK_URL:
        print("[ERROR] DISCORD_WEBHOOK_URL が未設定です", file=sys.stderr)
        return False

    body = {"content": text[:2000]}  # Discordの1メッセージ文字数上限(2000字)対策
    resp = requests.post(DISCORD_WEBHOOK_URL, json=body, timeout=10)
    if resp.status_code not in (200, 204):
        print(f"[ERROR] Discord送信失敗: {resp.status_code} {resp.text}", file=sys.stderr)
        return False
    return True


def format_message(item):
    lines = [
        f"**【{item['source']}】新着情報**",
        item["title"],
    ]
    if item["published"]:
        lines.append(f"_{item['published']}_")
    if item["link"]:
        lines.append(item["link"])
    return "\n".join(lines)


def main():
    seen = load_seen()
    new_items = fetch_new_entries(seen)

    if not new_items:
        print("新着情報はありませんでした。")
        return

    # 通知しすぎ防止のため上限をかける
    to_notify = new_items[:MAX_NOTIFY_PER_RUN]

    sent_count = 0
    for item in to_notify:
        message = format_message(item)
        ok = send_discord_message(message)
        if ok:
            seen.add(item["id"])
            sent_count += 1
        else:
            # 送信失敗した場合はseenに入れず、次回リトライさせる
            pass

    save_seen(seen)
    print(f"{sent_count}件の新着情報を通知しました。(検出総数: {len(new_items)}件)")


if __name__ == "__main__":
    main()
