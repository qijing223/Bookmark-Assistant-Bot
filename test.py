from rag_pipeline import RAGPipeline

def run_test():
    # 实例化 RAGPipeline
    pipeline = RAGPipeline(
        collection_name="xiaohongshu_content",
        db_path="./milvus_demo.db",
        top_k=3,
        temperature=0.7,
        model_name="gemini-1.5-pro"
    )
    # 测试查询
    query = "Steamed Dumpling Guide."
    response = pipeline.answer(query)

    # 打印结果
    print("\n🧠 问题：", query)
    print("\n💬 答案：", response["answer"])
    print("\n📚 来源文档：")
    for i, src in enumerate(response["sources"], start=1):
        print(f"\n--- Source {i} ---")
        print("📌 标题：", src["title"])
        print("📄 内容片段：", src["content"][:200], "..." if len(src["content"]) > 200 else "")

if __name__ == "__main__":
    run_test()