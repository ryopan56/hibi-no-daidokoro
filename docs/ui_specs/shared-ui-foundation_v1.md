# shared-ui-foundation v1

## 概要

- Task12「共通 UI 基盤とレイアウトシェル整備」のための Pencil フロー用 mock v1
- この段階ではコード実装を行わず、`home` / `login` / `signup` で横断利用する共通 UI の視覚案と実装意図を固める
- artifact-slug: `shared-ui-foundation`
- version: `v1`

## 主目的

- `base template` の受け皿を視覚化する
- auth 系とログイン後画面で、どこまで共通化し、どこから分けるかの基準を先に作る
- フラッシュメッセージ、フォームエラー、共通ヘッダー、下部ナビの配置ルールを先に固定する
- 後続タスクで screen-specific な装飾を増やしすぎないための共通ルールを持つ

## 対象範囲

- auth 系シェル
- ログイン後シェル
- フラッシュメッセージ表示位置
- フォームエラー表示位置
- ベース余白、コンテナ、タイポグラフィの方向性

対象外:

- 個別画面固有の完成 UI
- 実データに依存する細かな一覧設計
- AI 導線の作り込み
- `src/` のコード実装

## セクション構成

Pencil ファイル内は以下の 4 フレーム構成。

1. `Auth Shell`
2. `App Shell`
3. `Flash Message Pattern`
4. `Form Error Pattern`

## auth 系シェルとログイン後シェルの使い分け案

### auth 系シェル

- 1画面1目的を強く出す
- 中央寄せではなく、上から静かに読ませる縦積み
- 主 CTA は 1 つだけ
- `login_id` と `password` を基本構造とし、`signup` では `display_name` を追加しても同じカード構造を使う
- non-field error はフォームカード上部にまとめる

### ログイン後シェル

- 上部に共通ヘッダーの受け皿を置く
- 主 CTA を最上位カードに置く
- 下部ナビは「主要画面の切り替え口」として固定の受け皿を持つ
- 二次導線は主 CTA の下へ、静かな強度で積む

## フラッシュメッセージの表示方針

- ページ全体メッセージはヘッダー直下、主 CTA より上
- フォーム送信由来のものはフォームカードの上
- success / info / error は同じ箱構造を使い、色と文言で意味を分ける
- 文言は短く、責めないトーンを維持する

## フォームエラー表示方針

- non-field error はフォーム先頭にまとめる
- field error は対象フィールド直下に表示する
- help text と error text は同じ位置を使い、レイアウトジャンプを小さくする
- サーバーサイドバリデーションを正とし、クライアント側は補助扱い

## 共通ヘッダー / 下部ナビの受け皿方針

### 共通ヘッダー

- 役割はページ名、短い補助説明、必要最小限の右上アクション受け皿まで
- 画面ごとの独自 UI をヘッダーに寄せすぎない

### 下部ナビ

- ログイン後画面のみ
- 主要導線の切り替え口として 3〜4 項目を想定
- active / inactive の見分けは明確にする
- 画面固有アクションを置く場所ではなく、トップレベル導線に限定する

## 実装時に src 側で触る想定ファイル候補

- `src/meallogs/templates/base.html`
- `src/accounts/templates/accounts/login.html`
- `src/accounts/templates/accounts/signup.html`
- `src/accounts/templates/accounts/home.html`
- `src/meallogs/templates/meallogs/*.html`
- `src/static/` 配下の共通 CSS ファイル
- 必要なら共通 partial 用の template

## 作り込みすぎないための注意点

- Task12 は共通土台であり、個別画面の完成度をここで上げない
- `home` の固有情報量や一覧 UI をここで確定しない
- `login` / `signup` の文言差分は後続タスクで調整し、今は構造優先
- 下部ナビの項目名や数も最終確定ではなく、受け皿の確認を優先する
- AI 導線はこの mock の主役にしない

## 仕様メモ

- `login` 識別子は `email` ではなく `login_id`
- 表示名は `display_name`
- モバイルファースト
- 1画面の主目的は 1 つ
- 入力を急かさない
- エラーや案内文は責めないトーン
- AI は明示的なボタン操作時のみ
- 既存 URL / View / Form 契約は実装段階でも壊さない

## 人間承認時に見たいポイント

- auth 系とログイン後で分け方が自然か
- メッセージとエラーの出る位置が一貫しているか
- 共通ヘッダーが重くなりすぎていないか
- 下部ナビが主 CTA と競合していないか
- この段階で screen-specific に寄りすぎていないか
