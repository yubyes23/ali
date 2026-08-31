import time
import requests

# 示例数据源（截取部分）
data_list = [
    ("/🍑我的阿里分享/上瘾(2016)4KIQ全15集", "DmR2AyEMjbg", "root"),
    ("/🍑我的阿里分享/YYDSVIP电视剧", "dieULBdYP3D", "633c26e2666fd0e679a5455d92c66f9dd13c6d35"),
]


def check_link_exist(share_id):
  """第一轮：测试链接是否存在/失效"""
  url = f"https://api.aliyundrive.v2/adrive/v3/share_link/get_share_by_code?share_code={share_id}"
  try:
    # 实际请求时需要补全阿里云盘的 UA、Referer 等必要 Header
    response = requests.post(
        url, json={"share_code": share_id}, timeout=5
    ).json()
    if (
        "code" in response
        and response["code"] == "ShareLinkNotFound"
        or "NotFound" in str(response)
    ):
      return False  # 链接不存在
    return True
  except Exception:
    return False


def check_link_content(share_id, extraction_code=""):
  """第二轮：测试是否为空内容或被风控"""
  # 注：通常需要先获取 share_token 才能查看具体文件列表
  # 此处为逻辑抽象，实际可调用获取文件列表接口
  try:
    # 伪代码逻辑：请求文件列表
    # files = get_share_files(share_id, extraction_code)
    files = []  # 假设获取到的文件列表
    if not files:
      return False  # 内容为空或被风控和谐
    return True
  except Exception:
    return False


def main():
  normal_links = []
  dead_links = []
  empty_links = []

  print("=== 开始第一轮：检测链接存活状态 ===")
  for path, share_id, pwd in data_list:
    is_exist = check_link_exist(share_id)
    if not is_exist:
      print(f"[失效] 链接不存在: {path} ({share_id})")
      dead_links.append((path, share_id, pwd))
    else:
      # 第一轮通过，进入第二轮
      pwd_param = "" if pwd == "root" else pwd
      is_valid_content = check_link_content(share_id, pwd_param)

      if not is_valid_content:
        print(f"[空内容/风控] 链接已被删空: {path} ({share_id})")
        empty_links.append((path, share_id, pwd))
      else:
        print(f"[正常] 链接有效: {path} ({share_id})")
        normal_links.append((path, share_id, pwd))

    time.sleep(0.5)  # 控频防风控

  print("\n=== 清理完成统计 ===")
  print(f"总数: {len(data_list)}")
  print(f"有效正常链接: {len(normal_links)}")
  print(f"失效链接: {len(dead_links)}")
  print(f"风控空内容链接: {len(empty_links)}")


if __name__ == "__main__":
  main()
