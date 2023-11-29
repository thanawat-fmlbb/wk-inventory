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

RESULT_TASK_NAME = "wk-irs.tasks.send_result"
result_collector = get_celery_app(4)


@app.task
def check_inventory(**kwargs):
    main_id = kwargs.get('main_id', None)
    item_id = kwargs.get('item_id', None)
    quantity = kwargs.get('quantity', None)
    item_check_created = False # keeps track if an item was created
    
    try:
        create_item_check(main_id=main_id, item_id=item_id, quantity=quantity)
        # if an error was raised, then item_check_created will still be False
        item_check_created = True

    except ValueError as e:
        # value error will only be raised if there is not enough stock
        # so this will happen before the item_check is created
        # thus no need to return item
        print(e)
    except Exception as e:
        print(e)
        if item_check_created:
            return_item(main_id=main_id)
        
        
    result_object = {
        "main_id": main_id,
        "success": False,
        "service_name": "inventory",
        "payload": kwargs,
    }
    result_collector.send_task(
        RESULT_TASK_NAME,
        kwargs=result_object,
        task_id=main_id
    )


@app.task
def rollback(**kwargs):
    main_id = kwargs.get('main_id', None)
    try:
        return_item(main_id=main_id)
        result_object = {
            "main_id": main_id,
            "success": False, # this is for triggering the rollback on the backend
            "service_name": "inventory",
            "payload": kwargs,
        }
        result_collector.send_task(
            RESULT_TASK_NAME,
            kwargs=result_object,
            task_id=main_id
        )
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


@app.task(bind=True)
def test(self, **kwargs):
    from time import sleep
    sleep(2)
    result_object = {
        "main_id": self.request.id,
        "success": True,
        "service_name": "inventory",
        "payload": kwargs,
    }

    result_collector.send_task(
        RESULT_TASK_NAME,
        kwargs=result_object,
        task_id=self.request.id
    )
    return result_object
