import json
import os
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

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, user_id: str = Cookie(None)):
    users = load_users()
    
    if user_id and user_id in users:
        return website.TemplateResponse("index.html", {
            "request": request,
            "username": users[user_id]
        })
    else:
        return website.TemplateResponse("home.html", {"request": request})

@app.post("/login")
async def login(response: Response, username: str = Form(...)):
    users = load_users()
    
    new_uuid = str(uuid4())
    users[new_uuid] = username
    
    with open("users.json", "w", encoding="utf-8") as f:
        json.dump(users, f, indent=4)
        
    res = RedirectResponse(url="/", status_code=303)
    res.set_cookie(key="user_id", value=new_uuid, max_age=31536000)
    return res



@app.post("/login")
async def login(response: Response, username: str = Form(...)):
    users = load_users()
    
    new_uuid = str(uuid4())
    users[new_uuid] = username
    
    with open("users.json", "w", encoding="utf-8") as f:
        json.dump(users, f, indent=4)
        
    res = RedirectResponse(url="/", status_code=303)
    res.set_cookie(key="user_id", value=new_uuid, max_age=31536000)
    return res