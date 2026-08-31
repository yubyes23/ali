import json
import time
from playwright.sync_api import sync_playwright

def main():
    share_url = "https://www.alipan.com/s/WqpSshkZP9g/folder/651bffcd16ce6c2ad62944678622e204e6b752bf"
    
    print(f"正在以拟真慢速模式启动抓取: {share_url}")
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled"
            ]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080}
        )
        page = context.new_page()
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        try:
            print("正在安全访问页面...")
            page.goto(share_url, timeout=60000, wait_until="domcontentloaded")
            
            # 初始等待，模拟人类初次浏览页面
            print("等待初始加载 (8秒)...")
            time.sleep(8)
            
            # 模拟缓慢向下滚动加载全部 300 多个文件夹
            print("开始慢速滚动页面以触发全量加载...")
            all_folders = set()
            
            # 300多个项目大概需要滚动 15~20 次，每次滚动一小段距离并停顿
            for i in range(25):
                print(f"正在进行第 {i+1}/25 次滚动...")
                # 页面向下滚动 800 像素
                page.evaluate("window.scrollBy(0, 800);")
                # 停顿 3 秒，给阿里云盘前端异步加载留足时间，防止触发风控或漏加载
                time.sleep(3)
                
                # 实时抓取当前页面中露出来的所有文本项进行累加
                elements = page.locator('.file-item, [class*="Item"], [class*="row"], span[title]').all()
                for el in elements:
                    try:
                        text = el.inner_text().strip()
                        if text:
                            for line in text.split("\n"):
                                clean_line = line.strip()
                                # 过滤掉系统 UI、日期、广告等杂项
                                if clean_line and len(clean_line) > 1:
                                    if not any(kw in clean_line for kw in [
                                        "下载", "SVIP", "分享", "实时同步", "共 ", "按名称", 
                                        "公众号", "08/", "06/", "04/", "03/", "07/", "10/", 
                                        "2025/", "2026/", "今天", "文件夹", "大小", "修改时间"
                                    ]):
                                        all_folders.add(clean_line)
                    except:
                        continue
                print(f"当前已累计收集到不重复项目数: {len(all_folders)}")

            # 转为列表并按原网页顺序保持
            final_items = list(all_folders)
            
            print(f"抓取完成！共获取到有效项目: {len(final_items)} 个")
            
            result = {
                "update_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                "source_url": share_url,
                "total_items": len(final_items),
                "items": final_items
            }
            
            with open("alipan_list.json", "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print("成功生成完整的 alipan_list.json 文件！")
                
        except Exception as e:
            print(f"抓取过程异常: {e}")
            page.screenshot(path="error_snapshot.png", full_page=True)
            raise e
        finally:
            browser.close()

if __name__ == "__main__":
    main()
