from django.core.files.storage import storages, default_storage


def get_log_storage():
    try:
        return storages['logs']
    except:
        pass

    return default_storage
