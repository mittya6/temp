# pip install langchain-core langchain-community pysolr
# -*- coding: utf-8 -*-
from typing import List, Optional
import pysolr
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_core.prompts import ChatPromptTemplate

# ---- 設定 ----
SOLR_URL = "http://localhost:8983/solr"
SOLR_CORE = "my_core"          # 例: 'documents'
TEXT_FIELD = "text_t"          # 本文フィールド名（スキーマに合わせて変更）
RETURN_FIELDS = [TEXT_FIELD, "id", "title_s"]  # 返したいフィールド

# ---- Solr BM25 リトリーバ ----
class SolrBM25Retriever(BaseRetriever):
    def __init__(self, solr_client: pysolr.Solr, k: int = 4, fq: Optional[str] = None):
        self.solr = solr_client
        self.k = k
        self.fq = fq

    def _get_relevant_documents(self, query: str) -> List[Document]:
        params = {
            "q": f"{TEXT_FIELD}:({pysolr.Solr.escape_query(query)})",
            "rows": self.k,
            "fl": ",".join(RETURN_FIELDS),
        }
        if self.fq:
            params["fq"] = self.fq
        res = self.solr.search(**params)
        docs = []
        for hit in res:
            content = hit.get(TEXT_FIELD, "")
            metadata = {k: hit.get(k) for k in RETURN_FIELDS if k != TEXT_FIELD}
            docs.append(Document(page_content=content, metadata=metadata))
        return docs

# ---- 使い方（質問→文脈取得→LLMへ渡す最終プロンプトを組み立て）----
def format_docs(docs: List[Document]) -> str:
    # LLMに渡しやすいように整形
    chunks = []
    for i, d in enumerate(docs, 1):
        title = d.metadata.get("title_s") or d.metadata.get("id") or f"doc{i}"
        chunks.append(f"### {title}\n{d.page_content}")
    return "\n\n".join(chunks)

def build_llm_messages(question: str, context: str):
    prompt = ChatPromptTemplate.from_messages([
        ("system", "あなたは正確で簡潔なアシスタントです。事実は与えられたナレッジに限定して回答してください。"),
        ("human",
         "次の質問に日本語で答えてください。\n"
         "質問: {question}\n\n"
         "参考ナレッジ:\n{context}\n\n"
         "制約:\n- ナレッジにない推測はしない\n- 出典が必要なら該当箇所のタイトルかIDを示す")
    ])
    return prompt.format_messages(question=question, context=context)

if __name__ == "__main__":
    # Solrクライアント
    solr = pysolr.Solr(f"{SOLR_URL}/{SOLR_CORE}", always_commit=False, timeout=10)

    # 質問
    question = "社内規程の有給休暇の繰越条件を教えて"

    # 検索→コンテキスト整形
    retriever = SolrBM25Retriever(solr, k=4)
    docs = retriever.invoke(question)  # RetrieverはRunnableなのでinvoke可
    context = format_docs(docs)

    # LLMに渡す直前のメッセージ（ここでLLMは呼ばない）
    messages = build_llm_messages(question, context)

    # 例: 最終的にLLMへ渡すメッセージを確認（systemとhuman）
    for m in messages:
        print(f"[{m.type.upper()}]\n{m.content}\n")
