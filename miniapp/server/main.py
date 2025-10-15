from fastapi import FastAPI, Header, HTTPException, Depends, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute
from pydantic import BaseModel, Field
import hmac, hashlib, urllib.parse, os, json, sqlite3
import psycopg2
from psycopg2.extras import DictCursor
from typing import Optional, List
from dotenv import load_dotenv

# ===================== env =====================
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
if not BOT_TOKEN:
    raise RuntimeError("Set BOT_TOKEN in .env")

DB_PATH = os.getenv("DB_PATH", "")
if not DB_PATH:
    DB_PATH = os.path.join(os.path.dirname(__file__), "app.db")

# ===================== app =====================
app = FastAPI()
print("BOT_TOKEN(last8) =", os.getenv("BOT_TOKEN","")[-8:])
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "https://myoladean.serveo.net",  # URL фронтенда, с которого приходит запрос
        "https://myola-api.serveo.net",   # URL бэкенда, на который приходит запрос
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# ===================== Telegram WebApp auth =====================
def verify_init_data(init_data: str) -> dict:
    print("--- DEBUG: VERIFYING SIGNATURE ---")
    print("TOKEN USED BY BACKEND (last 8 chars):", BOT_TOKEN[-8:])
    print("------------------------------------")
    data = dict(urllib.parse.parse_qsl(init_data, keep_blank_values=True))

    hash_ = data.pop('hash', None)
    if not hash_:
        raise HTTPException(401, "No hash")

    check_string = "\n".join(f"{k}={v}" for k, v in sorted(data.items()))
    secret = hashlib.sha256(BOT_TOKEN.encode()).digest()
    h = hmac.new(secret, check_string.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(h, hash_):
        raise HTTPException(401, "Bad signature")

    # user приходит JSON-строкой — распарсим
    if "user" in data:
        try:
            data["user"] = json.loads(data["user"])
        except Exception:
            pass
    return data

def get_user(initdata: str = Header(..., alias="X-Telegram-InitData")):
    return verify_init_data(initdata)

# ===================== DB helpers =====================
# --- Загружаем данные для подключения к БД из .env ---
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "")
DB_NAME = os.getenv("DB_NAME", "University")

# ===================== DB helpers =====================
def conn():
    try:
        # Создаем подключение к PostgreSQL
        c = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASS,
            dbname=DB_NAME,
            cursor_factory=DictCursor # Очень важно для получения данных в виде словарей
        )
        return c
    except psycopg2.OperationalError as e:
        print(f"!!! ОШИБКА ПОДКЛЮЧЕНИЯ К БАЗЕ ДАННЫХ: {e}")
        raise HTTPException(status_code=500, detail="DB connection error")

# Функция ensure_schema() нам больше не нужна, так как таблица уже существует
# ensure_schema()

# ===================== Models =====================
# Мы "обманем" Pydantic с помощью Field(alias=...), чтобы API использовал удобные имена (name),
# а код работал с реальными именами колонок из вашей БД (first_name).
class ProfileIn(BaseModel):
    first_name: Optional[str] = Field("", alias="name")
    last_name: Optional[str] = Field("", alias="surname")
    phone: Optional[str] = ""
    email: Optional[str] = ""
    department_name: Optional[str] = Field("", alias="department")
    student_group: Optional[str] = Field("", alias="group")
    course: Optional[str] = ""
    status: Optional[str] = ""
    lang: Optional[str] = "ua"

class ProfileOut(ProfileIn):
    tg_id: int

# ===================== API: base & profile =====================
@app.get("/api/ping")
def ping():
    return {"ok": True}

@app.get("/api/me")
def me(user=Depends(get_user)):
    return {"user": user}

@app.get("/api/profile", response_model=ProfileOut)
def get_profile(user=Depends(get_user)):
    tg_id = user["user"]["id"]
    db = conn()
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
        return dict(student)

@app.post("/api/profile", response_model=ProfileOut)
def save_profile(payload: ProfileIn, user=Depends(get_user)):
    tg_id = user["user"]["id"]
    data = payload.dict(by_alias=False) # by_alias=False, чтобы использовать имена полей модели (first_name)

    sql = """
        INSERT INTO students (tg_id, first_name, last_name, phone, email, department_name, student_group, course, status, lang)
        VALUES (
            %(tg_id)s, %(first_name)s, %(last_name)s, %(phone)s, %(email)s,
            %(department_name)s, %(student_group)s, %(course)s, %(status)s, %(lang)s
        )
        ON CONFLICT (tg_id) DO UPDATE SET
            first_name = EXCLUDED.first_name,
            last_name = EXCLUDED.last_name,
            phone = EXCLUDED.phone,
            email = EXCLUDED.email,
            department_name = EXCLUDED.department_name,
            student_group = EXCLUDED.student_group,
            course = EXCLUDED.course,
            status = EXCLUDED.status,
            lang = EXCLUDED.lang
        RETURNING *;
    """
    db = conn()
    with db.cursor() as cur:
        cur.execute(sql, {**data, "tg_id": tg_id})
        updated_student = cur.fetchone()
        db.commit()
        return dict(updated_student)

# ===================== API: schedule =====================
schedule_router = APIRouter()

class ScheduleItem(BaseModel):
    id: int
    subject: str
    teacher: str
    time: str
    room: str
    day: str   # "Понеділок", "Вівторок", ...

# временные данные — потом заменим на БД
SCHEDULE_DATA: List[ScheduleItem] = [
    ScheduleItem(id=1, subject="Математика", teacher="Іваненко", time="09:00 - 10:30", room="101", day="Понеділок"),
    ScheduleItem(id=2, subject="Фізика",    teacher="Петренко",  time="10:45 - 12:15", room="202", day="Понеділок"),
    ScheduleItem(id=3, subject="Англійська", teacher="Brown",    time="09:00 - 10:30", room="203", day="Вівторок"),
]

@schedule_router.get("/schedule")
def get_schedule():
    return {"data": [s.dict() for s in SCHEDULE_DATA]}

@schedule_router.get("/schedule/{day}")
def get_schedule_by_day(day: str):
    filtered = [s.dict() for s in SCHEDULE_DATA if s.day.lower() == day.lower()]
    if not filtered:
        raise HTTPException(status_code=404, detail="Розклад не знайдено на цей день")
    return {"data": filtered}

app.include_router(schedule_router, prefix="/api", tags=["schedule"])

# ===================== DEBUG: список маршрутов =====================
@app.on_event("startup")
async def _print_routes():
    print("\n=== ROUTES REGISTERED ===")
    for r in app.routes:
        if isinstance(r, APIRoute):
            print(f"{','.join(sorted(r.methods))} {r.path}")
    print("=== /ROUTES ===\n")

@app.get("/api/_routes")
def _routes():
    out = []
    for r in app.routes:
        if isinstance(r, APIRoute):
            out.append({"methods": sorted(r.methods), "path": r.path, "name": r.name})
    return out
