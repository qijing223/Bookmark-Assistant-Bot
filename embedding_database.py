from pymilvus import MilvusClient
from sentence_transformers import SentenceTransformer
import numpy as np
import pandas as pd

# 假设已有的爬虫函数（需要用户自行实现或导入）
from crawl_xiaohongshu_board import crawl_xiaohongshu_board

class MilvusStorage:
    def __init__(self, collection_name="xiaohongshu_content", db_path="./milvus_demo.db"):
        """
        初始化 Milvus 存储
        Args:
            collection_name: 集合名称
            db_path: Milvus Lite 数据库路径
        """
        # 使用 MilvusClient 初始化（数据库文件会存储在 db_path 指定的位置）
        self.client = MilvusClient(db_path)
        self.collection_name = collection_name
        self.dim = 384  # MiniLM-L12-v2 的向量维度
        
        # 如果集合不存在，则创建（创建时只需指定 collection_name 和 dimension）
        if not self.client.has_collection(collection_name):
            self.client.create_collection(
                collection_name=collection_name,
                dimension=self.dim
            )
        
        # 初始化 SentenceTransformer 模型，用于生成文本嵌入
        self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    
    def _get_embeddings(self, texts):
        """获取文本的嵌入向量，关闭进度条显示"""
        embeddings = self.model.encode(texts, show_progress_bar=False)
        return embeddings.tolist()
    
    def insert_data(self, df):
        """
        将数据插入到 Milvus
        Args:
            df: pandas DataFrame，要求包含 "title" 和 "content" 两列
        """
        # 提取文本信息
        titles = df['title'].tolist()
        contents = df['content'].tolist()
        # 拼接 title 和 content 生成整体文本
        combined_texts = [f"{t} {c}" for t, c in zip(titles, contents)]
        # 计算文本嵌入
        embeddings = self._get_embeddings(combined_texts)
        
        # 构造数据，每条记录为一个字典，不需要存储 url（如果需要可自行添加）
        data = []
        for i, emb in enumerate(embeddings):
            data.append({
                "id": i,                # 可选字段，若不需要可以由 Milvus 自动生成
                "vector": emb,          # 向量字段
                "title": titles[i],     # 文本标题
                "content": contents[i]  # 文本内容
            })
        
        # 插入数据到指定集合
        res = self.client.insert(
            collection_name=self.collection_name,
            data=data
        )
        return res
    
    def search(self, query_text, top_k=5):
        """
        搜索相似内容
        Args:
            query_text: 查询文本
            top_k: 返回最相似的前 k 条记录
        Returns:
            搜索结果（列表）
        """
        # 计算查询文本的嵌入向量
        query_embedding = self._get_embeddings([query_text])[0]
        res = self.client.search(
            collection_name=self.collection_name,
            data=[query_embedding],
            limit=top_k,
            output_fields=["title", "content"]
        )
        return res
    
    def query(self, filter_str):
        """
        根据过滤条件查询记录
        Args:
            filter_str: 查询过滤表达式，例如 "title like '%AI%'"
        Returns:
            查询结果
        """
        res = self.client.query(
            collection_name=self.collection_name,
            filter=filter_str,
            output_fields=["title", "content"]
        )
        return res
    
    def delete(self, filter_str):
        """
        根据过滤条件删除记录
        Args:
            filter_str: 删除过滤表达式，例如 "title == 'xxx'"
        Returns:
            删除操作结果
        """
        res = self.client.delete(
            collection_name=self.collection_name,
            filter=filter_str
        )
        return res

# 示例主函数，演示如何使用 MilvusStorage
if __name__ == "__main__":
    # 爬取数据（要求 crawl_xiaohongshu_board 实现返回 DataFrame，包含 "title" 和 "content" 列）
    board_url = "https://www.xiaohongshu.com/board/67f9970b0000000022039d1a"
    df = crawl_xiaohongshu_board(board_url)
    
    # 创建 MilvusStorage 实例（若集合已存在则复用）
    storage = MilvusStorage(collection_name="xiaohongshu_content", db_path="./milvus_demo.db")
    
    # 插入数据
    res_insert = storage.insert_data(df)
    print("插入数据结果：", res_insert)
    
    # 搜索示例：查找与查询文本最相似的记录
    res_search = storage.search("rice", top_k=3)
    print("搜索结果：", res_search)
    
    # 查询示例：根据过滤条件查询（例如，根据标题关键词）
    res_query = storage.query("title like '%rice%'")
    print("查询结果：", res_query)

    # 删除db内容
    storage.client.drop_collection(collection_name="xiaohongshu_content")
