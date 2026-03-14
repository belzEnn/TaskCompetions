import json
import os
from random import choice
from uuid import uuid4
from fastapi import Cookie, FastAPI, Form, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

app = FastAPI()
website = Jinja2Templates(directory="website")

def load_users():
    if not os.path.exists("users.json"):
        return {}
    try:
        with open("users.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
            
    except (json.JSONDecodeError, FileNotFoundError):
        return {}

with open("tasks.json", "r", encoding="utf-8") as f:
    tasks_data = json.load(f)["pool"]

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, user_id: str = Cookie(None)):
    users = load_users()
    
    # 1. Якщо юзера немає в базі - показуємо повну форму (нік + кімната)
    if not user_id or user_id not in users:
        return website.TemplateResponse("index.html", {"request": request, "step": "register"})
    
    # 2. Якщо юзер є - показуємо тільки вхід в кімнату
    return website.TemplateResponse("index.html", {"request": request, "step": "join_room", "username": users[user_id]["username"]})

@app.post("/register")
async def register(username: str = Form(...), room_id: str = Form(...)):
    users = load_users()
    new_uuid = str(uuid4())
    users[new_uuid] = {"username": username, "room_id": room_id, "completed_tasks": []}
    
    with open("users.json", "w", encoding="utf-8") as f:
        json.dump(users, f, indent=4)
        
    # Створюємо редірект
    response = RedirectResponse(url="/game", status_code=303)
    # Встановлюємо куку прямо в цей об'єкт
    response.set_cookie(key="user_id", value=new_uuid, max_age=31536000)
    return response

@app.post("/login")
async def login(response: Response, username: str = Form(...)):
    users = load_users()
    new_uuid = str(uuid4())

    users[new_uuid] = {
        "username": username,
        "completed_tasks": []
    }
    
    with open("users.json", "w", encoding="utf-8") as f:
        json.dump(users, f, indent=4)
        
    res = RedirectResponse(url="/", status_code=303)
    res.set_cookie(key="user_id", value=new_uuid, max_age=31536000)
    return res
@app.post("/join")
async def join_room(request: Request, room_id: str = Form(...)):
    user_id = request.cookies.get("user_id")
    users = load_users()
    
    if user_id in users:
        users[user_id]["room_id"] = room_id
        with open("users.json", "w", encoding="utf-8") as f:
            json.dump(users, f, indent=4)
            
    return RedirectResponse(url="/", status_code=303)

@app.post("/change_room")
async def change_room(request: Request, room_id: str = Form(...)):
    user_id = request.cookies.get("user_id")
    users = load_users()
    
    if user_id in users:
        users[user_id]["room_id"] = room_id
        with open("users.json", "w", encoding="utf-8") as f:
            json.dump(users, f, indent=4)
            
    return RedirectResponse(url="/game", status_code=303)

@app.get("/game", response_class=HTMLResponse)
async def game_page(request: Request, user_id: str = Cookie(None)):
    users = load_users()
    if not user_id or user_id not in users:
        return RedirectResponse(url="/", status_code=303)
    
    user_data = users[user_id]
    
    # 1. Якщо у користувача немає активного завдання — призначаємо його
    if "active_task_id" not in user_data or user_data["active_task_id"] is None:
        available = [t for t in tasks_data if t["id"] not in user_data["completed_tasks"]]
        if available:
            user_data["active_task_id"] = choice(available)["id"]
            # Зберігаємо зміни в файл
            users[user_id] = user_data
            with open("users.json", "w", encoding="utf-8") as f:
                json.dump(users, f, indent=4)

    # 2. Отримуємо об'єкт завдання за ID
    current_task = next((t for t in tasks_data if t["id"] == user_data["active_task_id"]), None)
    
    # 3. Синхронізація: шукаємо суперника в тій же кімнаті
    room_id = user_data.get("room_id")
    opponent = None
    for uid, data in users.items():
        if uid != user_id and data.get("room_id") == room_id:
            # Знаходимо завдання суперника
            opp_task_id = data.get("active_task_id")
            opp_task = next((t for t in tasks_data if t["id"] == opp_task_id), None)
            
            opponent = {
                "name": data["username"],
                "task": opp_task
            }
            break

    return website.TemplateResponse("game.html", {
        "request": request,
        "username": user_data["username"],
        "user_task": current_task,
        "opponent": opponent or {"name": "Чекаємо гравця...", "task": None}
    })

@app.post("/task_complete/{task_id}")
async def complete_task(request: Request, task_id: int):
    user_id = request.cookies.get("user_id")
    users = load_users()
    
    if user_id in users:
        # Додаємо завдання у виконані
        users[user_id]["completed_tasks"].append(task_id)
        # Очищаємо активне завдання
        users[user_id]["active_task_id"] = None
        
        with open("users.json", "w", encoding="utf-8") as f:
            json.dump(users, f, indent=4)
    
    return RedirectResponse(url="/game", status_code=303)