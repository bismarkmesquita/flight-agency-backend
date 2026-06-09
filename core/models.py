from django.db import models
from datetime import datetime, date
from decimal import Decimal


class BaseModel(models.Model):
    """
    Serializes the model instance to a dictionary format, handling dates, decimals, and related objects.
    """
    class Meta:
        abstract = True

    def to_map(self):
        data = {}
        for field in self._meta.get_fields():
            name = field.name

            if field.auto_created and not field.concrete:
                continue

            try:
                value = getattr(self, name)
            except AttributeError:
                continue

            if value is None:
                data[name] = None
                continue

            # Relations
            if isinstance(field, (models.ForeignKey, models.OneToOneField)):
                data[name] = value.to_map() if hasattr(value, "to_map") else {"id": value.id}
                continue

            if isinstance(field, models.ManyToManyField):
                data[name] = [v.to_map() if hasattr(v, "to_map") else v.id for v in value.all()]
                continue

            # Special fields
            if isinstance(value, (datetime, date)):
                data[name] = value.isoformat()
            elif isinstance(value, Decimal):
                data[name] = float(value)
            else:
                data[name] = value

        return data
