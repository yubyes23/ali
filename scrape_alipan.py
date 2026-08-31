import json
import time
from playwright.sync_api import sync_playwright

def main():
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
            time.sleep(8)
            
            print(f"2. 正在寻找目标文件夹: '{target_folder_name}' ...")
            folder_locator = page.locator(f"text={target_folder_name}").first
            folder_locator.wait_for(state="visible", timeout=10000)
            folder_locator.click()
            print("成功点击进入目标文件夹！")
            
            # 给予充足的时间让子文件夹内部的虚拟列表渲染出来
            print("等待子文件夹内部列表完全渲染 (8秒)...")
            time.sleep(8)
            
            all_folders = set()
            print("3. 开始在子文件夹内滚动并广谱捕获名称...")
            
            for i in range(20):
                print(f"正在进行第 {i+1}/20 次滚动加载...")
                
                # 滚动容器
                page.evaluate("""
                    () => {
                        window.scrollBy(0, 800);
                        const scrollers = document.querySelectorAll('div');
                        scrollers.forEach(el => {
                            if (el.scrollHeight > el.clientHeight) {
                                el.scrollTop += 800;
                            }
                        });
                    }
                """)
                time.sleep(2.5)
                
                # 广谱捕获：不再局限于特定 class，而是抓取子页面中所有可能代表文件/文件夹名字的标签
                # 阿里云盘子目录通常使用 span, div 且带有文本或 title
                elements = page.locator('span, div, a').all()
                for el in elements:
                    try:
                        text = el.inner_text().strip()
                        # 有时候名字藏在 title 属性里
                        title_attr = el.get_attribute("title")
                        
                        candidates = [text, title_attr]
                        for name in candidates:
                            if name:
                                clean_name = name.strip()
                                # 过滤掉短字符、数字、时间、系统杂项
                                if clean_name and len(clean_name) > 1:
                                    if not any(kw in clean_name for kw in [
                                        "下载", "SVIP", "分享", "实时同步", "共 ", "按名称", 
                                        "公众号", "08/", "06/", "04/", "03/", "07/", "10/", 
                                        "2025/", "2026/", "今天", "文件夹", "大小", "修改时间",
                                        "上一页", "下一页", "确定", "取消", "属性", "重命名"
                                    ]) and not clean_name.isdigit():
                                        all_folders.add(clean_name)
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
