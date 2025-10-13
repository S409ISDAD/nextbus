alembic upgrade head

python -m backend.tasks.import_holidays 

python -m backend.tasks.import_nptg

python -m backend.tasks.import_naptan --no_update 

python -m backend.commands.setup_datasources