import os
import re
import time
import requests

# 配置文件路径
FILE_PATH = "ali_shares.txt"

def check_link_exist(share_id):
    """
    使用阿里云盘官方正确的分享查询接口
    """
    # 官方标准的获取分享信息接口
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
        response = requests.post(url, json=payload, headers=headers, timeout=6)
        
        # 如果返回 404 或其他错误，打印出来便于观察
        if response.status_code != 200:
            print(f"    [提示] 接口返回状态码 {response.status_code}")
            # 如果是 404，说明接口路径不对或失效，这里放行避免误杀
            return True
            
        res_data = response.json()
        
        # 检查阿里云盘明确的失效错误码
        if "code" in res_data:
            code_str = str(res_data["code"])
            if code_str in ["ShareLinkNotFound", "NotFound", "ShareLinkCancelled", "ShareLinkForbidden"]:
                print(f"    [失效] 阿里云盘反馈链接不存在: {code_str}")
                return False
                
        return True
        
    except Exception as e:
        print(f"    [网络异常] {e}")
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

    print(f"=== 开始精准校验，共读取到 {len(lines)} 行记录 ===")
    
    valid_records = []
    dead_count = 0
    skipped_count = 0

    for line in lines:
        original_line = line.strip()
        
        if not original_line or original_line.startswith("#"):
            continue

        # 核心改进：精准通过正则提取带有 0: 或 1: 的分享ID
        share_id = ""
        
        # 在整行中搜索形如 0:5JnzcFFWa6Y 中的分享码部分
        match = re.search(r'\b\d+:([a-zA-Z0-9]{11,14})\b', original_line)
        if match:
            share_id = match.group(1)
        else:
            # 备用匹配：直接找 11-14 位的纯字母数字
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

        # 测试有效性
        is_alive = check_link_exist(share_id)
        
        if not is_alive:
            print(f"[剔除死链] {original_line}  -> (提取的纯净ID: {share_id})")
            dead_count += 1
        else:
            print(f"[保留有效] ID: {share_id}")
            valid_records.append(original_line)
            
        time.sleep(0.3)

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
