import os
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

REDIS_HOSTNAME = os.environ.get('REDIS_HOSTNAME', 'localhost')
REDIS_PORT = os.environ.get('REDIS_PORT', '6379')

def get_celery_app(channel_number: int):
    redis_url = f"redis://{REDIS_HOSTNAME}:{REDIS_PORT}/{channel_number}"
    return Celery(  "inventory_service",
                    broker=redis_url,
                    backend=redis_url,
                    broker_connection_retry_on_startup=True)

app = get_celery_app(2)
result_collector = get_celery_app(4)

from .database.models import Thing, ItemCheck
from .database.engine import create_db_and_tables
create_db_and_tables()