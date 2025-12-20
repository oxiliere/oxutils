from  django.db import connection


def cacheops_prefix(query):
    if connection.schema_name:
        return '%s:' % connection.schema_name
    return 'default:'
