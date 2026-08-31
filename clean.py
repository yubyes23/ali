import os
import re
import time
import requests

# 配置文件路径
FILE_PATH = "ali_shares.txt"

def check_link_content(share_id, extraction_code=""):
    """
    直接测试分享内容是否还在（通过获取分享文件列表接口）
    返回: True (内容正常存在), False (内容为空、已被删空或风控失效)
    """
    url = "https://api.alipan.com/adrive/v3/file/list_by_share"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Content-Type": "application/json",
        "Referer": "https://www.alipan.com/"
    }
    
    # 获取分享详情通常需要 share_id，部分有提取码的可能需要 extra_code
    payload = {
        "share_id": share_id,
        "parent_file_id": "root",  # 根目录
        "limit": 50
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=6)
        
        # 接口状态码非 200 视作异常或被风控
        if response.status_code != 200:
            print(f"    [提示] 接口返回状态码 {response.status_code}，暂且放行防止误杀")
            return True
            
        res_data = response.json()
        
        # 检查阿里云盘明确的错误码（如分享不存在、已取消等）
        if "code" in res_data:
            code_str = str(res_data["code"])
            if code_str in ["ShareLinkNotFound", "NotFound", "ShareLinkCancelled", "ShareLinkForbidden"]:
                print(f"    [内容失效] 链接已被删或屏蔽: {code_str}")
                return False
                
        # 检查文件列表项
        items = res_data.get("items", [])
        
        # 如果 items 为空，说明里面已经没有文件了（被清空或和谐）
        if isinstance(items, list) and len(items) == 0:
            print(f"    [内容为空] 分享目录内文件已被清空")
            return False
            
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"    [网络异常] 请求出错: {e}，暂且放行")
        return True
    except Exception as e:
        print(f"    [未知错误] {e}")
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
        print(f"[-] 文件 {FILE_PATH} 读取为空，或者编码无法识别！")
        return

    print(f"=== 开始内容检测，共读取到 {len(lines)} 行记录 ===")
    
    valid_records = []
    dead_count = 0
    skipped_count = 0

    for line in lines:
        original_line = line.strip()
        
        if not original_line or original_line.startswith("#"):
            continue

        # 提取字段
        tokens = original_line.split()
        share_id = ""
        pwd = ""

        # 匹配 0:分享ID 格式
        for token in tokens:
            if re.match(r'^\d+:[a-zA-Z0-9]+$', token):
                share_id = token.split(":")[-1]
                break
            elif re.match(r'^[a-zA-Z0-9]{11,14}$', token):
                share_id = token
                break

        # 提取密码（如果有的化，通常在后面）
        if len(tokens) >= 3:
            pwd = tokens[2]

        # 兜底逻辑
        if not share_id and len(tokens) >= 2:
            candidate = tokens[1].replace("0:", "").replace("1:", "")
            if len(candidate) >= 6:
                share_id = candidate

        if not share_id or len(share_id) < 6:
            print(f"[跳过] 无法提取有效分享码: {original_line}")
            valid_records.append(original_line)
            skipped_count += 1
            continue

        # 直接测试内容是否还在
        is_content_valid = check_link_content(share_id, pwd)
        
        if not is_content_valid:
            print(f"[剔除] 内容失效/空链: {original_line}  -> (纯净ID: {share_id})")
            dead_count += 1
        else:
            print(f"[正常] 内容有效: {original_line}")
            valid_records.append(original_line)
            
        time.sleep(0.4)

    # 写回原文件
    with open(FILE_PATH, "w", encoding="utf-8") as f:
        for record in valid_records:
            f.write(record + "\n")

    print("\n=== 清理完成统计 ===")
    print(f"原始总行数: {len(lines)}")
    print(f"剔除空内容/失效数: {dead_count}")
    print(f"跳过未校验数: {skipped_count}")
    print(f"最终保留有效数: {len(valid_records)}")

if __name__ == "__main__":
    main()
