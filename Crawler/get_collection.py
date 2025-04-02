from DrissionPage import ChromiumPage
from time import sleep
import pandas as pd
from tqdm import tqdm
import random

# 创建 ChromiumPage 实例
page = ChromiumPage()

def sign_in():
    page.get('https://www.xiaohongshu.com')
    print("请在弹出的浏览器窗口中完成登录")
    sleep(1)  

def scroll_and_collect(times=1):
    print("开始滚动页面并收集链接...")
    all_data = set()
    for i in tqdm(range(times)):
        print("page",page.html[:10])
        # 使用 DOM 选择器定位 note 链接
        note_elements = page.eles('section.note-item a.cover.mask.ld')
        print(f"epoch {i+1}: link_sum {len(note_elements)}")
        for ele in note_elements:
            href = ele.attr('href')
            if href:
                full_link = f'https://www.xiaohongshu.com{href}'
                all_data.add(full_link)
        print(f"epoch {i+1}: link_sum_without_repition {len(all_data)} ")
        page.scroll.to_bottom()
        sleep(5)
    print(f"total_link: {len(all_data)}")
    return list(all_data)

def extract_detail(note_url):
    try:
        page.get(note_url)
        # 根据详情页实际 DOM 结构调整等待与选择器
        page.wait.ele('.title', timeout=5)
        title = page.ele('.title', timeout=1).text
        author = page.ele('.author-name', timeout=1).text
        author_link = page.ele('.author-name', timeout=1).parent().link
        author_img = page.ele('.author-avatar img', timeout=1).link
        like_text = page.ele('.interact-btn.like .num', timeout=1).text or '0'
        like = int(like_text.replace(',', ''))  # 如数字中包含逗号则去除
        return [title, author, note_url, author_link, author_img, like]
    except Exception as e:
        print(f"detail failure: {note_url} | reason: {e}")
        return None

def save_to_excel(data):
    df = pd.DataFrame(data, columns=['title', 'author', 'note_link', 'author_link', 'author_img', 'like'])
    df = df.drop_duplicates()
    df = df.sort_values(by='like', ascending=False)
    df.to_excel('xiaohongshu_board.xlsx', index=False)
    print("已保存为 xiaohongshu_board.xlsx")

if __name__ == "__main__":
    sign_in()
    board_url = 'https://www.xiaohongshu.com/board/663250f30000000017037d8d?xhsshare=CopyLink&appuid=605dff60000000000101dfa0&apptime=1743377081&share_id=f46a0ef7ec8a40e2aec4047a42d08204'
    page.get(board_url)
    print("正在加载收藏夹内容...")
    sleep(5)  # 等待页面异步加载
    print("page",page.html[:10])

    note_links = scroll_and_collect(times=2)

    print("开始抓取详情页内容...")
    all_contents = []
    for link in tqdm(note_links):
        detail = extract_detail(link)
        if detail:
            all_contents.append(detail)

    save_to_excel(all_contents)
