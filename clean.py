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

        # 1. 解析时：剔除行首的容器分类标记 (如 "0:", "0: " 等)，避免混淆
        clean_line = re.sub(r'^\d+:\s*', '', original_line)

        # 2. 智能切分数据 (兼容逗号、竖线、空格)
        if "," in clean_line:
            parts = [p.strip() for p in clean_line.split(",")]
        elif "|" in clean_line:
            parts = [p.strip() for p in clean_line.split("|")]
        else:
            parts = clean_line.split()

        if not parts:
            continue

        # 3. 智能提取 Share ID
        share_id = ""
        for part in parts:
            # 兼容带有完整 alipan.com/s/ 或 aliyundrive.com/s/ 的链接
            if "/s/" in part:
                share_id = part.split("/s/")[-1].split("/")[0].strip()
                break
            # 匹配典型的 11-14 位纯字母数字分享码
            elif re.match(r'^[a-zA-Z0-9]{11,14}$', part):
                share_id = part
                # 尽量采用后面的字符串作为ID（防止刚好前面的路径全英文）
                if len(parts) > 1 and parts.index(part) > 0:
                    break

        # 如果正则没抓到，强制取列表的第 2 个或第 1 个元素兜底
        if not share_id:
            if len(parts) >= 2:
                share_id = parts[1]
            else:
                share_id = parts[0]

        # 如果兜底后 ID 仍然为空或含有明显非 ID 字符，跳过
        if not share_id or len(share_id) < 6:
            print(f"[跳过] 无法提取有效分享码: {original_line}")
            valid_records.append(original_line)
            skipped_count += 1
            continue

        # 4. 执行存活校验
        if not check_link_exist(share_id):
            print(f"[失效] 剔除死链: {original_line}  -> (提取的ID: {share_id})")
            dead_count += 1
            continue

        if not check_link_content(share_id):
            print(f"[风控/空] 剔除空内容: {original_line}")
            empty_count += 1
            continue

        # 校验通过，完整保留原始行（带有 0: 标记）
        print(f"[正常] 验证通过: {original_line}  -> (提取的ID: {share_id})")
        valid_records.append(original_line)
        time.sleep(0.3)  # 控制并发防屏蔽

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
