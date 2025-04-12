from playwright.sync_api import sync_playwright
import time
import random
import pandas as pd
from tqdm import tqdm
import os

def crawl_xiaohongshu_board(board_url, excel_path='xiaohongshu_board.xlsx'):
    """
    爬取小红书收藏夹内容
    Args:
        board_url: 收藏夹URL
        excel_path: Excel文件保存路径，默认为'xiaohongshu_board.xlsx'
    Returns:
        pd.DataFrame: 包含标题、内容和URL的DataFrame
    """
    def sign_in(page):
        # 检查是否已经登录
        page.goto("https://www.xiaohongshu.com")
        try:
            # 尝试查找登录按钮，如果找不到说明已经登录
            page.wait_for_selector("text=登录", timeout=5000)
            print("未检测到登录状态，请在弹出的浏览器窗口中完成登录...")
            input("登录完成后请在终端按回车继续...")
        except:
            print("检测到已登录状态，继续执行...")

    def scroll_and_collect(page, times=1):
        print("开始滚动页面并收集链接...")
        all_data = set()
        for i in tqdm(range(times), desc="滚动中"):
            # 使用JavaScript一次性获取所有链接，提高效率
            note_elements = page.evaluate('''
                () => Array.from(document.querySelectorAll('section.note-item a.cover.mask.ld')).map(a => a.getAttribute('href'))
            ''')
            
            new_links = {f"https://www.xiaohongshu.com{href}" for href in note_elements if href}
            all_data.update(new_links)
            print(f"epoch {i+1}: 找到 {len(new_links)} 个新链接，总计 {len(all_data)} 个")

            # 滚动到底部
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(3)  # 保持3秒等待时间确保内容加载

        return list(all_data)

    def extract_detail(page, note_url, retry_count=2):
        for attempt in range(retry_count):
            try:
                # 使用更快的页面加载策略
                page.goto(note_url, wait_until='domcontentloaded', timeout=8000)
                
                # 等待关键元素加载
                page.wait_for_selector(".title", timeout=5000)
                page.wait_for_selector(".note-text", timeout=5000)
                
                # 使用evaluate一次性获取数据，减少网络请求
                data = page.evaluate('''
                    () => {
                        const title = document.querySelector('.title')?.innerText?.trim() || '';
                        const content = document.querySelector('.note-text')?.innerText?.trim() || '';
                        return [title, content];
                    }
                ''')
                
                if data and (data[0] or data[1]):  # 确保至少有标题或内容
                    return [data[0], data[1], note_url]  # 返回标题、内容和URL
                    
                if attempt < retry_count - 1:
                    time.sleep(1)
                
            except Exception as e:
                if attempt < retry_count - 1:
                    print(f"第 {attempt + 1} 次抓取失败: {note_url} | 将重试")
                    time.sleep(2)
                else:
                    print(f"抓取详情失败: {note_url} | 原因: {e}")
        return None

    # 使用持久化上下文
    user_data_dir = os.path.join(os.path.expanduser("~"), ".config", "xiaohongshu-browser")
    
    # 不使用 with 语句，直接创建 playwright 实例
    p = sync_playwright().start()
    browser = p.chromium.launch_persistent_context(
        user_data_dir,
        headless=False,
        viewport={'width': 1920, 'height': 1080},
        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    )
    page = browser.new_page()
    
    sign_in(page)
    
    page.goto(board_url)
    print("正在加载收藏夹内容...")
    time.sleep(3)  # 减少初始等待时间
    
    note_links = scroll_and_collect(page, times=2)
    
    print("开始抓取详情页内容...")
    all_contents = []
    for link in tqdm(note_links, desc="详情抓取"):
        time.sleep(random.uniform(1, 2))  # 减少等待时间
        detail = extract_detail(page, link)
        if detail:
            all_contents.append(detail)
    
    # 创建DataFrame
    df = pd.DataFrame(all_contents, columns=['title', 'content', 'url'])
    df = df.drop_duplicates()
    
    # 保存到Excel
    df.to_excel(excel_path, index=False)
    print(f"数据已保存至 {excel_path}，共 {len(df)} 条记录")
    
    print("爬虫任务完成！浏览器保持打开状态，可以继续使用。")
    print("如果要关闭浏览器，请手动关闭浏览器窗口。")
    
    return df

if __name__ == "__main__":
    # 示例用法
    board_url = "https://www.xiaohongshu.com/board/67f9970b0000000022039d1a"
    df = crawl_xiaohongshu_board(board_url)
    # 可以直接使用返回的DataFrame
    print(df.head())
