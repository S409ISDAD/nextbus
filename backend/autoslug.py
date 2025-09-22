from sqlalchemy import Column, String, event, select
from slugify import slugify
from sqlalchemy.orm import Session


class AutoSlugMixin:
    """Mixin to automatically set up AutoSlug columns after mapping."""

    @classmethod
    def __declare_last__(cls):
        for name, col in cls.__dict__.items():
            if isinstance(col, AutoSlug):
                col.setup(cls, name)


class AutoSlug(Column):
    """
    SQLAlchemy Column that generates a unique slug automatically.

    Parameters:
        source: str or callable, field name or function/property that returns string to slugify
        max_length: int, max length of slug
        unique: bool, enforce uniqueness
    """

    inherit_cache = True

    def __init__(self, source, max_length=255, unique=True, **kwargs):
        super().__init__(String(max_length), unique=unique, **kwargs)
        if not callable(source) and not isinstance(source, str):
            raise TypeError("source must be a field name or a callable")
        self.source = source
        self.max_length = max_length
        self.unique = unique

    def setup(self, model_cls, attr_name):
        @event.listens_for(model_cls, "before_insert")
        def receive_before_insert(mapper, connection, target):
            value = self._get_source_value(target)
            if value:
                slug_value = self._generate_unique_slug(
                    target, value, model_cls, attr_name
                )
                setattr(target, attr_name, slug_value)

        @event.listens_for(model_cls, "before_update")
        def receive_before_update(mapper, connection, target):
            value = self._get_source_value(target)
            if value:
                slug_value = self._generate_unique_slug(
                    target, value, model_cls, attr_name
                )
                setattr(target, attr_name, slug_value)

    def _get_source_value(self, instance):
        if callable(self.source):
            return self.source(instance)
        else:
            return getattr(instance, self.source, None)

    def _generate_unique_slug(self, instance, value, model_cls, attr_name):
        base_slug = slugify(value)[: self.max_length]
        if not self.unique:
            return base_slug

        session = Session.object_session(instance)
        if session is None:
            return base_slug

        slug_candidate = base_slug
        suffix = 1

        while True:
            stmt = select(model_cls).where(
                getattr(model_cls, attr_name) == slug_candidate
            )
            if instance.__dict__.get("id") is not None:
                stmt = stmt.where(model_cls.id != instance.id)
            exists = session.execute(stmt).scalar()
            if not exists:
                break

            slug_candidate = f"{base_slug}-{suffix}"
            if len(slug_candidate) > self.max_length:
                slug_candidate = (
                    slug_candidate[: self.max_length - len(f"-{suffix}")] + f"-{suffix}"
                )
            suffix += 1

        return slug_candidate
