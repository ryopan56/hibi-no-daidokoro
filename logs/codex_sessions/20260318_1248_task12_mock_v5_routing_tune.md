# Task12 Mock v5 Routing Tune

- タスク名: Task12「共通 UI 基盤とレイアウトシェル整備」v5 mock 修正
- モード: Pencil フロー / mock

## 実装概要

- v5 の背景、光だまり、Startup Copy Layer の方向性は維持
- auth に `signup` の補助導線を CTA 下で見やすく追加
- signed-in に日付単位ログ一覧の受け皿を追加
- home 上部は常設歓迎 box ではなく、一時メッセージ領域として整理
- ボトムナビを `Home / Calendar / Search` に寄せ、設定系導線は右上ハブ側想定へ整理

## 変更ファイル

- `docs/pencil/shared-ui-foundation_v5.pen`
- `docs/ui_mockups/shared-ui-foundation_v5_draft.png`
- `docs/ui_specs/shared-ui-foundation_v5.md`
- `logs/codex_sessions/20260318_1248_task12_mock_v5_routing_tune.md`

## 実行したコマンド / 操作

- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' SPEC.md`
- `sed -n '1,260p' docs/ui_specs/shared-ui-foundation_v5.md`
- `git status -sb`
- Pencil MCP で `shared-ui-foundation_v5.pen` を更新
- Pencil screenshot で全体確認
- Pencil export で `shared-ui-foundation_v5_draft.png` を更新

## 結果

- v5 を新規 version 化せず、同じ artifact のまま導線整理を反映
- signup 導線、home 一覧受け皿、ボトムナビの役割分担が mock 上で読み取りやすくなった
- 実装コードやテストには未着手

## 注意点 / 残課題

- `.pen` ファイル本体は Pencil editor 側の状態依存があり、リポジトリ上のテキスト内容は最小のプレースホルダになる場合がある
- v2 / v3 / v4 / v5 artifact は未追跡のまま残っている
- 一覧受け皿はあくまで領域提示であり、個別一覧画面の詳細設計は未確定

## 完了報告

- Task12 の v5 mock を、導線配置の観点で更新した
