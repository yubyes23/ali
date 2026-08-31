import json
import time
from playwright.sync_api import sync_playwright

def main():
    share_url = "https://www.alipan.com/s/WqpSshkZP9g/folder/651bffcd16ce6c2ad62944678622e204e6b752bf"
    
    print(f"正在以容器滚动模式启动抓取: {share_url}")
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
            
            print("等待初始加载 (8秒)...")
            time.sleep(8)
            
            all_folders = set()
            
            # 循环向下滚动，针对阿里云盘的滚动容器进行模拟
            print("开始模拟容器滚动以加载全量数据...")
            for i in range(20):
                print(f"正在进行第 {i+1}/20 次滚动加载...")
                
                # 核心改进：同时对 window 和可能的内部滚动列表执行向下滚动指令
                page.evaluate("""
                    () => {
                        window.scrollBy(0, 1000);
                        // 寻找可能的内部滚动容器并滚动到底部
                        const scrollers = document.querySelectorAll('div');
                        scrollers.forEach(el => {
                            if (el.scrollHeight > el.clientHeight) {
                                el.scrollTop += 1000;
                            }
                        });
                    }
                """)
                
                # 留出充足时间让懒加载请求返回数据
                time.sleep(3)
                
                # 提取当前页面渲染出的所有文件名标签
                # 阿里云盘通常使用带有 title 属性的元素或者文件列表项展示名称
                elements = page.locator('.file-item-title, [class*="file-name"], [class*="ItemName"], span[title]').all()
                for el in elements:
                    try:
                        text = el.inner_text().strip() or el.get_attribute("title")
                        if text:
                            clean_text = text.strip()
                            if clean_text and len(clean_text) > 1:
                                if not any(kw in clean_text for kw in [
                                    "下载", "SVIP", "分享", "实时同步", "共 ", "按名称", 
                                    "公众号", "08/", "06/", "04/", "03/", "07/", "10/", 
                                    "2025/", "2026/", "今天", "文件夹", "大小", "修改时间"
                                ]):
                                    all_folders.add(clean_text)
                    except:
                        continue
                print(f"当前已累计收集到不重复项目数: {len(all_folders)}")

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
