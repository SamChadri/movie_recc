from celery import Celery
from flask import current_app

def make_celery(app_name=__name__):
    broker_uri = 'amqp://localhost'
    celery = Celery(app_name, backend=broker_uri, broker=broker_uri,)

    return celery

def init_celery(app, celery):
    celery.conf.update(app.config)
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask


