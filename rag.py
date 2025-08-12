# pip install pandas rank-bm25 langchain-core
# pip install fugashi==1.* ipadic==1.*

# -*- coding: utf-8 -*-
import os
import re
from typing import List, Optional, Tuple
import pandas as pd
from rank_bm25 import BM25Okapi
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate

CSV_PATH = "solr_export.csv"   # 与えられたCSV名

TITLE_CANDIDATES = ["title", "title_s", "subject", "name"]
ID_CANDIDATES = ["id", "ID", "Id"]

# --------- 日本語向けトークナイズ（軽量版） ---------
# fugashi が入っていれば使い、無ければ「文字バイグラム」にフォールバックします
def _char_bigrams(s: str) -> List[str]:
    s = re.sub(r"\s+", "", s)  # 空白除去
    return [s[i:i+2] for i in range(len(s)-1)] if len(s) > 1 else ([s] if s else [])

try:
    from fugashi import Tagger  # type: ignore
    _tagger = Tagger()  # 初期化コスト小
    def ja_tokenize(text: str) -> List[str]:
        if not text:
            return []
        return [w.surface for w in _tagger(text)]
except Exception:
    def ja_tokenize(text: str) -> List[str]:
        if not text:
            return []
        # 英数は単語、その他はバイグラムでそこそこ戦える
        tokens = []
        # 単純に英数は単語分割
        for part in re.findall(r"[A-Za-z0-9_]+|[^A-Za-z0-9_\s]+", text):
            if re.match(r"[A-Za-z0-9_]+", part):
                tokens.append(part.lower())
            else:
                tokens.extend(_char_bigrams(part))
        return tokens

# --------- CSV 読み込みと列検出 ---------
def detect_columns(df: pd.DataFrame) -> Tuple[Optional[str], Optional[str], List[str]]:
    cols = list(df.columns)

    # id / title 列推定
    id_col = next((c for c in ID_CANDIDATES if c in cols), None)
    title_col = next((c for c in TITLE_CANDIDATES if c in cols), None)

    # テキスト候補列（object / string 系）
    text_cols = []
    for c in cols:
        if c in {id_col, title_col}:
            continue
        if pd.api.types.is_object_dtype(df[c]) or pd.api.types.is_string_dtype(df[c]):
            text_cols.append(c)
    if not text_cols:
        # 全部対象（数値も文字化）
        text_cols = [c for c in cols if c not in {id_col, title_col}]
    return id_col, title_col, text_cols

def row_to_text(row: pd.Series, text_cols: List[str]) -> str:
    parts = []
    for c in text_cols:
        v = row.get(c, None)
        if pd.isna(v) or v is None:
            continue
        s = str(v).strip()
        if not s:
            continue
        parts.append(f"\n{s}")
    return "\n\n".join(parts)

# --------- RAG: BM25 リトリーバ ---------
class CSVBM25Retriever:
    def __init__(self, docs: List[Document]):
        self.docs = docs
        # コーパスをトークナイズ
        self.tokens_corpus = [ja_tokenize(d.page_content) for d in docs]
        self.bm25 = BM25Okapi(self.tokens_corpus)

    def search(self, query: str, k: int = 4) -> List[Document]:
        q_tokens = ja_tokenize(query)
        scores = self.bm25.get_scores(q_tokens)
        # 上位k件
        top_idx = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
        results = []
        for i in top_idx:
            d = self.docs[i]
            md = dict(d.metadata)
            md["bm25_score"] = float(scores[i])
            results.append(Document(page_content=d.page_content, metadata=md))
        return results

# --------- LLMへ渡す前の整形 ---------
def format_docs(docs: List[Document]) -> str:
    out = []
    for i, d in enumerate(docs, 1):
        title = d.metadata.get("title") or d.metadata.get("title_s") \
                or d.metadata.get("id") or f"doc{i}"
        out.append(f"### {title}\n{d.page_content}")
    return "\n\n---\n\n".join(out)

def build_llm_messages(question: str, context: str):
    prompt = ChatPromptTemplate.from_messages([
        ("system", "あなたは正確で簡潔なアシスタントです。回答は与えられたコンテキストに限定してください。"),
        ("human",
         "次の質問に日本語で答えてください。\n"
         "質問: {question}\n\n"
         "参考ナレッジ:\n{context}\n\n"
         "制約:\n- ナレッジにない推測はしない\n- 必要なら出典としてタイトルやIDを示す")
    ])
    return prompt.format_messages(question=question, context=context)

# --------- メイン ---------
if __name__ == "__main__":
    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(f"{CSV_PATH} が見つかりません。")

    df = pd.read_csv(CSV_PATH)
    id_col, title_col, text_cols = detect_columns(df)

    # CSV → Document化
    docs = []
    for idx, row in df.iterrows():
        page = row_to_text(row, text_cols)
        if not page:
            continue
        md = {}
        # id
        if id_col and pd.notna(row.get(id_col, None)):
            md["id"] = str(row[id_col])
        else:
            md["id"] = f"row-{idx}"
        # title
        if title_col and pd.notna(row.get(title_col, None)):
            md["title"] = str(row[title_col])
        docs.append(Document(page_content=page, metadata=md))

    if not docs:
        raise ValueError("有効なテキスト行がありません。CSV内容をご確認ください。")

    # BM25 構築 & 検索
    retriever = CSVBM25Retriever(docs)
    question = "有給休暇の繰越条件を教えて"
    top_docs = retriever.search(question, k=4)

    # コンテキスト組み立て → LLMメッセージ（呼ばない）
    context = format_docs(top_docs)
    messages = build_llm_messages(question, context)

    # 確認出力
    for m in messages:
        print(f"[{m.type.upper()}]\n{m.content}\n")
