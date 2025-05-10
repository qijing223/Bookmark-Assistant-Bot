from embedding_database import MilvusStorage
from crawl_xiaohongshu_board import crawl_xiaohongshu_board
from pymilvus import MilvusClient

# 示例主函数，演示如何使用 MilvusStorage
if __name__ == "__main__":
    # 爬取数据（要求 crawl_xiaohongshu_board 实现返回 DataFrame，包含 "title" 和 "content" 列）
    '''
    board_url = "https://www.xiaohongshu.com/board/67f9970b0000000022039d1a"
    df = crawl_xiaohongshu_board(board_url)
    
    # 先检查并删除已存在的集合
    client = MilvusClient("./milvus_demo.db")
    if client.has_collection(collection_name="xiaohongshu_content"):
        client.drop_collection(collection_name="xiaohongshu_content")
    client.close()
     # 插入数据
    res_insert = storage.insert_data(df)
    print("插入数据结果：", res_insert)
    '''
    
    # 创建 MilvusStorage 实例
    storage = MilvusStorage(collection_name="xiaohongshu_content", db_path="./milvus_demo.db")
    
    
    # 搜索示例：查找与查询文本最相似的记录
    res_search = storage.search("How do you solve a Rubik’s Cube?", top_k=3, similarity_threshold=0.2)
    print("搜索结果：", res_search)
    
    res_search = storage.search("hangzhou", top_k=3, similarity_threshold=0.2)
    print("搜索结果：", res_search)

    
    # 查询示例：根据过滤条件查询（例如，根据标题关键词）
    res_query = storage.query("title like '%rice%'")
    print("查询结果：", res_query)

    # 删除db内容
    # storage.client.drop_collection(collection_name="xiaohongshu_content")

    # storage.close()
