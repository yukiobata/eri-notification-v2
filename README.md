# 千葉恵里 情報通知Bot(Discord版)

「千葉恵里」に関する新着情報(Google Newsのキーワード検索＋任意で公式サイト/ブログのRSS)を
定期的に取得し、新しい記事があればDiscordに通知するBotです。

GitHub Actionsで3時間おきに自動実行されます(`workflow_dispatch`で手動実行も可能)。

---

## 1. Discord Webhook URLを作る(1分で終わります)

1. 通知を受け取りたいDiscordサーバー(自分専用のサーバーでもOK。無ければ「+」から新規作成)を開く
2. 通知させたいテキストチャンネルの右上の歯車アイコン(チャンネルの編集)をクリック
3. 左メニューの「連携サービス」→「ウェブフック」→「新しいウェブフック」を作成
4. 名前やアイコンは好きに設定し、「ウェブフックURLをコピー」をクリック
   - これが `DISCORD_WEBHOOK_URL` です(誰にも共有しないでください。知られると誰でもそのチャンネルに投稿できてしまいます)

LINEと違って公式アカウント作成やuserId取得のような手間は一切不要です。

## 2. GitHubリポジトリを作る

1. GitHubで新しいリポジトリを作成(Privateでも可)
2. このフォルダの中身(`check_news.py`, `requirements.txt`, `seen.json`, `.github/workflows/check.yml`)を
   そのリポジトリにpush

## 3. GitHub Secretsを設定

リポジトリの `Settings > Secrets and variables > Actions > New repository secret` から以下を登録:

| Secret名 | 値 |
|---|---|
| `DISCORD_WEBHOOK_URL` | 手順1でコピーしたWebhook URL |

## 4. 動作確認

- `Actions` タブ → `Chiba Eri News Check` → `Run workflow` で手動実行し、Discordに通知が届くか確認
- 初回実行時は既存の記事が全部「新着」扱いになるため、大量通知が来ます(`MAX_NOTIFY_PER_RUN`で件数制限してあります)
- 2回目以降は前回までにチェック済みの記事(`seen.json`)は再通知されません

## 5. カスタマイズ

- `check_news.py` の `SOURCES` リストに、公式ブログや特定サイトのRSSフィードURLを追加すると
  そのサイトの新着も監視対象にできます
  - `filter_keyword` にキーワードを指定すると、そのソースの記事のうちタイトル/本文抜粋にキーワードを含むものだけ通知します
    (AKB48公式ブログのようにメンバー全員の共同ブログの場合に有効)
- 実行頻度は `.github/workflows/check.yml` の `cron` を変更(現在は3時間おき)
- 通知メッセージの見た目を変えたい場合は `format_message()` を編集(Embed形式にすることも可能)
- **注意**: アメブロのRSSは仕様上、直近10件までしか取得できません。共同ブログ(akihabara48など)は
  更新頻度が高い日だと3時間の間に10件以上投稿されて取りこぼす可能性があるため、心配な場合は
  cronの間隔を短くする(例: 1時間おき)ことを検討してください
- X(Twitter)は公式APIが有料化されており、非公式スクレイピングはX社の利用規約違反となるため、
  本スクリプトには含めていません。公式アカウントがRSS配信やブログを持っていればそちらを利用してください
