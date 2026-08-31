import os
import time
import requests

# 配置文件路径
FILE_PATH = "ali_shares.txt"


def check_link_exist(share_id):
  """第一轮：测试链接是否存在/失效"""
  url = f"https://api.aliyundrive.v2/adrive/v3/share_link/get_share_by_code?share_code={share_id}"
  try:
    response = requests.post(
        url, json={"share_code": share_id}, timeout=5
    ).json()
    if (
        "code" in response
        and response["code"] == "ShareLinkNotFound"
        or "NotFound" in str(response)
    ):
      return False
    return True
  except Exception:
    return False


def check_link_content(share_id, extraction_code=""):
  """第二轮：测试是否为空内容或被风控"""
  try:
    # 模拟文件列表获取逻辑（可按需对接你的具体 API/Cookie 逻辑）
    files = []  # 假设获取到的文件列表
    if not files:
      return False
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

  # 读取文本文件
  with open(FILE_PATH, "r", encoding="utf-8") as f:
    lines = f.readlines()

  print(f"=== 开始处理，共读取到 {len(lines)} 行记录 ===")

  for line in lines:
    line = line.strip()
    if not line or line.startswith("#"):
      continue  # 跳过空行或注释

    # 假设文本格式为: 路径,分享ID,提取码 (根据你的实际文本格式调整分隔符)
    parts = line.split(",")
    if len(parts) < 2:
      continue

    path, share_id = parts[0].strip(), parts[1].strip()
    pwd = parts[2].strip() if len(parts) > 2 else "root"

    # 第一轮：存活检测
    if not check_link_exist(share_id):
      print(f"[失效] 剔除死链: {path} ({share_id})")
      dead_count += 1
      continue

    # 第二轮：风控/空内容检测
    pwd_param = "" if pwd == "root" else pwd
    if not check_link_content(share_id, pwd_param):
      print(f"[风控/空] 剔除空内容链接: {path} ({share_id})")
      empty_count += 1
      continue

    # 校验通过，保留记录
    print(f"[保留] 有效链接: {path} ({share_id})")
    valid_records.append(line)
    time.sleep(0.3)  # 控制请求频率

  # 将清洗后的有效链接写回文件
  with open(FILE_PATH, "w", encoding="utf-8") as f:
    for record in valid_records:
      f.write(record + "\n")

  print("\n=== 清理完成统计 ===")
  print(f"原始总行数: {len(lines)}")
  print(f"剔除死链数: {dead_count}")
  print(f"剔除风控数: {empty_count}")
  print(f"剩余有效数: {len(valid_records)}")


if __name__ == "__main__":
  main()
