# Task12 Mock v5 Signup Button Tune

- タスク名: Task12「共通 UI 基盤とレイアウトシェル整備」v5 signup 導線修正
- モード: Pencil フロー / mock

## 実装概要

- auth 画面の signup 導線を、テキストリンクから補助ボタンへ変更
- 文言を `初めての方はこちら` に更新
- 主 CTA `ログインする` の下に置き、主 CTA より一段軽い見え方に調整

## 変更ファイル

- `docs/pencil/shared-ui-foundation_v5.pen`
- `docs/ui_mockups/shared-ui-foundation_v5_draft.png`
- `docs/ui_specs/shared-ui-foundation_v5.md`
- `logs/codex_sessions/20260318_1254_task12_mock_v5_signup_button.md`

## 実行したコマンド / 操作

- Pencil MCP で `shared-ui-foundation_v5.pen` を更新
- auth shell のスクリーンショット確認
- Pencil export で `shared-ui-foundation_v5_draft.png` を更新

## 結果

- signup 導線が、主 CTA を崩さずに見つけやすくなった
- 実装コードやテストには未着手

## 注意点 / 残課題

- `.pen` ファイル本体は Pencil editor 側の状態依存があり、リポジトリ上のテキスト内容は最小のプレースホルダになる場合がある
- v5 全体 artifact は未追跡のまま

## 完了報告

- auth 画面の signup 導線を補助ボタン化して更新した
