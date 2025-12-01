from sqlalchemy import event
from backend.models import Stop


@event.listens_for(Stop, "before_insert")
def before_insert_stop(mapper, connection, target):
    target.search_name = target.compute_search_name()


@event.listens_for(Stop, "before_update")
def before_update_stop(mapper, connection, target):
    target.search_name = target.compute_search_name()
