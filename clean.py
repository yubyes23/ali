import os
import re
import time
import requests

# 配置文件路径
FILE_PATH = "ali_shares.txt"


def check_link_exist(share_id):
  """第一轮：调用阿里云盘 API 检测分享 ID 是否存活"""
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


def check_link_content(share_id):
  """第二轮：测试是否为空内容或被风控 (预留逻辑)"""
  try:
    return True
  except Exception:
    return False


def main():
  if not os.path.exists(FILE_PATH):
    print(
        f"[-] 找不到文件: {FILE_PATH}，请确认该文件与脚本在同一目录下。"
    )
    return

  lines = []
  # 自动兼容不同编码格式（utf-8 和 gbk）
  for encoding in ["utf-8", "gbk", "utf-16"]:
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

    # 忽略空行和注释行
    if not original_line or original_line.startswith("#"):
      continue

    # 按空格或 Tab 切分字段
    tokens = original_line.split()
    share_id = ""

    # 遍历所有分段，寻找带有 "数字:" 开头的项 (例如 0:5JnzcFFWa6Y)
    for token in tokens:
      if re.match(r"^\d+:[a-zA-Z0-9]+$", token):
        share_id = token.split(":")[-1]  # 剥离冒号前缀，只留纯分享码
        break
      elif re.match(r"^[a-zA-Z0-9]{11,14}$", token):
        share_id = token
        break

    # 兜底保险
    if not share_id and len(tokens) >= 2:
      candidate = tokens[1].replace("0:", "").replace("1:", "")
      if len(candidate) >= 6:
        share_id = candidate

    if not share_id or len(share_id) < 6:
      print(f"[跳过] 无法提取有效分享码: {original_line}")
      valid_records.append(original_line)
      skipped_count += 1
      continue

    # 4. 执行存活校验（用纯净的 share_id 请求）
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
    time.sleep(0.3)  # 控制请求频率防风控

  # 5. 写回原文件（保留原有的 0: 格式）
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
