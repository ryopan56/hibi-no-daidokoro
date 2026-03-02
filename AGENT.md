# Project: 日々の台所 (hibi-no-daidokoro)

---

## 0. 目的

本プロジェクトは「記録を責めない」思想を持つ食事ログアプリである。
実装は常に [SPEC.md](http://spec.md/) を正とする。
不明点は推測実装せず、提案としてコメントすること。

---

## 1. 技術スタック

- Django 5.2 (LTS)
- PostgreSQL
- Docker Compose 前提（ローカルにDjangoを直接インストールしない）
- Django Templates + Bootstrap
- OpenAI API（Structured Outputs）

---

## 2. 認証方針

- login_id を USERNAME_FIELD とする
- メールアドレスは保持しない
- Django標準のパスワードハッシュを使用
- セッション認証

---

## 3. 実装原則

### 3.1 推測禁止

仕様が曖昧な場合は勝手に実装しない。
SPEC.md に追記案を提示して承認後に実装する。

### 3.2 enumの扱い

- DBは SmallInteger
- アプリ側で Enum 管理
- logs.json では定数名で保存

### 3.3 Djangoモデル優先

- テーブル定義.mdがMySQL表記でも、最終的にはDjangoモデルを正とする
- DBはPostgreSQL

---

## 4. ログ取得ポリシー（必須）

### 4.1 ログディレクトリ構成

logs/
├── app/               # 実行ログ（Git管理しない）
├── ai/                # AIログ（Git管理しない）
├── export_import/     # Export/Import処理ログ（Git管理しない）
└── codex_sessions/    # Codex会話ログ（Git管理する）

### 4.2 必ずログを取るタイミング

1. 各HTTPリクエスト開始/終了
2. DB保存前後
3. AI呼び出し前後
4. エラー発生時（stacktrace含む）
5. export/import実行時
6. 週次肯定判定時
7. Codexとの各セッション

### 4.3 Codexセッションログ（必須）

保存場所：
logs/codex_sessions/YYYYMMDD_HHMM_taskXX.md

必須内容：

- 指示内容
- Codexの応答
- 実施変更
- 発生問題
- 解決方法

※ APIキー等はマスクすること

---

## 5. Git / GitHub 運用（必須）

### 5.1 ブランチ戦略

- main: 常に動作可能状態
- feat/task-XX-<name>: タスク単位ブランチ

### 5.2 コミット方針

- タスク完了単位でコミット
- 意味のある単位で分割可
- 変更理由が分かるメッセージ

### 5.3 Gitに含める

- AGENT.md
- SPEC.md
- docs/
- src/
- docker関連
- .env.example
- logs/codex_sessions/

### 5.4 Gitに含めない

- .env
- logs/app/
- logs/ai/
- logs/export_import/
- media/
- **pycache**/
- DBデータ

### 5.5 作業手順

1. featureブランチ作成
2. 実装
3. 起動確認
4. git diff確認
5. コミット
6. codex_sessionsログ保存
7. mainへマージ

---

## 6. エクスポート/インポート

- schema_version=1
- 同一ユーザーへ上書き復元
- マージ禁止
- ZIP構成：logs.json + photos/

---

END
