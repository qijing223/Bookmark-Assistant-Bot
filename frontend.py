import os
import json
from pathlib import Path

import gradio as gr
from vertexai import init

from rag_pipeline import RAGPipeline
from crawl_xiaohongshu_board import crawl_xiaohongshu_board
from embedding_database import MilvusStorage

# ---------- Vertex AI credential & init ----------
KEY_PATH = "./my-gemini-key.json"
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = KEY_PATH

with open(KEY_PATH, "r") as f:
    PROJECT_ID = json.load(f)["project_id"]

# 根据你的区域调整
init(project=PROJECT_ID, location="us-central1")

# ---------- Milvus / Collection settings ----------
COLLECTION_NAME = "xiaohongshu_content"
DB_PATH = "./milvus_demo.db"
FLAG_PATH = Path(".xhs_loaded.flag")   # 抓取完成的标志文件

# ---------- Helper : ensure vectors only loaded once ----------
def ensure_vectors_loaded(favorite_url: str):
    """If flag exists, skip crawling. Otherwise crawl + insert + create flag."""
    if FLAG_PATH.exists():
        return  # 已抓取过

    # --- 抓取小红书收藏夹 ---
    df = crawl_xiaohongshu_board(favorite_url)

    # --- 写入向量数据库 ---
    storage = MilvusStorage(collection_name=COLLECTION_NAME, db_path=DB_PATH)
    storage.insert_data(df)

    # --- 创建 flag 文件 ---
    FLAG_PATH.touch()

# ---------- RAG 推理 ----------
def answer_query(query: str):
    pipeline = RAGPipeline(
        collection_name=COLLECTION_NAME,
        db_path=DB_PATH,
        top_k=3,
        temperature=0.7,
        model_name="gemini-1.5-pro"
    )
    return pipeline.answer(query)

# ---------- ChatInterface 回调 ----------
def rag_chat(user_message: str, history: list[tuple[str, str]], favorite_url: str):
    if not favorite_url.strip():
        return "Please paste the bookmark link on the left first, then ask questions."

    # 确保向量已加载（首次会抓取并写入）
    ensure_vectors_loaded(favorite_url)

    # 生成回答
    response = answer_query(user_message)

    answer = f"Question: {user_message}\n\n"
    answer += f"Answer: {response['answer']}\n\n"
    answer += "Source Document:\n"
    for i, src in enumerate(response["sources"], 1):
        answer += f"\n--- Source {i} ---\n"
        answer += f"Title: {src['title']}\n"
        answer += f"URL: {src['url']}...\n"
    return answer

# ---------- Gradio UI ----------
with gr.Blocks(title="Bookmark Assistant Bot Demo") as demo:
    gr.Markdown(
        """## 🔎 Bookmark Assistant Bot
1. Paste the favorites link on the left
2. Enter keywords or questions in the chat box on the right
3. The backend will retrieve and generate answers"""
    )

    with gr.Row():
        favorite_box = gr.Textbox(
            label="📁 Bookmark link (required once)",
            placeholder="e.g., https://www.xiaohongshu.com/board/...",
            lines=1
        )

    chat = gr.ChatInterface(
        fn=rag_chat,
        additional_inputs=[favorite_box],
        examples=[["python"], ["cooking"]]
    )

# ---------- Start ----------
if __name__ == "__main__":
    demo.launch(share=False)