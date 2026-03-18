# shared-ui-foundation v3

## 概要

- Task12「共通 UI 基盤とレイアウトシェル整備」の Pencil フロー用 mock v3
- v2 のやわらかさは維持しつつ、肯定メッセージの整理、Startup Copy Layer の前提化、色と統一感の整理を行った版
- artifact-slug: `shared-ui-foundation`
- version: `v3`

## v2 からの変更点

- `Startup Copy Layer` を追加した
- auth / signed-in の肯定メッセージを同系統の `affirmation` 面に整理した
- auth 側の茶色メッセージ box を、導入カードではなく「入口の肯定感を弱く引き継ぐ面」として意味を明確化した
- signed-in shell の歓迎メッセージも常設バナー感を弱め、auth とつながる扱いへ寄せた
- flash / error は v2 の責めない方向性を維持しつつ、affirmation と役割が混ざらないよう見え方を分けた

## フレーム構成

1. `Startup Copy Layer`
2. `Auth Shell`
3. `Signed-in Shell`
4. `Flash Message Pattern`
5. `Form Error Pattern`

## 肯定メッセージの整理方針

- auth / home の肯定メッセージは、意味的に近いものとして `affirmation` 系の面へ寄せた
- 色は success よりニュートラルで、強い状態色にしない
- 役割は「操作結果」ではなく、「ここに来てよい」「まだ急がなくてよい」を受け止めること
- 常設パネルに見えすぎないよう、面はやわらかく、文量も短く抑える

## Startup Copy Layer の役割

- アプリ起動時に、登録済みテキスト群からランダムで1件だけ出る前提を示す
- 短時間で消え、その後に auth shell または signed-in shell が現れる前段レイヤーとして扱う
- ただし秒数やアニメーション仕様まではこの mock で固定しない

## auth / signed-in shell との関係

### Startup → Auth

- 起動時コピーのあと、入口側の affirmation が弱く引き継がれる
- ただしフォーム導線は止めすぎない

### Startup → Signed-in

- signed-in 側でも affirmation は残るが、主役はあくまで `primary action`
- 肯定メッセージは居場所の面、CTA は行動の面として役割を分ける

## flash / error との役割分担

- `affirmation`: 居場所、受容、急かさない前提
- `success flash`: 保存や送信の結果通知
- `info / guidance`: 補足や案内
- `form error`: 入力補助、修正ポイントの提示

見た目もこの順で差をつけ、affirmation と success を同じ箱に見せない。

## 下部ナビをどこまで確定したか

- v3 でも「受け皿」まで
- active 1 / placeholder 2 の見せ方に留める
- 項目数、最終ラベル、遷移設計は確定しきらない

## 実装時の注意点

- Startup Copy Layer は root/auth/home の前段レイヤーとして扱い、詳細アニメーションは実装時に最小限で整理する
- affirmation は success flash と CSS / partial を分けて扱う
- auth / signed-in で同系統の affirmation token を使い、色の意味をぶらさない
- 主 CTA と affirmation の優先順位を逆転させない
- Task12 の段階なので、個別画面の完成 UI へ寄りすぎない
- `login_id` / `display_name` 前提は維持する

## 承認時に見たいポイント

- auth / signed-in の肯定メッセージに統一感があるか
- success flash と affirmation が混ざって見えないか
- Startup Copy Layer が「前段で短く出る」前提として読めるか
- Startup → auth / home のつながりが自然か
- 情報量を増やしすぎず、静かさとやわらかさを維持できているか
