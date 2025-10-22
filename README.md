できます。やり方はいくつかありますが、いちばん実装しやすいのは「一定間隔でメールを集計 → 件数が閾値（10通）以上なら Teams に投稿」という定期フローです。まずは“同じようなメール＝件名や送信元が同一”という前提の実装例を出し、その後に“ゆるい類似（件名の一部一致など）”の方法も載せます。

# パターンA：件名や送信元が同じメールを数える（標準コネクタのみ）

**構成（例：直近24時間で10通以上）**

1. **トリガー**：`スケジュール - 繰り返し`（例：毎時）
2. **アクション**：`Office 365 Outlook - メールの取得 (V3)`

   * フォルダー: 受信トレイ
   * **検索クエリ**（AQS）例

     * 送信元固定：`from:"alerts@vendor.com" received>=@{formatDateTime(addHours(utcNow(), -24), 'yyyy/MM/dd HH:mm')}`
     * 件名固定：`subject:"Your Alert Title" received>=@{formatDateTime(addHours(utcNow(), -24), 'yyyy/MM/dd HH:mm')}`
   * 取得件数（Top）: 200 など十分大きめ（上限に注意）
3. **条件**：`length(body('メールの取得_(V3)')?['value']) >= 10`

   * **はい**側：`Microsoft Teams - チャネルまたはチャットにメッセージを投稿`
     例文：「過去24時間で同種メールが@{length(...)}件到達」

> 式サンプル（条件の左辺）：
> `@length(body('メールの取得_(V3)')?['value'])`

**ポイント**

* Outlook の「検索クエリ」は AQS（Advanced Query Syntax）です。`from:`, `subject:`, `received>=` などの組み合わせが使えます。
* 期間は `addHours(utcNow(), -24)` を `-48` や `addDays(utcNow(), -7)` に変えればOK。
* 件名が完全一致しない小さな差分があると拾えないので、その場合は次のパターンBへ。

---

# パターンB：「同じような」件名を束ねてカウント（部分一致・グループ化）

**構成（例：件名に特定のキーワードを含むメールを24時間で集計し、件名ごとに10通以上なら通報）**

1. **トリガー**：`スケジュール - 繰り返し`（毎時）
2. **アクション**：`メールの取得 (V3)`

   * 検索クエリ（例）：`"Error 500" received>=@{formatDateTime(addHours(utcNow(), -24), 'yyyy/MM/dd HH:mm')}`
3. **Select（データ操作）**：件名配列を作成

   * マッピング：`From: item()?['subject']  To: item()?['subject']`
4. **Compose（重複排除）**：`union(body('Select'), body('Select'))` → **distinctSubjects**
5. **Apply to each（distinctSubjects）**：各件名について…

   * **Filter array**：`body('メールの取得_(V3)')?['value']` を対象に
     条件：`contains(item()?['subject'], items('Apply_to_each'))`
     （※「件名にその件名文字列を含む」＝ゆるい束ね方。先頭一致なら `startsWith()` を使う）
   * **条件**：`length(body('Filter_array')) >= 10`

     * **はい**側：Teams に「件名：○○ が直近24hで 10件以上」などを投稿

**ポイント**

* 「似ている」定義を `contains()` / `startsWith()` / 正規化（例：余分な番号・日付を `replace()` で除去）で調整できます。
* 件名ではなく「送信元ドメイン」で束ねたい場合は、`item()?['from']?['emailAddress']` を `endsWith(..., '@vendor.com')` でグループ化してもOK。

---

# パターンC：さらに厳密な類似判定（オプション）

* **AI Builder** の「テキスト類似度」や「分類」を使って、本文・件名の意味的な近さで束ねる（※有償/プレミアム要素）。
* **Microsoft Graph `List messages` + $search** を使って KQL 検索を細かく組む（必要に応じて）。

---

## よくあるハマりどころ

* **取得件数の上限**：`メールの取得 (V3)` は Top 上限あり。24時間に大量流入する場合は、複数回取得（オフセット）やより狭い時間間隔での繰り返しにする。
* **タイムゾーン**：`formatDateTime()` は既定 UTC。必要なら `convertTimeZone()` を使って JST 表記に。
* **重複投稿抑止**：Teams への投稿前に「前回通知からX分以内はスキップ」などのフラグ（環境変数／Dataverse／SharePoint リスト／OneDrive の小ファイル）で抑止可能。
* **「既読/未読」だけで判断しない**：AQS の `isread:false` だけだと運用でブレやすい。期間 + 件名/送信元のほうが安定。

---

## まず動く最小例（コピペ向け式）

* **期間（24h前）**：`@{formatDateTime(addHours(utcNow(), -24), 'yyyy/MM/dd HH:mm')}`
* **条件（10件以上）**：`@greaterOrEquals(length(body('メールの取得_(V3)')?['value']), 10)`

---

必要なら、あなたの「似ている」の定義（例：送信元固定？件名の先頭一致？本文の特定フレーズ含む？期間は何時間/日？）に合わせて、実際のフロー画面のスクショ手順レベルまで落とし込みます。
