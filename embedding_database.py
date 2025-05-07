from pymilvus import MilvusClient
from sentence_transformers import SentenceTransformer
import numpy as np
import pandas as pd
import pytesseract
from PIL import Image
import requests
from io import BytesIO
import ast
from unstructured.partition.image import partition_image


class MilvusStorage:
    def __init__(self, collection_name="xiaohongshu_content", db_path="./milvus_demo.db"):
        self.client = MilvusClient(db_path)
        self.collection_name = collection_name
        self.dim = 384  # MiniLM-L12-v2 输出维度

        if not self.client.has_collection(collection_name):
            self.client.create_collection(
                collection_name=collection_name,
                dimension=self.dim
            )

        self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

    def close(self):
        self.client.close()

    def _get_embeddings(self, texts):
        embeddings = self.model.encode(texts, show_progress_bar=False)
        return embeddings.tolist()

    def extract_ocr_with_tesseract(self, img_url: str) -> str:
        try:
            # print(f"🔍 Tesseract 提取图片: {img_url}")
            response = requests.get(img_url, timeout=8)
            img = Image.open(BytesIO(response.content)).convert("RGB")
            text = pytesseract.image_to_string(img, lang='chi_sim+eng')
            return text.strip()
        except Exception as e:
            print(f"❌ Tesseract 提取失败: {img_url}, 错误: {e}")
            return ""

    def extract_from_image_with_unstructured(self, img_url):
        try:
            response = requests.get(img_url, timeout=10)
            img_bytes = BytesIO(response.content)
            elements = partition_image(file=img_bytes)
            text_blocks = [el.text for el in elements if el.text]
            return "\n".join(text_blocks)
        except Exception as e:
            print(f"❌ 提取失败: {img_url}, 错误: {e}")
            return ""

    def insert_data(self, df):
        titles = df['title'].tolist()
        contents = df['content'].tolist()
        image_lists = df['images'].tolist() if 'images' in df.columns else ["[]"] * len(df)

        # 提取每条记录的 OCR 文本
        ocr_texts = []
        for raw in image_lists:
            try:
                urls = ast.literal_eval(raw) if isinstance(raw, str) else raw
                ocr_parts = [self.extract_ocr_with_tesseract(url) for url in urls]
                ocr_text = "\n".join([t for t in ocr_parts if t.strip()])
                if ocr_text:
                    print(ocr_text)
                else:
                    print("⚠️ 没有提取到 OCR 内容！")
            except Exception as e:
                print(f"❌ OCR 提取失败：{e}")
                ocr_text = ""
            ocr_texts.append(ocr_text)

        combined_texts = [
            f"{t} {c} {ocr}".strip()
            for t, c, ocr in zip(titles, contents, ocr_texts)
        ]

        embeddings = self._get_embeddings(combined_texts)

        data = []
        for i, emb in enumerate(embeddings):
            data.append({
                "id": i,
                "vector": emb,
                "title": titles[i],
                "content": combined_texts[i]
            })

        res = self.client.insert(
            collection_name=self.collection_name,
            data=data
        )
        return res


    def search(self, query_text, top_k=5, similarity_threshold=0.5):
        query_embedding = self._get_embeddings([query_text])[0]
        res = self.client.search(
            collection_name=self.collection_name,
            data=[query_embedding],
            limit=top_k,
            output_fields=["title", "content"]
        )
        # 过滤掉相似度低于阈值的结果
        filtered_results = []
        for match in res[0]:
            # Milvus 返回的是距离值，需要转换为相似度分数
            similarity = 1 - match["distance"]  # 将距离转换为相似度
            if similarity >= similarity_threshold:
                filtered_results.append(match)
        return [filtered_results] if filtered_results else [[]]

    def query(self, filter_str):
        res = self.client.query(
            collection_name=self.collection_name,
            filter=filter_str,
            output_fields=["title", "content"]
        )
        return res

    def delete(self, filter_str):
        res = self.client.delete(
            collection_name=self.collection_name,
            filter=filter_str
        )
        return res
