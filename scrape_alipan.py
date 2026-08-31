import json
import time
from playwright.sync_api import sync_playwright

def main():
    share_url = "https://www.alipan.com/s/WqpSshkZP9g/folder/651bffcd16ce6c2ad62944678622e204e6b752bf"
    
    print(f"正在以防检测模式启动浏览器: {share_url}")
    with sync_playwright() as p:
        # 针对反爬进行定制启动参数
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled", # 核心：隐藏自动化特征
                "--disable-infobars",
                "--start-maximized"
            ]
        )
        
        # 创建更真实的浏览器上下文
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            device_scale_factor=1,
            is_mobile=False,
            has_touch=False
        )
        
        page = context.new_page()
        
        # 注入脚本绕过 navigator.webdriver 检测
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        try:
            print("正在访问页面...")
            page.goto(share_url, timeout=60000, wait_until="domcontentloaded")
            
            # 给予充足的时间让前端 JS 动态渲染
            print("等待网络请求与列表渲染 (10秒)...")
            time.sleep(10)
            
            # 保存当前截图，如果再次失败可以在 GitHub Actions 的 Artifacts 里查看现场
            page.screenshot(path="debug_snapshot.png", full_page=True)
            
            # 尝试抓取页面中所有可能包含文件名文本的标签
            # 阿里云盘通常用 span、div 渲染文件名，这里提取所有文本后通过代码过滤
            print("正在提取页面文本内容...")
            all_texts = page.locator("body").all_text_contents()
            
            # 获取所有具有 title 属性或者常见文本的元素
            elements = page.locator("span, div, a").all_inner_texts()
            
            # 简单清洗：把获取到的文本按行拆分并去重
            candidates = []
            for text in elements:
                lines = text.split("\n")
                for line in lines:
                    cleaned_line = line.strip()
                    # 过滤掉太短或明显的 UI 按钮文字
                    if cleaned_line and len(cleaned_line) > 1 and cleaned_line not in ["网盘", "分享", "阿里云盘", "登录", "注册"]:
                        candidates.append(cleaned_line)
            
            # 去重保留顺序
            file_names = list(dict.fromkeys(candidates))
            
            print(f"初步捕获到相关文本数量: {len(file_names)}")
            
            result = {
                "update_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                "source_url": share_url,
                "files": file_names[:100] # 截取前100条预览
            }
            
            with open("alipan_list.json", "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print("成功生成 alipan_list.json 文件！")
                
        except Exception as e:
            print(f"抓取异常: {e}")
            page.screenshot(path="error_snapshot.png", full_page=True)
            raise e
        finally:
            browser.close()

if __name__ == "__main__":
    main()
