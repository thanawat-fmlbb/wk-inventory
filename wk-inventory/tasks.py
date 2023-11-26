import os

from celery import Celery
from dotenv import load_dotenv
from .models import create_db_and_tables, create_item_check, return_item, set_item_stock

def create_celery_app():
    load_dotenv()
    internal_app = Celery("inventory",
                          broker=f"redis://"
                                 f"{os.environ.get('REDIS_HOSTNAME', 'localhost')}"
                                 f":{os.environ.get('REDIS_PORT', '6379')}"
                                 f"/", # TODO: change channel
                          backend=f"redis://"
                                  f"{os.environ.get('REDIS_HOSTNAME', 'localhost')}"
                                  f":{os.environ.get('REDIS_PORT', '6379')}"
                                  f"/", # TODO: change channel
                          broker_connection_retry_on_startup=True)
    return internal_app

app = create_celery_app()
create_db_and_tables()

@app.task
def check_inventory(**kwargs):
    main_id = kwargs.get('main_id', None)
    item_id = kwargs.get('item_id', None)
    quantity = kwargs.get('quantity', None)

    # when items are checked out, we need to update the stock
    try:
        create_item_check(main_id=main_id, item_id=item_id, quantity=quantity)
    except Exception as e:
        print(e)
        return False


@app.task
def rollback(**kwargs):
    main_id = kwargs.get('main_id', None)
    try:
        return_item(main_id=main_id)
    except Exception as e:
        print(e)
        return False


@app.task
def create_item(**kwargs):
    item_id = kwargs.get('item_id', None)
    stock = kwargs.get('stock', None)

    try:
        set_item_stock(item_id=item_id, stock=stock)
    except Exception as e:
        print(e)
        return False
