import json
import time
from playwright.sync_api import sync_playwright

def main():
    share_url = "https://www.alipan.com/s/WqpSshkZP9g/folder/651bffcd16ce6c2ad62944678622e204e6b752bf"
    
    print(f"正在启动深度抓取脚本: {share_url}")
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
            print("正在访问分享链接...")
            page.goto(share_url, timeout=60000, wait_until="domcontentloaded")
            time.sleep(5)
            
            # 1. 滚动页面以加载完当前目录下的所有文件夹（处理懒加载）
            print("正在滚动页面以加载所有文件夹...")
            for _ in range(5):  # 滚动5次，视文件夹多少可调
                page.keyboard.press("PageDown")
                time.sleep(1.5)
            
            # 2. 精准提取当前目录下的文件夹/文件名称以及可能带有的后缀
            # 阿里云盘的文件列表通常包含在特定样式的行或带有标题的元素中
            print("正在提取当前目录结构...")
            
            # 尝试通过更精准的选择器获取文件列表项
            items_data = []
            
            # 抓取所有带有文件名特征的元素
            # 阿里云盘网页版文件名通常在具有特定 class 或 title 属性的标签里
            elements = page.locator('.file-item, [class*="Item"], [class*="row"]').all()
            
            folders = []
            for el in elements:
                try:
                    text = el.inner_text().strip()
                    if text:
                        lines = [l.strip() for l in text.split("\n") if l.strip()]
                        # 过滤掉日期和杂项，寻找真正的名字
                        for line in lines:
                            # 排除常见 UI 垃圾文本
                            if not any(kw in line for kw in ["下载", "SVIP", "分享", "实时同步", "共 ", "按名称", "公众号", "08/", "06/", "2025/", "今天"]):
                                if line not in folders:
                                    folders.append(line)
                except:
                    continue
            
            print(f"成功解析到有效项目共 {len(folders)} 个。")
            
            # 结构化存储结果
            result = {
                "update_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                "source_url": share_url,
                "total_items": len(folders),
                "items": folders
            }
            
            with open("alipan_list.json", "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print("已成功更新 alipan_list.json！")
                
        except Exception as e:
            print(f"抓取出现错误: {e}")
            page.screenshot(path="error_snapshot.png", full_page=True)
            raise e
        finally:
            browser.close()

if __name__ == "__main__":
    main()
