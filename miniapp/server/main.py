import os
import hmac
import hashlib
import urllib.parse
import json
from contextlib import asynccontextmanager
from typing import Optional, List
import traceback

import psycopg2
from psycopg2.extras import DictCursor
from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Depends, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ===================== Загрузка переменных окружения =====================
load_dotenv()

# --- Токен Бота ---
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
if not BOT_TOKEN:
    raise RuntimeError("Set BOT_TOKEN in .env")

# --- Данные для подключения к БД ---
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "")
DB_NAME = os.getenv("DB_NAME", "")


# ===================== Приложение FastAPI =====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Этот код выполнится при старте сервера
    print("=== Application startup complete ===")
    yield
    # Этот код выполнится при остановке сервера
    print("=== Application shutdown complete ===")


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "https://myoladean.serveo.net",
        "https://my-miniapp.duckdns.org",
        "https://my-ola-api.onrender.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===================== Авторизация Telegram WebApp =====================

def verify_init_data(init_data: str) -> dict:
    """
    Проверяет данные авторизации из Telegram Web App.
    """
    try:
        data = dict(urllib.parse.parse_qsl(init_data, keep_blank_values=True))
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid initData format")

    if 'hash' not in data:
        raise HTTPException(status_code=401, detail="No hash in initData")

    hash_ = data.pop('hash')
    check_string = "\n".join(f"{k}={v}" for k, v in sorted(data.items()))

    # Правильная логика вычисления секретного ключа
    secret_key = hmac.new(key=b"WebAppData", msg=BOT_TOKEN.encode(), digestmod=hashlib.sha256).digest()
    h = hmac.new(key=secret_key, msg=check_string.encode(), digestmod=hashlib.sha256).hexdigest()

    if not hmac.compare_digest(h, hash_):
        raise HTTPException(status_code=401, detail="Bad signature")

    if "user" in data:
        try:
            data["user"] = json.loads(data["user"])
        except json.JSONDecodeError:
            raise HTTPException(status_code=401, detail="Invalid user data format")

    return data


def get_user(initdata: str = Header(..., alias="X-Telegram-InitData")):
    """
    Функция-зависимость для использования в эндпоинтах FastAPI.
    """
    return verify_init_data(initdata)


# ===================== Работа с базой данных =====================


def conn():
    try:
        # Создаем подключение к PostgreSQL
        c = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASS,
            dbname=DB_NAME,
            cursor_factory=DictCursor
        )
        return c
    except psycopg2.OperationalError as e:
        # --- РАСШИРЕННОЕ ЛОГИРОВАНИЕ ОШИБКИ ---
        print("!!! DETAILED DATABASE CONNECTION ERROR !!!")
        print(traceback.format_exc())
        print("-----------------------------------------")
        raise HTTPException(status_code=500, detail=f"DB connection error: {e}")


# ===================== Модели данных (Pydantic) =====================

class ProfileIn(BaseModel):
    first_name: Optional[str] = Field(None, alias="name")
    last_name: Optional[str] = Field(None, alias="surname")
    phone: Optional[str] = None
    email: Optional[str] = None
    department_name: Optional[str] = Field(None, alias="department")
    student_group: Optional[str] = Field(None, alias="group")
    course: Optional[str] = None
    status: Optional[str] = None
    lang: Optional[str] = None


class ProfileOut(ProfileIn):
    tg_id: int


class ScheduleItem(BaseModel):
    id: int
    subject: str
    teacher: Optional[str] = None
    time: str
    room: Optional[str] = None
    day: str
    course: Optional[int] = None
    grp: Optional[str] = None


# ===================== API эндпоинты =====================

api_router = APIRouter(prefix="/api")


@api_router.get("/ping")
def ping():
    return {"ok": True}


@api_router.get("/me")
def me(user: dict = Depends(get_user)):
    return {"user": user}


@api_router.get("/profile", response_model=ProfileOut)
def get_profile(user: dict = Depends(get_user)):
    tg_id = user["user"]["id"]
    db = conn()
    student = None
    with db.cursor() as cur:
        cur.execute("SELECT * FROM students WHERE tg_id = %s", (tg_id,))
        student = cur.fetchone()
        if not student:
            cur.execute(
                "INSERT INTO students (tg_id, first_name) VALUES (%s, %s) RETURNING *",
                (tg_id, user["user"].get("first_name", "user"))
            )
            student = cur.fetchone()
            db.commit()
    db.close()
    if student:
        return dict(student)  # <--- ГЛАВНОЕ ИСПРАВЛЕНИЕ ЗДЕСЬ
    raise HTTPException(status_code=404, detail="Student not found")


@api_router.post("/profile", response_model=ProfileOut)
def save_profile(payload: ProfileIn, user: dict = Depends(get_user)):
    tg_id = user["user"]["id"]
    data = payload.model_dump(by_alias=False)  # Используем .model_dump() вместо .dict()

    sql = """
        INSERT INTO students (tg_id, first_name, last_name, phone, email, department_name, student_group, course, status, lang)
        VALUES (
            %(tg_id)s, %(first_name)s, %(last_name)s, %(phone)s, %(email)s,
            %(department_name)s, %(student_group)s, %(course)s, %(status)s, %(lang)s
        )
        ON CONFLICT (tg_id) DO UPDATE SET
            first_name = EXCLUDED.first_name, last_name = EXCLUDED.last_name,
            phone = EXCLUDED.phone, email = EXCLUDED.email,
            department_name = EXCLUDED.department_name, student_group = EXCLUDED.student_group,
            course = EXCLUDED.course, status = EXCLUDED.status, lang = EXCLUDED.lang
        RETURNING *;
    """
    db = conn()
    with db.cursor() as cur:
        cur.execute(sql, {**data, "tg_id": tg_id})
        updated_student = cur.fetchone()
        db.commit()
    db.close()
    return updated_student

@api_router.get("/schedule", response_model=List[ScheduleItem])
def get_schedule(user: dict = Depends(get_user)):
    db = conn()
    schedule_data = []
    with db.cursor() as cur:
        cur.execute("SELECT * FROM schedule ORDER BY time")
        schedule_data = cur.fetchall()
    db.close()
    return [dict(row) for row in schedule_data]  # <--- И ГЛАВНОЕ ИСПРАВЛЕНИЕ ЗДЕСЬ


app.include_router(api_router)