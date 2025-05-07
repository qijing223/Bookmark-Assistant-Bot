from typing import List, Any
from langchain_core.retrievers import BaseRetriever
from langchain.schema import Document
from langchain.prompts import PromptTemplate
from pydantic import Field


class MilvusMultiQueryRetriever(BaseRetriever):
    """支持多 query 改写的 Retriever，兼容 from_chain_type。"""
    storage: Any = Field()
    llm: Any = Field()
    top_k: int = Field(default=5)
    n_queries: int = Field(default=3)
    query_rewrite: bool = Field(default=True)
    similarity_threshold: float = Field(default=0.5)

    def _generate_queries(self, query: str) -> List[str]:
        rewrite_prompt = PromptTemplate.from_template(
            "Please generate {n} different rephrasings of the following user question, optimized for information retrieval: \n\nUser Question: {query}\n\nRewritten Queries:"
        )
        query_rewriter = rewrite_prompt | self.llm
        output = query_rewriter.invoke({"query": query, "n": self.n_queries}).content
        queries = [q.strip("-• \n") for q in output.strip().split("\n") if q.strip()]
        print(f"Generated queries: {queries}")
        return queries[:self.n_queries]
    
    def _get_relevant_documents_for_one_query(self, query: str) -> List[Document]:
        results = self.storage.search(query, top_k=self.top_k, similarity_threshold=self.similarity_threshold)
        docs = []
        for match in results[0]:
            metadata = {"title": match["entity"]["title"]}
            content = match["entity"]["content"]
            docs.append(Document(page_content=content, metadata=metadata))
        return docs

    def _get_relevant_documents(self, query: str) -> List[Document]:
        sub_queries = self._generate_queries(query)

        all_docs = []
        for q in sub_queries:
            all_docs.extend(self._get_relevant_documents_for_one_query(q))

        # 去重（按 page_content）
        unique_docs = {}
        for doc in all_docs:
            key = doc.page_content.strip()
            if key not in unique_docs:
                unique_docs[key] = doc

        return list(unique_docs.values())
