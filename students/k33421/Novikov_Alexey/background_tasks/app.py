import asyncio
import os
import uuid
from datetime import datetime
from time import sleep

from celery import current_app as celery_app
from fastapi import BackgroundTasks, FastAPI, HTTPException
from starlette.responses import FileResponse

from celery_app import celery_write_csv

app = FastAPI()


def simple_write_notification(email: str, message: str = "") -> None:
    with open("logs.log", mode="a") as email_file:
        content = f"{datetime.utcnow()} – notification for {email}: {message}\n"
        email_file.write(content)


async def heavy_async_write_notification(email: str, message: str = "") -> None:
    await asyncio.sleep(5)
    with open("logs.log", mode="a") as email_file:
        content = f"{datetime.utcnow()} – notification for {email}: {message}\n"
        email_file.write(content)


def heavy_sync_write_notification(email: str, message: str = "") -> None:
    sleep(5)
    with open("logs.log", mode="a") as email_file:
        content = f"{datetime.utcnow()} – notification for {email}: {message}\n"
        email_file.write(content)


def write_csv(csv_name: str) -> None:
    sleep(20)
    with open(f"files/{csv_name}.csv", mode="w") as csv_file:
        content = f"{datetime.utcnow()}"
        csv_file.write(content)


@app.post("/simple-send-notification/{email}")
async def simple_send_notification(email: str):
    simple_write_notification(email=email, message="Какое-то письмо")
    return {"message": "Уведомление отправлено"}


@app.post("/heavy-async-send-notification/{email}")
async def heavy_async_send_notification(email: str):
    await heavy_async_write_notification(email=email, message="Какое-то письмо")
    return {"message": "Уведомление отправлено"}


@app.post("/heavy-async-bg-send-notification/{email}")
async def heavy_async_bg_send_notification(email: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(heavy_async_write_notification, email=email, message="Какое-то письмо")
    return {"message": "Уведомление отправлено"}


@app.post("/heavy-sync-bg-send-notification/{email}")
async def heavy_sync_bg_send_notification(email: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(heavy_sync_write_notification, email=email, message="Какое-то письмо")
    return {"message": "Уведомление отправлено"}


@app.post("/csv/create")
async def create_csv(background_tasks: BackgroundTasks):
    csv_name = str(uuid.uuid4())
    background_tasks.add_task(write_csv, csv_name=csv_name)
    return {"csv_name": csv_name}


@app.get("/csv/check/{csv_name}")
async def check_csv(csv_name: str):
    if os.path.isfile(f"files/{csv_name}.csv"):
        status = "SUCCESS"
    else:
        status = "PENDING"

    return {"status": status}


@app.get("/csv/get/{csv_name}")
async def get_csv(csv_name: str):
    return FileResponse(f"files/{csv_name}.csv")


@app.post("/celery/csv/create/{user_id}")
async def celery_create_csv(user_id: int):
    task = celery_write_csv.delay(user_id)
    return {"task_id": task.id}


@app.get("/celery/csv/check/{task_id}/{user_id}")
async def celery_check_csv(task_id: str, user_id: int):
    task = celery_app.AsyncResult(task_id)
    status = task.status

    if status == "SUCCESS" and user_id != task.result.get("user_id"):
        status = "PROTECTED"

    return {"status": status}


@app.get("/celery/csv/get/{task_id}/{user_id}")
async def celery_get_csv(task_id: str, user_id: int):
    task = celery_app.AsyncResult(task_id)
    result = task.result

    if user_id != result.get("user_id"):
        raise HTTPException(status_code=403, detail="Доступ к файлу запрещён!")

    csv_name = result.get("csv_name")

    return FileResponse(f"files/{csv_name}.csv")
