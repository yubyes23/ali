import os
import re
import time
import requests

# 配置文件路径
FILE_PATH = "ali_shares.txt"

def check_link_by_web(share_id):
    """
    通过直接访问阿里云盘分享落地页的 HTTP 状态码来判断存活
    返回: True (活着), False (死链/404/不存在)
    """
    url = f"https://www.alipan.com/s/{share_id}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9",
    }
    
    try:
        # 使用 allow_redirects=True 顺便处理重定向
        response = requests.get(url, headers=headers, timeout=8, allow_redirects=True)
        
        # 如果网页直接返回 404，或者提示页面不存在，说明死链
        if response.status_code == 404:
            return False
            
        # 有时候阿里云盘死链会重定向到一个统一的“页面不存在”或提示页，可以通过网页文本简单二次判断
        body_text = response.text
        if "已被取消" in body_text or "不存在" in body_text or "已失效" in body_text:
            return False
            
        # 只要能正常响应（例如 200），且没有明显的失效字眼，就判定为正常
        return True
        
    except requests.exceptions.RequestException:
        # 网络波动超时等情况，为防止误杀，默认判定为存活保留
        return True
    except Exception:
        return True

def main():
    if not os.path.exists(FILE_PATH):
        print(f"[-] 找不到文件: {FILE_PATH}，请确认该文件与脚本在同一目录下。")
        return

    lines = []
    for encoding in ['utf-8', 'gbk', 'utf-16']:
        try:
            with open(FILE_PATH, "r", encoding=encoding) as f:
                lines = f.readlines()
            break
        except UnicodeDecodeError:
            continue

    if not lines:
        print(f"[-] 文件 {FILE_PATH} 读取为空！")
        return

    print(f"=== 开始网页状态校验，共读取到 {len(lines)} 行记录 ===")
    
    valid_records = []
    dead_count = 0
    skipped_count = 0

    for line in lines:
        original_line = line.strip()
        
        if not original_line or original_line.startswith("#"):
            continue

        # 精准匹配 0: 或 1: 后面的 11-14 位分享码
        share_id = ""
        match = re.search(r'\b\d+:([a-zA-Z0-9]{11,14})\b', original_line)
        if match:
            share_id = match.group(1)
        else:
            # 备用兼容逻辑
            tokens = original_line.split()
            for token in tokens:
                clean_token = token.replace("0:", "").replace("1:", "")
                if re.match(r'^[a-zA-Z0-9]{11,14}$', clean_token):
                    share_id = clean_token
                    break

        if not share_id:
            print(f"[跳过] 无法提取有效分享码: {original_line}")
            valid_records.append(original_line)
            skipped_count += 1
            continue

        # 通过网页访问检测
        is_alive = check_link_by_web(share_id)
        
        if not is_alive:
            print(f"[剔除死链] {original_line}  -> (提取的纯净ID: {share_id})")
            dead_count += 1
        else:
            print(f"[保留有效] ID: {share_id}")
            valid_records.append(original_line)
            
        time.sleep(0.3)  # 保持适当缓冲，避免请求太快触发 Cloudflare/防火墙拦截

    # 写回原文件
    with open(FILE_PATH, "w", encoding="utf-8") as f:
        for record in valid_records:
            f.write(record + "\n")

    print("\n=== 清理完成统计 ===")
    print(f"原始总行数: {len(lines)}")
    print(f"剔除死链数: {dead_count}")
    print(f"跳过未校验数: {skipped_count}")
    print(f"最终保留有效数: {len(valid_records)}")

if __name__ == "__main__":
    main()
