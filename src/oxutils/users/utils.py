from django.contrib.auth import get_user_model


def update_user(oxid: str, data: dict):
    user = get_user_model().objects.get(oxi_id=oxid)
    changes = False
    if data:
        for key, value in data.items():
            if hasattr(user, key):
                setattr(user, key, value)
                changes = True
    if changes:
        user.save()

    return user
