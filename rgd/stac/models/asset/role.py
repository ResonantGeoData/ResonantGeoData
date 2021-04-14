from django.db import models


class AssetRole(models.Model):
    """
    The `roles` field is used to describe the purpose of each asset.
    It is recommended to include one for every asset, to give users
    a sense of why they might want to make use of the asset. There
    are some emerging standards that enable clients to take particular
    action when they encounter particular roles, listed below. But
    implementors are encouraged to come up with their own terms to
    describe the role.
    """

    slug = models.SlugField[str, str]()
    description = models.TextField[str, str]()
