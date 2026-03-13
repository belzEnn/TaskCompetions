from fastapi import FastAPI, Request, UploadFile, File, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from requests import request
from random import choice
from uuid import uuid4
from json import load
from os import makedirs
from pathlib import Path
from shutil import copyfileobj

app = FastAPI()
website = Jinja2Templates(directory="website")
UPLOAD_DIR = "uploads"

makedirs(UPLOAD_DIR, exist_ok=True)

with open("tasks.json", "r", encoding="utf-8") as f:
    data = load(f)

@app.get("/", response_class=HTMLResponse)
async def get_home(request: Request, response: Response):
    user_id = request.cookies.get("user_id")
    
    if not user_id:
        user_id = str(uuid4())
    
    task = choice(data["pool"])
    res = website.TemplateResponse("index.html", {
        "request": request,
        "task_id": task["id"],
        "task_name": task["name"],
        "points": task["points"]
    })

    response.set_cookie(key="user_id", value=user_id, max_age=31536000)
    return res