import os

from celery import Celery
from dotenv import load_dotenv
from .models import create_db_and_tables, create_item_check, return_item, set_item_stock

load_dotenv()
REDIS_HOSTNAME = os.environ.get('REDIS_HOSTNAME', 'localhost')
REDIS_PORT = os.environ.get('REDIS_PORT', '6379')

def get_celery_app(channel_number: int):
    redis_url = f"redis://{REDIS_HOSTNAME}:{REDIS_PORT}/{channel_number}"
    return Celery(  "inventory",
                    broker=redis_url,
                    backend=redis_url,
                    broker_connection_retry_on_startup=True)

app = get_celery_app(2)
create_db_and_tables()

result_collector = get_celery_app(4)

@app.task(bind=True)
def test(self, **kwargs):
    from time import sleep
    sleep(5)
    print(kwargs)
    print(self.request.id)
    result_collector.send_task(
            "wk-irs.tasks.send_result",
            kwargs=kwargs,
            task_id=self.request.id
        )
    return {"msg": "hello, i got the stuff"}

@app.task
def check_inventory(**kwargs):
    main_id = kwargs.get('main_id', None)
    item_id = kwargs.get('item_id', None)
    quantity = kwargs.get('quantity', None)

    # when items are checked out, we need to update the stock
    try:
        create_item_check(main_id=main_id, item_id=item_id, quantity=quantity)
        result_collector.send_task(
            "wk-irs.tasks.send_result",
            kwargs=kwargs,
            task_id=main_id
        )
    except Exception as e:
        print(e)
        return False


@app.task
def rollback(**kwargs):
    main_id = kwargs.get('main_id', None)
    try:
        return_item(main_id=main_id)
        return {
            "main_id": main_id,
            "success": False, # this is for triggering the rollback on the backend
        }
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
