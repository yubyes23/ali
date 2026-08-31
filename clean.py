import os
import re
import time
import requests

# 配置文件路径
FILE_PATH = "ali_shares.txt"

def check_link_exist(share_id):
    """第一轮：调用阿里云盘真实的分享校验接口"""
    # 阿里云盘官方公开分享解析 API 地址
    url = "https://api.alipan.com/v2/share_link/get_share_by_code"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Content-Type": "application/json",
        "Referer": "https://www.alipan.com/"
    }
    
    payload = {
        "share_code": share_id
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=5)
        res_data = response.json()
        
        # 如果返回结果中包含 code 且提示未找到，说明分享失效/被取消
        if "code" in res_data:
            code_str = str(res_data["code"])
            if "NotFound" in code_str or "ShareLinkNotFound" in code_str or "PassCode" in code_str:
                # 注意：如果是因为需要密码而返回特定错误码，其实链接是存在的。
                # 但通常 get_share_by_code 只需要 share_code 即可返回基本信息。
                pass
            # 明确为找不到或失效
            if code_str in ["ShareLinkNotFound", "NotFound", "ShareLinkCancelled"]:
                return False
                
        # HTTP 状态码非 200 视作失效
        if response.status_code != 200:
            return False
            
        # 如果能正常拿到基本响应结构（例如包含 share_id 或 warning 等），说明链接活着
        return True
    except Exception as e:
        # 网络异常或解析错误时保守起见先判定为存活，避免误杀，或者根据需求返回 False
        return True

def check_link_content(share_id):
    """第二轮：测试是否为空内容或被风控 (预留接口)"""
    try:
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
        print(f"[-] 文件 {FILE_PATH} 读取为空，或者编码无法识别！")
        return

    print(f"=== 开始处理，共读取到 {len(lines)} 行记录 ===")
    
    valid_records = []
    dead_count = 0
    empty_count = 0
    skipped_count = 0

    for line in lines:
        original_line = line.strip()
        
        if not original_line or original_line.startswith("#"):
            continue

        # 提取字段
        tokens = original_line.split()
        share_id = ""

        # 匹配 0:分享ID 格式
        for token in tokens:
            if re.match(r'^\d+:[a-zA-Z0-9]+$', token):
                share_id = token.split(":")[-1]
                break
            elif re.match(r'^[a-zA-Z0-9]{11,14}$', token):
                share_id = token
                break

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

        # 执行真实的 API 接口检测
        if not check_link_exist(share_id):
            print(f"[失效] 剔除死链: {original_line}  -> (纯净ID: {share_id})")
            dead_count += 1
            continue

        if not check_link_content(share_id):
            print(f"[风控/空] 剔除空内容: {original_line}")
            empty_count += 1
            continue

        print(f"[正常] 验证通过: {original_line}  -> (纯净ID: {share_id})")
        valid_records.append(original_line)
        time.sleep(0.3)  # 控制请求频率防止触发安全频控

    # 写回原文件（保留原有的 0: 格式排版）
    with open(FILE_PATH, "w", encoding="utf-8") as f:
        for record in valid_records:
            f.write(record + "\n")

    print("\n=== 清理完成统计 ===")
    print(f"原始总行数: {len(lines)}")
    print(f"剔除死链数: {dead_count}")
    print(f"剔除风控数: {empty_count}")
    print(f"跳过未校验: {skipped_count}")
    print(f"剩余有效数: {len(valid_records)}")

if __name__ == "__main__":
    main()
