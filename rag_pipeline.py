from langchain.chains import RetrievalQA
from langchain_google_vertexai import ChatVertexAI
from embedding_database import MilvusStorage
from retriever import MilvusMultiQueryRetriever
from langchain.prompts import PromptTemplate

import os
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./my-gemini-key.json"

class RAGPipeline:
    default_template_rq = """Use the following context to answer the question at the end. If you don’t know the answer, just say you don’t know—don’t try to make one up.
    {context}
    Question: {question}
    Answer:"""

    def __init__(
        self,
        collection_name: str = "xiaohongshu_content",
        db_path: str = "./milvus_demo.db",
        top_k: int = 3,
        temperature: float = 0.7,
        model_name: str = "gemini-1.5-pro",
        template: str = default_template_rq
    ):
        # 初始化向量库
        self.storage = MilvusStorage(collection_name=collection_name, db_path=db_path)

        # 初始化 LLM & prompt
        self.llm = ChatVertexAI(model_name=model_name, temperature=temperature)
        self.QA_CHAIN_PROMPT = PromptTemplate(input_variables=["context","question"],
                                template=template)

        # 构建 Retriever
        self.retriever = MilvusMultiQueryRetriever(storage=self.storage, top_k=top_k, query_rewrite=True, llm=self.llm)

        # 构建 QA Chain
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            retriever=self.retriever,
            return_source_documents=True,
            chain_type_kwargs={"prompt": self.QA_CHAIN_PROMPT}
        )

    def answer(self, query: str) -> dict:
        """
        输入自然语言问题，返回答案及其来源文档。
        """
        result = self.qa_chain.invoke(query)
        return {
            "answer": result["result"],
            "sources": [
                {
                    "title": doc.metadata.get("title", ""),
                    "content": doc.page_content
                }
                for doc in result["source_documents"]
            ]
        }