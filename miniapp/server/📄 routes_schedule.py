from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

# Простая модель расписания
class ScheduleItem(BaseModel):
    id: int
    subject: str
    teacher: str
    time: str
    room: str
    day: str

# Пример временного хранилища (в будущем заменим на БД)
schedule_data = [
    ScheduleItem(id=1, subject="Математика", teacher="Іваненко", time="09:00 - 10:30", room="101", day="Понеділок"),
    ScheduleItem(id=2, subject="Фізика", teacher="Петренко", time="10:45 - 12:15", room="202", day="Понеділок"),
    ScheduleItem(id=3, subject="Англійська", teacher="Brown", time="09:00 - 10:30", room="203", day="Вівторок"),
]

@router.get("/schedule")
def get_schedule():
    return {"data": schedule_data}

@router.get("/schedule/{day}")
def get_schedule_by_day(day: str):
    filtered = [s for s in schedule_data if s.day.lower() == day.lower()]
    if not filtered:
        raise HTTPException(status_code=404, detail="Розклад не знайдено на цей день")
    return {"data": filtered}
