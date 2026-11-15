# agent-wiki

**人と AI エージェントが一緒に育てる多言語ナレッジベース。**
Markdown + Git が正本。どの言語でも使える SQLite 全文検索、秘密情報スキャン、週次ヘルスチェック、
そして Claude・ChatGPT・Gemini・Codex から読み書きできる MCP サーバーを備えています。

[English](README.md) · [简体中文](README.zh-CN.md) · 日本語 · [Español](README.es.md)

## こんな人に

- AI エージェントがセッションをまたぐと、決定事項や過去の失敗を忘れてしまう；
- チームが複数の言語（例: 日本語と英語）で書いていて、まとめて検索したい；
- エージェントに知識を書かせたいが、レビューを挟み、API キーの流出は防ぎたい。

## エージェントで使う

`wiki init` が `AGENTS.md` と `CLAUDE.md` を生成し、Claude Code・Codex・Cursor などに「作業前に `wiki search`、
作業後にプロジェクトページと教訓を更新し、`[[id]]` でリンクし、`wiki check` を実行する」よう指示します。Wiki のフォルダでエージェントを開くだけで使えます。

## 特長

- **どの言語でも設定なしで検索。** 単語インデックス（大文字小文字・アクセント無視、前方一致）と、
  日本語・中国語・韓国語・タイ語のように空白で区切らない文字向けのトライグラムインデックスを併用します。
  2 文字の語は正規化した部分一致で検索します。
- **6 言語の UI。** メッセージ、レポート、テンプレートが English・中文・日本語・Español・Français・Deutsch に対応。
  各ページは `lang:` で自分の言語を宣言できます。
- **依存ゼロ。** コアは Python 標準ライブラリのみ。MCP はオプションです。
- **エージェント向けの安全策。** `wiki check` が API キーや秘密鍵の混入を防ぎ、MCP からの投稿は **受信箱** に入って
  レビューされるまで本体に反映されません。HTTP はクライアントごとのトークン（read / write、ハッシュのみ保存）。
- **週次ヘルスチェック。** `wiki lint` が孤立ページ、古いページ、重複の疑い、リンクのない教訓、「廃止」「deprecated」と書かれた行を一覧にします。

## はじめかた

```bash
pip install "git+https://github.com/SWYZLCO/agent-wiki"
wiki init my-wiki --lang ja
cd my-wiki
wiki add lesson "デプロイ前に DNS の所有アカウントを確認する" --slug check-dns --project website
wiki check
wiki search デプロイ
```

デモ: `wiki --root examples/demo-wiki search 予約確認`

## エージェントとの接続（MCP）

```bash
pip install "agent-wiki[mcp] @ git+https://github.com/SWYZLCO/agent-wiki"
claude mcp add wiki -- wiki --root /path/to/my-wiki mcp stdio
wiki mcp token add chatgpt read
AGENT_WIKI_HOSTS=wiki.example.com wiki mcp http --port 8790
```

コマンドと設定の詳細は [英語版 README](README.md) を参照してください。

## SWYZL & Co. について

agent-wiki は [SWYZL & Co.](https://swyzl.tech)（Swyzle Technologies Inc.、カナダ・トロント都市圏）の日々の仕事から生まれました。
私たちは AI ネイティブのデジタルスタジオとして、企業が使うデジタルシステムを設計・構築・統合し、その中で AI を働かせています。
Design it. Build it. Add AI. お問い合わせ: info@swyzl.tech

## ライセンス

MIT © SWYZL & Co.
