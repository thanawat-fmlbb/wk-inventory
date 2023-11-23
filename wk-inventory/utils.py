# will restructure the code after each service is done
from celery import Celery
import os

def rollback_payment(main_id: int):
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
    internal_app.send_task(
        "wk-payment.tasks.rollback",
        args=(main_id,),
        task_id=main_id # TODO: establish a convention for task_id
    )
