from __future__ import annotations

from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self) -> None:
        # Work around Python 3.14 behavior changes around copying super()
        # objects which can break Django's template context copying and thus
        # the admin UI. Safe on older versions too.
        try:
            from django.template.context import BaseContext
        except Exception:
            return

        if getattr(BaseContext.__copy__, "_patched_for_py314", False):
            return

        def _basecontext_copy(self):  # type: ignore[no-redef]
            duplicate = self.__class__.__new__(self.__class__)
            try:
                duplicate.__dict__ = self.__dict__.copy()
            except Exception:
                for key, value in getattr(self, "__dict__", {}).items():
                    setattr(duplicate, key, value)
            if hasattr(self, "dicts"):
                duplicate.dicts = self.dicts[:]
            return duplicate

        _basecontext_copy._patched_for_py314 = True  # type: ignore[attr-defined]
        BaseContext.__copy__ = _basecontext_copy  # type: ignore[assignment]
