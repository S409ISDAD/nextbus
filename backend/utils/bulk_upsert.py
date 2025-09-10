from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session
from more_itertools import chunked


def bulk_upsert(
    session: Session,
    model,
    rows: list[dict],
    conflict_cols: list[str],
    update_cols: list[str],
):
    """
    Perform a bulk upsert into a PostgreSQL table using SQLAlchemy.

    Args:
        session (Session): Active SQLAlchemy session.
        model (Base): SQLAlchemy ORM model class.
        rows (list[dict]): List of dictionaries representing rows.
        conflict_cols (list[str]): Columns to check for conflicts.
        update_cols (list[str]): Columns to update on conflict.
    """
    if not rows:
        return

    all_columns = [col.name for col in model.__table__.columns if not col.computed]
    # exclude autoincrement
    pk_autoinc_cols = [
        col.name
        for col in model.__table__.columns
        if col.primary_key and col.autoincrement and col.name not in [*conflict_cols]
    ]
    normalized_rows = [
        {
            col: row.get(col)
            for col in all_columns
            if not (col in pk_autoinc_cols and col not in row)
        }
        for row in rows
    ]

    for batch in chunked(normalized_rows, 10000):
        stmt = insert(model).values(batch)
        stmt = stmt.on_conflict_do_update(
            index_elements=conflict_cols,
            set_={col: getattr(stmt.excluded, col) for col in update_cols},
        )
        session.execute(stmt)
    session.commit()
