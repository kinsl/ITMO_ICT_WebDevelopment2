import uuid
from datetime import datetime
from time import sleep

from celery import Celery

app = Celery("celery_app", result_backend="redis://localhost:6379/0", broker="pyamqp://guest@localhost//")


@app.task
def celery_write_csv(user_id):
    sleep(20)
    csv_name = uuid.uuid4()
    with open(f"files/{csv_name}.csv", mode="w") as csv_file:
        content = f"{datetime.utcnow()}"
        csv_file.write(content)

    return {"user_id": user_id, "csv_name": str(csv_name)}
