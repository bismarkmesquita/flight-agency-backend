from django.forms import ValidationError
from django.shortcuts import _get_queryset


def get_object_or_none(klass, *args, **kwargs):
    """
    Use get() to return an object, or None if the object does not exist.
    """
    queryset = _get_queryset(klass)
    try:
        return queryset.get(*args, **kwargs)
    except queryset.model.DoesNotExist:
        return None


def only_digits(value: str):
    if not value:
        return value
    return "".join(filter(str.isdigit, value))


def check_max_length(model, field_name, value):
    field = model._meta.get_field(field_name)
    max_len = field.max_length
    if value and len(value) > max_len:
        raise ValidationError(
            f"{field_name} exceeds the maximum size. ({max_len})."
        )
