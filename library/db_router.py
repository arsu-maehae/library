"""
Thread-local database router.

- Auth/session/admin tables always stay on 'default' (PostgreSQL).
- All librarian & member model queries go to whichever alias the
  current admin chose at login ('default' = PostgreSQL, 'oracle' = Oracle).
  The alias is stored in thread-local storage and set by DBSelectorMiddleware
  on every request.
"""

import threading

_thread_local = threading.local()

# Apps whose tables must always live on the default (PostgreSQL) database.
_AUTH_APPS = {'auth', 'contenttypes', 'sessions', 'admin', 'authtoken'}

# Individual models (app_label, model_name) that must always use default
# even though their app_label is not in _AUTH_APPS.
# AdminProfile has a FK to auth.User so it can only live on PostgreSQL.
_DEFAULT_ONLY_MODELS = {('librarian', 'adminprofile')}


def set_db_alias(alias: str) -> None:
    _thread_local.alias = alias


def get_db_alias() -> str:
    return getattr(_thread_local, 'alias', 'default')


class SessionDBRouter:
    def _use_default(self, model):
        return (
            model._meta.app_label in _AUTH_APPS
            or (model._meta.app_label, model._meta.model_name) in _DEFAULT_ONLY_MODELS
        )

    def db_for_read(self, model, **hints):
        if self._use_default(model):
            return 'default'
        return get_db_alias()

    def db_for_write(self, model, **hints):
        if self._use_default(model):
            return 'default'
        return get_db_alias()

    def allow_relation(self, obj1, obj2, **hints):
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        # Auth/session tables only ever go on the default (PostgreSQL) DB.
        if app_label in _AUTH_APPS:
            return db == 'default'
        # Library app tables are mirrored on both databases so that
        # `migrate` creates them on PostgreSQL and
        # `migrate --database=oracle` creates them on Oracle.
        return True
