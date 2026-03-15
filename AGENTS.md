# AGENT.md

## 0. この文書の役割
この文書は、hibi-no-daidokoro リポジトリにおける Codex / ChatGPT の行動規範を定める。
この文書はプロダクト仕様書ではない。
プロダクト仕様・文書優先順位・横断仕様は SPEC.md を参照すること。
MCP や外部接続の実際の許可範囲は `.codex/config.toml` に従うこと。

## 1. 最優先ルール
- 仕様変更を勝手に行わない
- 仕様不足・仕様衝突を見つけた場合は、実装で吸収せず「提案」として整理する
- プロダクトに関する判断は SPEC.md を優先する
- ツール権限・外部接続は `.codex/config.toml` を優先する
- secrets は読まない、出さない、貼らない

## 2. 技術前提
- Django 5.x / PostgreSQL / Docker Compose / Django Templates
- `logs/app/` などの実行ログ系と、`logs/codex_sessions/` を運用する
- `logs/codex_sessions/` は Git 管理対象
- ローカル開発は Docker Compose 前提とする
- 既存のディレクトリ構成は勝手に変えない

## 3. 作業開始時
作業開始時は、原則として以下を確認する。
- SPEC.md
- 現在の進捗サマリー
- 必要な仕様ページ
- Deep research レビュー
- `git status -sb`
- `git log --oneline --decorate -10`

必要な仕様ページとは、要件定義 / 非機能要件 / 画面仕様 / URLメソッド / テーブル定義 / enum対応表 / AIプロンプト仕様 / メッセージ仕様 などを指す。

開始時の方針:
- まず前提を要約する
- 仕様衝突や前提不足があれば、実装前に列挙する
- 大きな UI 変更、本番インフラ構成、移行手順のような横断的作業は、いきなり実装せず先に計画を作る

## 4. 作業の基本姿勢
- 既存構成を尊重し、最小差分で変更する
- ディレクトリ構成や命名規則を勝手に変えない
- 不明点を推測で埋めない
- 破壊的変更は避ける
- 横断的な方針変更は提案として整理し、承認前に実装しない

## 5. Git 運用
- `main` は常に安定状態を保つ
- タスクごとに作業ブランチを切る
  - 例: `feat/task-12-frontend-planning`
  - 例: `fix/task-xx-...`
- push はユーザーがローカルで実施する
- Codex は `git push` を行わない
- PR 作成 / 更新のみ、ユーザーが明示的に依頼した場合に限り GitHub MCP 経由で行ってよい
- 破壊的な Git 操作は禁止
  - `git reset --hard`
  - `git clean -fd`
  - 履歴改変
  - 大量削除

## 6. 外部接続
- Codex 本体の一般ネットワークは原則 OFF
- 外部接続は `.codex/config.toml` の許可範囲に従う
- GitHub 操作は GitHub MCP に限定する
- Notion 連携は Notion MCP を用いてよいが、用途は原則として参照に限る
- Notion への更新・書き込みは、ユーザーが明示的に依頼した場合のみ検討する
- ただし、Notion 側 integration capability が read-only の場合は書き込みを試みない
- 許可されていない外部接続は行わない

## 7. Notion の扱い
- Notion は「作業ハブ / 要約ハブ / 補助参照元」として扱う
- 仕様の最終決定は SPEC.md に従う
- GitHub の最新状態を毎回そのまま Notion に転記しない
- Notion には要約を残す
- secrets や `.env` 実値は Notion に貼らない

## 8. secrets / 環境変数
- APIキー / PAT / DB接続情報 / `.env` の実値 / 各種 secret は表示しない
- 不要に `.env` を開かない
- `KEY` / `SECRET` / `TOKEN` を含む情報は原則として扱わない
- 例外として、PR 作成 / 更新を行う日だけ `GITHUB_PERSONAL_ACCESS_TOKEN` を一時的に使う運用は可とする
- secret 値を表示するコマンドは提案しない
- secret を含む内容を Notion / ChatGPT / ログへ転記しない

## 9. テスト
- 変更後は適切なテストを行う
- 基本は `docker compose exec web python manage.py test` を用いる
- 必要に応じて対象を絞ったテストや手動確認を行う
- テスト未実施の場合は、未実施理由を明記する

## 10. 作業終了時
- 実装内容を確認する
- 必要なテストを実施する
- `git diff` で変更内容を確認する
- 必要に応じて `git diff --cached` でコミット対象差分を確認する
- 適切な粒度で `git add` / `git commit` を行う
- コミットメッセージは Conventional Commits を基本とする
- `logs/codex_sessions/` にセッションログを残す
- 完了報告には少なくとも以下を含める
  1. 変更ファイル
  2. 実装概要（仕様と実装の対応）
  3. 実行したテスト / コマンド
  4. 注意点 / 残課題
  5. ログファイル名

## 11. 禁止事項
- 仕様を勝手に変更すること
- secrets を読む / 出す / 貼ること
- Notion に secrets や生ログを貼ること
- GitHub へ勝手に push すること
- 破壊的な Git 操作をすること
- 未承認の外部接続を増やすこと
