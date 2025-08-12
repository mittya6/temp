import pysolr
import csv

# Solr接続設定
SOLR_URL = "http://localhost:8983/solr/my_core"
FIELDS = ["id", "title_s", "text_t"]  # 出力したいフィールド
BATCH_SIZE = 1000
OUTPUT_FILE = "solr_export.csv"

solr = pysolr.Solr(SOLR_URL, timeout=60)

cursor = "*"
total_count = 0

with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as csvfile:
    writer = csv.writer(csvfile)
    # ヘッダー行
    writer.writerow(FIELDS)

    while True:
        results = solr.search("*:*", **{
            "cursorMark": cursor,
            "sort": "id asc",
            "rows": BATCH_SIZE,
            "fl": ",".join(FIELDS)
        })

        for doc in results:
            row = [doc.get(f, "") for f in FIELDS]
            writer.writerow(row)
            total_count += 1

        print(f"{total_count} 件を書き出し中...")

        if cursor == results.nextCursorMark:
            break
        cursor = results.nextCursorMark

print(f"書き出し完了: {total_count} 件 → {OUTPUT_FILE}")
