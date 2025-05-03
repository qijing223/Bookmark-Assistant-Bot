# initialize_milvus.py
from embedding_database import MilvusStorage
import pandas as pd

# 清空 collection 中所有数据的正确方式
def delete_all_from_collection(storage):
    # 获取所有数据的 ID（你插入时设置了 "id" 字段）
    all_data = storage.client.query(
        collection_name=storage.collection_name,
        filter="id >= 0",  # 假设所有 ID 都是非负整数
        output_fields=["id"]
    )
    all_ids = [doc["id"] for doc in all_data]

    if all_ids:
        storage.client.delete(
            collection_name=storage.collection_name,
            ids=all_ids  # 传入主键列表删除
        )
        print(f"🗑️ 已删除原有 {len(all_ids)} 条记录")
    else:
        print("⚠️ 集合中无数据，无需删除")

def initialize(overwrite=True):
    # 读取你爬下来的收藏夹内容
    excel_path = "./xiaohongshu_board.xlsx"
    df = pd.read_excel(excel_path)

    # 初始化 Milvus 向量数据库
    storage = MilvusStorage(collection_name="xiaohongshu_content", db_path="./milvus_demo.db")

    if overwrite:
        print("⚠️ 正在清空已有数据（覆盖模式）...")
        delete_all_from_collection(storage)

    # 插入数据
    res = storage.insert_data(df)
    print(f"✅ 成功将 {len(df)} 条笔记插入到 Milvus 中！")

if __name__ == "__main__":
    initialize()
