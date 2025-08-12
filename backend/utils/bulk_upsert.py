from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session


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

    stmt = insert(model).values(rows)

    # Build update mapping for on_conflict_do_update
    update_dict = {col: stmt.excluded[col] for col in update_cols}

    stmt = stmt.on_conflict_do_update(index_elements=conflict_cols, set_=update_dict)

    session.execute(stmt)
    session.commit()
