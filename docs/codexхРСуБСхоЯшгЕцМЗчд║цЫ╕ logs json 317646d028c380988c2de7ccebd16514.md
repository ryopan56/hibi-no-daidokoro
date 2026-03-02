# codex向け実装指示書/logs.json

## Task 0: 事前準備

Project: 日々の台所

1. [AGENT.md](http://agent.md/) と [SPEC.md](http://spec.md/) を必ず読み、遵守すること。
2. Docker Compose 前提で Django 5.2 + PostgreSQL の雛形を作成する。
3. ローカルにDjangoを直接インストールしない構成にする。
4. src/ 配下にDjangoプロジェクトを作る。
5. .env.example を作成し、.env はGit追跡しない。
6. .gitignore を作成する（AGENT.mdのGitポリシーに従う）。
7. logging設定を追加し、logs/app/ に出力する。
8. featureブランチ feat/task-00-bootstrap で作業する。
9. タスク完了後、コミットし、logs/codex_sessions にセッションログを保存する。

注意点：

ディレクトリ構成は以下を固定する。勝手に階層変更しない。

- docs/: 設計md
- src/: Djangoプロジェクト
- logs/codex_sessions/: Codex会話ログ（Git管理）
- logs/app/, logs/ai/, logs/export_import/: 実行ログ（Git管理しない）
- media/: 画像アップロード（Git管理しない）
- ルートに docker-compose.yml, [AGENT.md](http://agent.md/), [SPEC.md](http://spec.md/), .env.example を置く

最終目標：

- docker compose up で起動
- [http://localhost:8000/](http://localhost:8000/) でプレースホルダ表示
- migration が成功する

---

## Task 1: 認証（login_id）一式

**目的**: `login_id` で signup/login/logout ができ、セッションが張れる。

**実装範囲**:

- CustomUser（`USERNAME_FIELD = login_id`）
- signup/login/logout のビュー・フォーム・テンプレ
- CSRF、バリデーション、ログイン必須デコレータ/ミドルウェア
    
    **受入条件**:
    
- URL表どおり：`/signup` GET/POST、`/login` POST、`/logout` POST
- 不正ログイン時に責めないエラー文言（画面仕様のトーン）

---

## Task 2: ホーム（歓迎メッセージ＋日付導線）

**目的**: `/home` で歓迎メッセージ＋導線を出す。

**実装範囲**:

- `/home`：歓迎メッセージ表示（仕様に沿う。DB保存しない）
- 「今日の記録へ」 `/logs/today` リダイレクト
    
    **受入条件**:
    
- ログイン直後 or 当日初回ホームアクセス時のみ歓迎文言が出る…

---

## Task 3: MealLog（表示/保存）＋enum変換ユーティリティ

**目的**: 指定日ログの表示・保存ができる。

**実装範囲**:

- `/logs/<log_date>` GET/POST（存在しなければ作成or初期化して表示）
- enum（DB数値）↔ 表示定数（LOW等）↔ 表示ラベル（低等）の変換を一元化
    
    **受入条件**:
    
- UNIQUE(user, log_date) を守る（同日2重作成しない）
- フォーム値のバリデーション（time_minutes は 10/30/60 など）

---

## Task 4: 写真アップロード/削除（最大10枚）

**目的**: 写真が追加・削除でき、ログに紐づく。

**実装範囲**:

- `/logs/<log_date>/photos` POST、`/photos/<photo_id>/delete` POST
- `MEDIA_ROOT/MEDIA_URL`、Pillow、UUIDファイル名運用
    
    **受入条件**:
    
- 1ログ最大10枚（超過は画面に優しくエラー表示）
- 削除は所有者チェック必須

---

## Task 5: タグ（候補表示）＋中間テーブル

**目的**: 1ログに複数タグ付与でき、過去タグ候補が出る。

**実装範囲**:

- tags(kind, name) と meal_log_tags
- ログ画面でタグ追加/削除（UIは簡素でOK）
    
    **受入条件**:
    
- AND検索の条件としてタグを扱える下地がある

---

## Task 6: 食材カテゴリ（中間テーブル）

**目的**: 食材カテゴリが複数付与できる。

**実装範囲**:

- meal_log_ingredients(category) のCRUD（ログ画面内でチェックボックス等）
    
    **受入条件**:
    
- enum対応表に沿う（MEAT/FISH…）

---

## Task 7: 検索（AND検索・日付範囲）

**目的**: 条件で過去ログを探せる。

**実装範囲**:

- `/search` GET/POST
- AND検索 + 日付範囲
    
    **受入条件**:
    
- 検索結果一覧 → 日付クリックで記録画面へ

---

## Task 8: カレンダー（月表示）

**目的**: 月単位でログ有無だけが見える。

**実装範囲**:

- `/calendar` GET
- ログある日だけ軽い印（空白日を強調しない）
    
    **受入条件**:
    
- 日付クリックで記録画面へ

---

## Task 9: AI（minimum/recommend）＋回数制限＋フォールバック

**目的**: AI提案が構造化で動き、制限超過や障害でも壊れない。

**実装範囲**:

- `/ai/minimum` `/ai/recommend` POST
- 入力/出力スキーマ通りに実装（Structured Outputs前提）
- 1日3回制限（JST日付判定）
- ai_usage_logs 記録
    
    **受入条件**:
    
- エラー/タイムアウト/制限時は定型文フォールバック

---

## Task 10: 通知（アプリ内）＋週次肯定（weekly praise）

**目的**: 「通知」「週次肯定」をホーム表示トリガーで出す。

**実装範囲**:

- 通知設定 `/settings/notifications` GET/POST
- 週次肯定：日曜0時（JST）基準、次回ホーム表示時に1回だけ 要件定義 2d2646d028c380879a9df230d7…
- weekly_praise のAI入出力は仕様通り
    
    **受入条件**:
    
- 2週間空いていても1回のみ表示

---

## Task 11: エクスポート/インポート（ZIP）

**目的**: 端末にバックアップでき、上書き復元できる。

**実装範囲**:

- `/export` GET/POST、`/import` GET/POST
- ZIPの中身：`logs.json` と `photos/`
- 復元は同一ユーザーへ上書き（既存データ削除→投入）
    
    **受入条件**:
    
- マージ機能なし
- 写真も復元できる

---

# 2) logs.json スキーマ案（v1）

設計要件上「同一ユーザーへ上書き復元」「マージなし」なので、**DBの整数IDを持ち出さず**、エクスポートは「意味のあるデータ」を主にします。

また、AI入力で定数名（LOW等）を使う設計なので、logs.jsonでも **enumは“定数名”で保存**するのが自然です。

## logs.json（トップレベル）

```
{
  "schema_version":1,
  "exported_at_utc":"2026-03-02T04:00:00Z",
  "app": {
    "name":"hibi-no-daidokoro",
    "timezone_policy":"db:UTC, business:JST"
  },
  "user": {
    "login_id":"string",
    "display_name":"string"
  },
  "notification_settings": {
    "enabled":true,
    "weekday":"WED",
    "last_sent_at_utc":"2026-02-26T01:23:45Z"
  },
  "tags": [
    {
      "tag_uid":"uuid",
      "kind":"SPECIAL|SEASON|EVENT",
      "name":"string",
      "created_at_utc":"2026-02-01T00:00:00Z"
    }
  ],
  "meal_logs": [
    {
      "log_uid":"uuid",
      "log_date":"YYYY-MM-DD",

      "energy_level":"LOW|MEDIUM|HIGH|null",
      "time_minutes":10,
      "child_care":true,
      "minimum_mode":false,

      "result":"COOKED|NOT_COOKED|BOUGHT|EAT_OUT|FROZEN|LEFTOVER|null",
      "cook_granularity":"FULL|SIMPLE|WARMED|CUT_ONLY|PLATED|null",

      "comment":"string|null",

      "weather":"SUNNY|RAINY|SNOWY|WINDY|null",
      "temp_feel":"COLD|JUST|HOT|null",
      "season":"SPRING|SUMMER|AUTUMN|WINTER|null",
      "mood":"LIGHT|RICH|WARM|EASY|null",
      "cooking_method":"GRILL|SIMMER|STEAM|STIR_FRY|null",

      "ingredient_categories": ["MEAT","FISH","EGG","VEGETABLE","BEAN","FROZEN"],

      "tag_uids": ["uuid","uuid"],

      "photos": [
        {
          "photo_uid":"uuid",
          "path":"photos/2026/02/01/<uuid>.jpg",
          "original_name":"IMG_1234.JPG",
          "content_type":"image/jpeg",
          "sha256":"optional",
          "created_at_utc":"2026-02-01T00:00:00Z"
        }
      ],

      "created_at_utc":"2026-02-01T00:00:00Z",
      "updated_at_utc":"2026-02-01T00:10:00Z"
    }
  ]
}
```