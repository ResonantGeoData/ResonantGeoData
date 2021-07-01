from functools import reduce

from django.db.models import Count

from .base import Image, ImageSet


def get_or_create_image_set(image_ids, defaults=None):
    """Get or create ImageSet containing provided Image IDs."""
    # Check if an ImageSet already exists containing all of these images
    q = ImageSet.objects.annotate(count=Count('images')).filter(count=len(image_ids))
    imsets = reduce(lambda p, id: q.filter(images=id), image_ids, q).values()
    if len(imsets) > 0:
        # Grab first, could be N-many
        imset = ImageSet.objects.get(id=imsets[0]['id'])
        return imset, False
    # Otherwise, create it
    if not defaults:
        defaults = {}
    imset = ImageSet(**defaults)
    imset.save()  # Have to save before adding to ManyToManyField
    images = Image.objects.filter(pk__in=image_ids).all()
    for image in images:
        imset.images.add(image)
    imset.save()
    return imset, True
