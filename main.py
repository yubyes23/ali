from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from playwright.sync_api import sync_playwright

app = FastAPI()

class Task(BaseModel):
    url: str
    cookies: dict = None # 传入网盘的登录态

@app.post("/save")
def save_link(task: Task):
    with sync_playwright() as p:
        # 启动无头浏览器
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        
        # 如果有登录 Cookie，注入进去
        if task.cookies:
            context.add_cookies(task.cookies)
            
        page = context.new_page()
        try:
            # 1. 打开分享链接
            page.goto(task.url, timeout=30000)
            
            # 2. 模拟点击保存按钮（根据实际网盘页面的选择器编写）
            # page.click(".save-btn-class")
            # page.wait_for_timeout(3000)
            
            browser.close()
            return {"status": "success", "message": "转存指令已执行"}
        except Exception as e:
            browser.close()
            raise HTTPException(status_code=500, detail=str(e))
