import glob
import json
import os
import pandas as pd


def load_missing_pets(json_dir="static/json"):
    """读取 static/json/*.json 提取未拥有的宠物 (unknown != false)"""
    missing_map = {}
    pattern = os.path.join(json_dir, "*.json")

    for file_path in glob.glob(pattern):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            # unknown 不为 False 说明未拥有
                            if item.get("unknown") is not False:
                                pet_id = item.get("id")
                                pet_name = item.get("name")
                                if pet_id:
                                    missing_map[pet_id] = pet_name
        except Exception as e:
            print(f"⚠️ 读取图鉴文件 {file_path} 报错: {e}")

    return missing_map


def load_scene_pets(scene_json_path="static/roco_scene_pets_clean.json"):
    """读取已清洗的场景宠 JSON 数据"""
    scene_pets = {}

    if not os.path.exists(scene_json_path):
        print(f"❌ 找不到场景宠文件: {scene_json_path}")
        return scene_pets

    with open(scene_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 适配两种数据结构（不管是清洗后的单层结构，还是原始嵌套结构）
    pets_list = []
    if isinstance(data, list):
        # 如果外层是数组，判断里面是否是嵌套包
        if len(data) > 0 and isinstance(data[0], dict) and "data" in data[0]:
            for page in data:
                pets_list.extend(page.get("data", []))
        else:
            pets_list = data

    for pet in pets_list:
        # 兼容新旧字段名（"编号/技能ID" 或 "skill_pet_id"）
        skill_id = pet.get("编号/技能ID") or pet.get("skill_pet_id")
        name = pet.get("宠物名称") or pet.get("name", "未知")
        catch_way = pet.get("获取/捕获途径") or pet.get(
            "catch_way", "暂无说明"
        )
        recommend_character = pet.get("推荐性格") or pet.get(
            "recommend_character", "暂无"
        )
        recommend_recruit = pet.get("推荐配招") or pet.get(
            "recommend_recruit", "暂无"
        )
        total = pet.get("种族值和") or pet.get("total", 0)
        img_url = pet.get("图片链接") or pet.get("img_url", "")

        if skill_id and skill_id not in scene_pets:
            scene_pets[skill_id] = {
                "id": skill_id,
                "name": name,
                "catch_way": catch_way,
                "recommend_character": recommend_character,
                "recommend_recruit": recommend_recruit,
                "total": total,
                "img_url": img_url,
            }

    return scene_pets


def compare_and_generate():
    # 1. 获取未拥有列表
    missing_map = load_missing_pets("static/json")
    print(f"🔍 统计到图鉴未拥有宠物总数: {len(missing_map)} 只")

    # 2. 读取 static 目录下的场景宠数据
    scene_json = "static/roco_scene_pets_clean.json"
    scene_pets = load_scene_pets(scene_json)
    print(f"📍 统计到可捕捉场景宠总数: {len(scene_pets)} 只")

    # 3. 比对未拥有 && 场景可抓
    catchable_missing = []
    for pet_id, pet_name in missing_map.items():
        if pet_id in scene_pets:
            catchable_missing.append(scene_pets[pet_id])

    # 4. 排序
    catchable_missing.sort(key=lambda x: x["id"])

    print("\n" + "=" * 60)
    print(
        f"🎯 筛选完成！共有 【 {len(catchable_missing)} 】 只场景宠是你目前【未拥有】且【可以直接去捕捉】的！"
    )
    print("=" * 60 + "\n")

    # 打印前 15 只
    for pet in catchable_missing[:15]:
        print(
            f"📍 [ID: {pet['id']}] {pet['name']} | 地点: {pet['catch_way']}"
        )

    # 5. 保存结果
    df = pd.DataFrame(catchable_missing)
    if not df.empty:
        df.rename(
            columns={
                "id": "宠物ID",
                "name": "宠物名称",
                "catch_way": "捕捉地点/获取方式",
                "recommend_character": "推荐性格",
                "recommend_recruit": "推荐配招",
                "total": "种族值和",
                "img_url": "立绘图片",
            },
            inplace=True,
        )
        excel_path = "可捕捉的未拥有场景宠清单.xlsx"
        df.to_excel(excel_path, index=False, engine="openpyxl")
        print(f"\n📊 攻略表格已更新至: {os.path.abspath(excel_path)}")

    with open("catchable_missing.json", "w", encoding="utf-8") as f:
        json.dump(catchable_missing, f, ensure_ascii=False, indent=2)


# if __name__ == "__main__":
compare_and_generate()