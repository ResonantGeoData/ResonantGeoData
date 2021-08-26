def non_unique_get_or_create(model, **kwargs):
    # We are assuming these are unique, but this isn't enforced
    query = model.objects.filter(**kwargs)
    if query.exists():
        return query.first()
    return model(**kwargs).save()
