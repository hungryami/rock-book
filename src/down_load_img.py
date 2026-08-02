#!/usr/bin/env python3
import os
import json
import time
import requests

# 1. 路径定位
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_DIR = os.path.join(BASE_DIR, "../static/json")
IMG_DIR = os.path.join(BASE_DIR, "../static/img")

os.makedirs(IMG_DIR, exist_ok=True)

# 2. 读取并合并 JSON 数据
json_files = [f for f in os.listdir(JSON_DIR) if f.endswith(".json")]
pets_dict = {}

for file_name in json_files:
    file_path = os.path.join(JSON_DIR, file_name)
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                for pet in data:
                    if "id" in pet and "name" in pet:
                        pets_dict[pet["id"]] = pet
    except Exception as e:
        print(f"❌ 读取 {file_name} 失败: {e}")

print(f"📦 共汇总到 {len(pets_dict)} 只独立宠物，开始规范化下载图片...")

# 3. Headers 配置
headers = {
    "accept": "*/*",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-US;q=0.7",
    "cache-control": "no-cache",
    "pragma": "no-cache",
    "referer": "https://res.17roco.qq.com/h5/index.html",
    "sec-ch-ua": '"Not;A=Brand";v="8", "Chromium";v="150", "Microsoft Edge";v="150"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36 Edg/150.0.0.0",
}

session = requests.Session()
session.headers.update(headers)

# 4. 批量下载 & 强制统一命名为 {pet_id}.png
for pet_id, pet_data in pets_dict.items():
    pet_name = pet_data["name"]
    # 强制将保存文件名固定为: 997.png (去掉多余的杠)
    save_path = os.path.join(IMG_DIR, f"{pet_id}.png")

    # 如果正确名称的文件已存在，跳过
    if os.path.exists(save_path) and os.path.getsize(save_path) > 500:
        continue

    str_id = str(pet_id)
    padded_id = str_id.zfill(3)

    urls_to_try = [
        f"https://res.17roco.qq.com/res/combat/icons/{padded_id}-.png",
        f"https://res.17roco.qq.com/res/combat/icons/{padded_id}.png",
        f"https://res.17roco.qq.com/res/combat/icons/{str_id}-.png",
        f"https://res.17roco.qq.com/res/combat/icons/{str_id}.png",
        f"https://res.17roco.qq.com/h5/cdn/sprite-full-avatar/1/{str_id}-720.png",
        f"https://res.17roco.qq.com/h5/cdn/sprite-full-avatar/1/{str_id}.png",
    ]

    success = False
    for url in urls_to_try:
        try:
            res = session.get(url, timeout=5)
            if res.status_code == 200 and len(res.content) > 500:
                # 【核心修正】：统一写入 save_path ({pet_id}.png)
                with open(save_path, "wb") as f:
                    f.write(res.content)
                print(
                    f"✅ 下载并规范保存: [{pet_id}] {pet_name} -> static/img/{pet_id}.png"
                )
                success = True
                break
        except Exception:
            pass

    if not success:
        print(f"❌ 下载失败 (无匹配资源): [{pet_id}] {pet_name}")

    time.sleep(0.02)

print("\n🎉 图片重新整理完毕！请刷新 index.html 页面查看！")


