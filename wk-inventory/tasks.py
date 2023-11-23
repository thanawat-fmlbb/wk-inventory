import os

from celery import Celery
from dotenv import load_dotenv
from .models import create_item_check, create_items
from .utils import rollback_payment

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
    try:
        create_item_check(main_id=main_id, item_id=item_id, quantity=quantity)
    except Exception as e:
        print(e)
        return False


@app.task
def rollback(main_id: int):
    try:
        rollback_payment(main_id=main_id)
    except Exception as e:
        print(e)
        return False

@app.task
def add_thing(name:str, price:int, stock:int):
    try:
        create_items(name=name, price=price, stock=stock)
    except Exception as e:
        print(e)
        return False
