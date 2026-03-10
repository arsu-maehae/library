"""
Middleware that reads the admin's chosen DBMS from the session and sets
the thread-local alias used by SessionDBRouter before every request.

Supported session values:
  'default'  → PostgreSQL  (also the fallback when nothing is set)
  'oracle'   → Oracle
"""

from library.db_router import set_db_alias

_VALID_ALIASES = {'default', 'oracle'}


class DBSelectorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only activate an alternative DB when an admin is authenticated.
        # Unauthenticated requests (login page, member pages) always use
        # the default PostgreSQL database so auth lookups never hit Oracle.
        if request.user.is_authenticated and request.user.is_superuser:
            alias = request.session.get('dbms', 'default')
            if alias not in _VALID_ALIASES:
                alias = 'default'
        else:
            alias = 'default'
        set_db_alias(alias)
        return self.get_response(request)
