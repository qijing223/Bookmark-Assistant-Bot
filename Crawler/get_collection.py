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
    sleep(1)  # 留足扫码时间

def scroll_and_collect(times=1):
    all_data = set()  # 用 set 去重链接

    for i in tqdm(range(times)):
        sleep(random.uniform(1, 2))
        page.scroll.to_bottom()
        sleep(2)

        sections = page.eles('a.cover.mask.ld')
        for section in sections:
            try:
                href = section.attr('href')
                if href and href.startswith('/explore/'):  # 仅保留笔记链接
                    full_link = f'https://www.xiaohongshu.com{href}'
                    all_data.add(full_link)
            except:
                continue

    print(f"✅ 共获取到 {len(all_data)} 篇笔记链接")
    return list(all_data)

def extract_detail(note_url):
    try:
        page.get(note_url)
        page.wait.ele('.title', timeout=5)

        title = page.ele('.title', timeout=1).text
        author = page.ele('.author-name', timeout=1).text
        author_link = page.ele('.author-name', timeout=1).parent().link
        author_img = page.ele('.author-avatar img', timeout=1).link
        like = page.ele('.interact-btn.like .num', timeout=1).text or '0'

        return [title, author, note_url, author_link, author_img, int(like)]
    except Exception as e:
        print(f"❌ 获取失败: {note_url} | 原因: {e}")
        return None

def save_to_excel(data):
    df = pd.DataFrame(data, columns=['title', 'author', 'note_link', 'author_link', 'author_img', 'like'])
    df = df.drop_duplicates()
    df = df.sort_values(by='like', ascending=False)
    df.to_excel('xiaohongshu_board.xlsx', index=False)
    print("✅ 已保存为 xiaohongshu_board.xlsx")

if __name__ == "__main__":
    sign_in()

    board_url = 'https://www.xiaohongshu.com/board/663250f30000000017037d8d?xhsshare=CopyLink&appuid=605dff60000000000101dfa0&apptime=1743377081&share_id=f46a0ef7ec8a40e2aec4047a42d08204'
    page.get(board_url)
    print("正在加载收藏夹内容...")

    page.wait.eles_loaded('a.cover.mask.ld', timeout=15)
    note_links = scroll_and_collect(times=15)

    print("开始抓取详情页内容...")
    all_contents = []
    for link in tqdm(note_links):
        detail = extract_detail(link)
        if detail:
            all_contents.append(detail)

    save_to_excel(all_contents)
