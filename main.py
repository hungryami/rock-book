from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

import json
import os
import uvicorn


app = FastAPI()



# 静态文件
app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static"
)



class Light(BaseModel):

    id: int





# 首页

@app.get("/")
def index():

    return FileResponse(
        "rock_book/index.html"
    )





# 点亮接口

@app.post("/api/light")
def light(data: Light):


    target_id = data.id


    files = [

        "宠物大全.json",

        "战斗宠物.json",

        "新宠物.json",

        "宠物皮肤.json"

    ]


    result = []



    for file in files:


        path = os.path.join(
            "static",
            "json",
            file
        )


        if not os.path.exists(path):

            continue



        with open(
            path,
            "r",
            encoding="utf-8"
        ) as f:

            pets = json.load(f)



        changed = False

        for pet in pets:
            if int(pet.get("id", -1)) == target_id:
                old = pet.get("unknown", True)

                # 切换状态
                pet["unknown"] = not old

                changed = True

                result.append(
                    {
                        "file": file,
                        "name": pet.get("name"),
                        "old": old,
                        "new": pet["unknown"],
                    }
                )





        if changed:


            with open(
                path,
                "w",
                encoding="utf-8"
            ) as f:


                json.dump(

                    pets,

                    f,

                    ensure_ascii=False,

                    indent=4

                )



    return {

        "success": True,

        "id": target_id,

        "result": result

    }






# 查询单个宠物

@app.get("/api/pet/{id}")
def get_pet(id:int):


    result=[]


    files=[

        "宠物大全.json",

        "战斗宠物.json",

        "新宠物.json",

        "宠物皮肤.json"

    ]


    for file in files:


        path=f"static/json/{file}"


        if not os.path.exists(path):

            continue



        with open(
            path,
            "r",
            encoding="utf-8"
        ) as f:

            pets=json.load(f)



        for p in pets:


            if int(p.get("id",-1))==id:

                result.append(p)



    return result







if __name__ == "__main__":


    uvicorn.run(

        app,

        host="localhost",

        port=8000

    )