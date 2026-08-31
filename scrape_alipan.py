import json
import time
from playwright.sync_api import sync_playwright

def main():
    # 根分享链接
    root_share_url = "https://www.alipan.com/s/WqpSshkZP9g"
    target_folder_name = "电视剧实时同步更新"
    
    print(f"正在以拟真交互模式启动抓取: {root_share_url}")
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
            print("1. 正在访问根分享链接...")
            page.goto(root_share_url, timeout=60000, wait_until="domcontentloaded")
            
            print("等待根目录加载 (8秒)...")
            time.sleep(8)
            
            # 2. 寻找目标文件夹并点击进入
            print(f"正在寻找目标文件夹: '{target_folder_name}' ...")
            
            # 尝试通过文本精准定位并点击
            try:
                # 寻找包含目标名称的元素并点击
                folder_locator = page.locator(f"text={target_folder_name}").first
                folder_locator.wait_for(state="visible", timeout=10000)
                folder_locator.click()
                print("成功点击进入目标文件夹！")
            except Exception as click_err:
                print(f"按文本直接点击失败，尝试遍历点击: {click_err}")
                # 备用方案：截图并抛出异常，帮助排查
                page.screenshot(path="click_error_snapshot.png", full_page=True)
                raise click_err
            
            # 等待子文件夹内部页面渲染加载
            print("等待子文件夹内部列表加载 (6秒)...")
            time.sleep(6)
            
            # 3. 在子文件夹内部开始慢速向下滚动，获取所有 300 多个子项
            all_folders = set()
            print("开始在子文件夹内模拟容器滚动以加载全量数据...")
            
            for i in range(25): # 25轮滚动，确保能拉到底
                print(f"正在进行第 {i+1}/25 次滚动加载...")
                
                page.evaluate("""
                    () => {
                        window.scrollBy(0, 1000);
                        const scrollers = document.querySelectorAll('div');
                        scrollers.forEach(el => {
                            if (el.scrollHeight > el.clientHeight) {
                                el.scrollTop += 1000;
                            }
                        });
                    }
                """)
                
                time.sleep(3) # 停顿 3 秒防风控和等异步数据
                
                # 提取当前可见的文件名
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
                "source_url": root_share_url,
                "target_folder": target_folder_name,
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
