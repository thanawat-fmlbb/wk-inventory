import os

from celery import Celery
from dotenv import load_dotenv


def create_celery_app():
    load_dotenv()
    internal_app = Celery("inventory",
                          broker=f"redis://"
                                 f"{os.environ.get('REDIS_HOSTNAME', 'localhost')}"
                                 f":{os.environ.get('REDIS_PORT', '6381')}"
                                 f"/", # TODO: change channel
                          backend=f"redis://"
                                  f"{os.environ.get('REDIS_HOSTNAME', 'localhost')}"
                                  f":{os.environ.get('REDIS_PORT', '6381')}"
                                  f"/", # TODO: change channel
                          broker_connection_retry_on_startup=True)
    return internal_app


app = create_celery_app()

@app.task
def check_inventory(main_id: int, item_id: int, quantity: int):
    # when items are checked out, we need to update the stock
    load_dotenv()
    try:
        print("WIP")
    except Exception as e:
        print(e)
        return False

@app.task
def rollback(main_id: int):
    load_dotenv()
    try:
        print("WIP")
    except Exception as e:
        print(e)
        return False
