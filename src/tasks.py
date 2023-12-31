import celery
from celery.exceptions import SoftTimeLimitExceeded
from opentelemetry import trace, propagate
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

from src.database.models import create_item_check, return_item, setup
from src import app, result_collector

RESULT_TASK_NAME = "wk-irs.tasks.send_result"


@app.task(
    soft_time_limit=30,
    time_limit=60,
    name='wk-inventory.tasks.check_inventory'
)
def check_inventory(**kwargs):
    celery.current_task.request.headers.get("traceparent")
    tracer = trace.get_tracer(__name__)
    ctx = propagate.extract(celery.current_task.request.headers)
    with tracer.start_as_current_span("check_inventory", context=ctx):
        main_id = kwargs.get('main_id', None)
        item_id = kwargs.get('item_id', None)
        quantity = int(kwargs.get('quantity', None))
        success = True
        try:
            create_item_check(main_id=main_id, item_id=item_id, quantity=quantity)
        except ValueError as e:
            # value error will only be raised if there is not enough stock
            # so this will happen before the item_check is created
            # thus no need to return item
            print(e)
            success = False
            kwargs["error"] = "out_of_stock"
        except SoftTimeLimitExceeded as e:
            print(e)
            success = False
            kwargs["error"] = "timeout"
            return_item(main_id=main_id)
        except Exception as e:
            print(e)
            success = False
            kwargs["error"] = str(e)
            return_item(main_id=main_id)

        carrier = {}
        TraceContextTextMapPropagator().inject(carrier)
        header = {"traceparent": carrier["traceparent"]}

        result_object = {
            "main_id": main_id,
            "success": success,
            "service_name": "inventory",
            "payload": kwargs,
        }
        result_collector.send_task(
            RESULT_TASK_NAME,
            kwargs=result_object,
            task_id=str(main_id),
            headers=header,
        )
        return success


@app.task(name='wk-inventory.tasks.rollback')
def rollback(**kwargs):
    celery.current_task.request.headers.get("traceparent")
    tracer = trace.get_tracer(__name__)
    ctx = propagate.extract(celery.current_task.request.headers)
    with tracer.start_as_current_span("rollback_inventory", context=ctx):
        main_id = kwargs.get('main_id', None)
        try:
            return_item(main_id=main_id)
        except Exception as e:
            print(e)
            return False

        carrier = {}
        TraceContextTextMapPropagator().inject(carrier)
        header = {"traceparent": carrier["traceparent"]}
        result_object = {
            "main_id": main_id,
            "success": False,  # this is for triggering the rollback on the backend
            "service_name": "inventory",
            "payload": kwargs,
        }
        result_collector.send_task(
            RESULT_TASK_NAME,
            kwargs=result_object,
            task_id=str(main_id),
            headers=header,
        )
        return True


@app.task(name='wk-inventory.tasks.setup')
def db_setup():
    try:
        setup()
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
        task_id=str(self.request.id)
    )
    return result_object
