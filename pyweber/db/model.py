"""Declarative model base for PyWeber apps."""

from __future__ import annotations


def _build_base():
    try:
        from sqlalchemy.orm import DeclarativeBase, declared_attr
    except ImportError as exc:
        raise ImportError(
            "Database support requires the 'db' extra. "
            "Install with: pip install 'pyweber[db]'"
        ) from exc

    class Model(DeclarativeBase):
        """SQLAlchemy declarative base used by PyWeber apps."""

        @declared_attr.directive
        def __tablename__(cls) -> str:  # type: ignore[misc]
            return cls.__name__.lower()

        def __repr__(self) -> str:
            pk = None
            try:
                mapper = self.__mapper__
                pk = tuple(getattr(self, c.key, None) for c in mapper.primary_key)
            except Exception:
                pass
            return f'<{self.__class__.__name__} pk={pk!r}>'

    return Model


try:
    Model = _build_base()
except ImportError:
    class Model:  # type: ignore[no-redef]
        """Placeholder when SQLAlchemy is not installed."""

        def __init_subclass__(cls, **kwargs):
            raise ImportError(
                "Database support requires the 'db' extra. "
                "Install with: pip install 'pyweber[db]'"
            )
