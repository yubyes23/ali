import json
import time
from playwright.sync_api import sync_playwright

def main():
    # 阿里云盘分享链接和目标目录
    share_url = "https://www.alipan.com/s/WqpSshkZP9g/folder/651bffcd16ce6c2ad62944678622e204e6b752bf"
    
    print(f"正在启动浏览器抓取: {share_url}")
    with sync_playwright() as p:
        # 启动 Chromium（无头模式，适合 CI 环境）
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        page = context.new_page()
        
        try:
            # 访问链接
            page.goto(share_url, timeout=60000)
            
            # 阿里云盘通常需要一点时间通过前端 JS 渲染出文件列表，这里等待文件元素加载
            print("等待页面动态渲染...")
            # 根据阿里云盘网页版常见的 CSS 选择器或关键字进行等待
            page.wait_for_selector('.file-item-title, [class*="file-name"], [class*="ItemName"]', timeout=20000)
            
            # 多给 3 秒让异步数据彻底加载完
            time.sleep(3)
            
            # 提取所有文件名（尝试多种可能的匹配规则）
            file_names = []
            selectors = ['.file-item-title', '[class*="file-name"]', '[class*="ItemName"]', 'span[title]']
            
            for sel in selectors:
                elements = page.locator(sel).all_text_contents()
                if elements:
                    # 清理并去重
                    cleaned = [name.strip() for name in elements if name.strip()]
                    if cleaned:
                        file_names.extend(cleaned)
            
            # 去重但保留顺序
            file_names = list(dict.fromkeys(file_names))
            
            print(f"成功获取到 {len(file_names)} 个项目：")
            for name in file_names[:20]:  # 打印前20个预览
                print(f" - {name}")
                
            # 保存结果到 JSON 文件，供后续步骤或 Pages 使用
            result = {
                "update_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                "source_url": share_url,
                "files": file_names
            }
            with open("alipan_list.json", "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"抓取过程中出现异常: {e}")
            # 发生错误时截个图保存，方便在 GitHub Actions 报错时排查
            page.screenshot(path="error_snapshot.png")
            raise e
        finally:
            browser.close()

if __name__ == "__main__":
    main()
