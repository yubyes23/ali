import os
import time
import requests
import re

# 配置文件路径
FILE_PATH = "ali_shares.txt"

def check_link_exist(share_id):
    """第一轮：调用阿里云盘 API 检测分享 ID 是否存活"""
    url = f"https://api.aliyundrive.v2/adrive/v3/share_link/get_share_by_code?share_code={share_id}"
    try:
        response = requests.post(url, json={"share_code": share_id}, timeout=5).json()
        if "code" in response and (response["code"] == "ShareLinkNotFound" or "NotFound" in str(response)):
            return False
        return True
    except Exception:
        return False

def check_link_content(share_id):
    """第二轮：测试是否为空内容或被风控 (预留逻辑)"""
    try:
        # 如需检测空目录，需在此处实现获取文件列表 API
        return True
    except Exception:
        return False

def main():
    if not os.path.exists(FILE_PATH):
        print(f"[-] 找不到文件: {FILE_PATH}")
        return

    valid_records = []
    dead_count = 0
    empty_count = 0
    skipped_count = 0

    with open(FILE_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()

    print(f"=== 开始处理，共读取到 {len(lines)} 行记录 ===")

for line in lines:
        original_line = line.strip()
        
        # 忽略空行和注释行
        if not original_line or original_line.startswith("#"):
            continue

        # 核心修改：精准切分每一行
        # 比如把 "/路径  0:5JnzcFFWa6Y  root" 按空白字符（空格/Tab）切成多个部分
        tokens = original_line.split()
        
        share_id = ""
        actual_index = -1
        
        # 遍历所有分段，寻找带有 "数字:" 开头的项，或者符合 11-14 位特征的项
        for i, token in enumerate(tokens):
            # 如果某一段带有形如 "0:" 或 "1:" 的前缀
            if re.match(r'^\d+:[a-zA-Z0-9]+$', token):
                share_id = token.split(":")[-1]  # 剥离冒号，只留后面的分享码
                actual_index = i
                break
            # 兼容万一没有带 0: 的纯分享码
            elif re.match(r'^[a-zA-Z0-9]{11,14}$', token):
                share_id = token
                actual_index = i
                break

        # 如果还没找到，尝试从带 /s/ 的链接中提取
        if not share_id:
            for i, token in enumerate(tokens):
                if "/s/" in token:
                    share_id = token.split("/s/")[-1].split("/")[0].strip()
                    actual_index = i
                    break

        # 兜底保险
        if not share_id and len(tokens) >= 2:
            # 默认取倒数第二个或第二个作为分享码
            candidate = tokens[1].replace("0:", "").replace("1:", "")
            if len(candidate) >= 6:
                share_id = candidate

        if not share_id or len(share_id) < 6:
            print(f"[跳过] 无法提取有效分享码: {original_line}")
            valid_records.append(original_line)
            skipped_count += 1
            continue

        # 4. 执行存活校验（此时的 share_id 已经是纯净的 5JnzcFFWa6Y，不带 0: 了）
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
        time.sleep(0.3)蔽

    # 5. 将仍存活的数据写回原文件
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
