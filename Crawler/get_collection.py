from DrissionPage import ChromiumPage
from time import sleep
import pandas as pd
from tqdm import tqdm
import random

# 创建 ChromiumPage 实例
page = ChromiumPage()

def sign_in():
    page.get('https://www.xiaohongshu.com')
    print("请在20秒内扫码登录")
    sleep(20)
    # 登录后Cookie会自动保存在浏览器配置中，后续可复用

def scroll_and_collect(times=20):
    all_data = []

    for i in tqdm(range(times)):
        sleep(random.uniform(1, 2))
        page.scroll.to_bottom()
        sleep(1)

        sections = page.eles('.note-item')
        for section in sections:
            try:
                footer = section.ele('.footer', timeout=1)
                title = footer.ele('.title', timeout=1).text
                author_wrapper = footer.ele('.author-wrapper', timeout=1)
                author = author_wrapper.ele('.author', timeout=1).text
                author_link = author_wrapper.ele('tag:a', timeout=1).link
                author_img = author_wrapper.ele('tag:img', timeout=1).link
                like = footer.ele('.like-wrapper', timeout=1).text or "0"
                note_link = section.ele('tag:a', timeout=1).link

                all_data.append([title, author, note_link, author_link, author_img, int(like)])
            except:
                continue

    return all_data

def save_to_excel(data):
    df = pd.DataFrame(data, columns=['title', 'author', 'note_link', 'author_link', 'author_img', 'like'])
    df = df.drop_duplicates()
    df = df.sort_values(by='like', ascending=False)
    df.to_excel('xiaohongshu_board.xlsx', index=False)
    print("✅ 已保存为 xiaohongshu_board.xlsx")

if __name__ == "__main__":
    sign_in()
    # 替换为你自己的收藏夹链接
    board_url = 'https://www.xiaohongshu.com/board/5e858e8f0000000001001e81?xhsshare=CopyLink&appuid=5e631c6b0000000001006dae'
    page.get(board_url)
    print("正在加载收藏夹内容...")
    sleep(3)
    data = scroll_and_collect(times=20)
    save_to_excel(data)
