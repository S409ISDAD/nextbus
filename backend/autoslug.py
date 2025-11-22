"""
Slug utils for SQLAlchemy models.

Original code from https://digitalhedgehog.org/articles/how-to-manage-slugs-for-database-entities-with-flask-and-sqlalchemy
Modified to fit nextbus models.
"""

from sqlalchemy import Column, String, event, select
from slugify import slugify
from sqlalchemy.orm import Session
import re
from backend.config import get_logger
from backend.db.db import SessionLocal

log = get_logger(__name__)


SLUG_MAX_LENGTH = 128


class SlugMixin:
    """Mixin to automatically set up AutoSlug columns after mapping."""

    slug_target_col = "slug"
    slug = Column(String, unique=True, nullable=True)


# @event.listens_for(SessionLocal, "before_commit")
# def update_before_commit(session: Session):
#     """Update slugs for all new and modified items before commit."""

#     new_items = [obj for obj in session.new if isinstance(obj, SlugMixin)]
#     dirty_items = [obj for obj in session.dirty if isinstance(obj, SlugMixin)]

#     all_items = new_items + dirty_items

#     update_slugs(session, all_items)


def update_all_slugs(session: Session):
    from backend.models import Service, Locality

    all_items = []
    for cls in [Service, Locality]:
        items = session.execute(select(cls)).scalars().all()
        session.query(cls).update({cls.slug: None})  # reset all slugs
        all_items.extend(items)

    session.flush()
    log.debug("reset slugs, now updating...")

    update_slugs(session, all_items)

    session.commit()


def update_slugs(session: Session, all_items: list[SlugMixin]):
    """update slugs for the given items."""

    log.debug(f"Updating slugs for {len(all_items)} items.")

    if all_items:
        slugs_map = {}

        for item in all_items:
            table = item.__table__

            if table not in slugs_map:
                slugs_map[table] = set(
                    c[0] for c in session.execute(select(table.c.slug)).all()
                )

            item_slug = str(item.slug or "")
            to_slugify = getattr(item, item.slug_target_col)

            if not to_slugify:
                log.warning(
                    f"Cannot generate slug for item {item} as source column '{item.slug_target_col}' is empty."
                )
                continue

            slug = slugify(to_slugify)[:SLUG_MAX_LENGTH]
            if not item_slug.startswith(slug):  # only update if changed
                base_slug = slug
                i = 1

                while slug in slugs_map[table]:
                    i += 1
                    slug_candidate = f"{base_slug}-{i}"
                    if len(slug_candidate) > SLUG_MAX_LENGTH:
                        slug_candidate = (
                            base_slug[: SLUG_MAX_LENGTH - len(f"-{i}")] + f"-{i}"
                        )
                    log.warning(
                        f"Slug '{slug}' already exists in table '{table.name}', trying '{slug_candidate}'"
                    )
                    slug = slug_candidate
                item.slug = slug
                slugs_map[table].add(slug)

    else:
        log.debug("No items to update slugs for.")


if __name__ == "__main__":
    from backend.config import setup_logging

    setup_logging()
    # event.remove(SessionLocal, "before_commit", update_before_commit)
    with SessionLocal() as db:
        log.info("Updating slugs for all models...")
        update_all_slugs(db)
    # event.listen(SessionLocal, "before_commit", update_before_commit)
