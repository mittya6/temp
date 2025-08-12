import pysolr

solr = pysolr.Solr("http://localhost:8983/solr/my_core", timeout=10)

cursor = '*'
batch_size = 1000

while True:
    results = solr.search('*:*', **{
        'cursorMark': cursor,
        'sort': 'id asc',
        'rows': batch_size,
        'fl': 'id,title_s,text_t'
    })
    for r in results:
        print(r)  # ここでCSVに書き出しなど

    if cursor == results.nextCursorMark:
        break
    cursor = results.nextCursorMark
