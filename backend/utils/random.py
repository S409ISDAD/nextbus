from backend.db.db import SessionLocal
from backend.models import Stop
from backend.utils.time_taken import time_taken

with SessionLocal() as db:
    stop: Stop = db.query(Stop).filter(Stop.atco_code == "1900HA110081").first()
    print(f"Localities towards {stop.name}:")
    with time_taken():
        localities = stop.localities_towards()

    for locality in localities:
        print(locality.name)
