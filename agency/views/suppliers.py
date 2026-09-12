from django.db.models import Q
from agency.models import Supplier
from agency.failures import CreateSupplierFailureReason, SupplierFailureReason
from core.views import BaseAPIView
from core.utils import get_object_or_none
from users.models import User
from users.permissions import HasRole


class BaseSupplierView(BaseAPIView):
    def serializer(self, obj):
        return {
            "id": obj.id,
            "name": obj.name,
            "tax_id": obj.tax_id,
            "phone": obj.phone,
            "country": obj.country,
            "postal_code": obj.postal_code,
            "city": obj.city,
            "state": obj.state,
            "neighborhood": obj.neighborhood,
            "address": obj.address,
            "address_number": obj.address_number,
            "complement": obj.complement
        }

    def validate_data(self, data, supplier_id=None):
        required_fields = [
            "name",
            "phone",
            "country",
            "postal_code",
            "city",
            "state",
            "neighborhood",
            "address",
            "address_number",
        ]

        missing_fields = [
            field
            for field in required_fields
            if data.get(field) is None
        ]

        if missing_fields:
            return None, self.error_response(
                message=f"Required fields: {', '.join(missing_fields)}",
                reason=CreateSupplierFailureReason.MISSING_FIELDS.value,
            )

        name = data["name"]
        phone = data["phone"]
        country = data["country"]
        postal_code = data["postal_code"]
        city = data["city"]
        state = data["state"]
        neighborhood = data["neighborhood"]
        address = data["address"]
        address_number = data["address_number"]

        tax_id = data.get("tax_id")
        complement = data.get("complement")

        filters = Q()
        if phone:
            filters |= Q(phone=phone)
        if tax_id:
            filters |= Q(tax_id=tax_id)

        existing = Supplier.objects.filter(filters)

        if supplier_id:
            existing = existing.exclude(id=supplier_id)

        if existing.exists():
            return None, self.error_response(
                message=(
                    "A supplier already exists with the "
                    "provided phone number or tax ID."
                ),
                reason=CreateSupplierFailureReason.ALREADY_REGISTERED.value,
            )

        return {
            "name": name,
            "tax_id": tax_id,
            "phone": phone,
            "country": country,
            "postal_code": postal_code,
            "city": city,
            "state": state,
            "neighborhood": neighborhood,
            "address": address,
            "address_number": address_number,
            "complement": complement
        }, None


class SuppliersView(BaseSupplierView):
    def get(self, request):
        suppliers = Supplier.objects.all().order_by("name")
        data = [self.serializer(supplier) for supplier in suppliers]

        return self.success_response(data=data)


class CreateSupplierView(BaseSupplierView):
    permission_classes = (HasRole,)
    ALLOWED_ROLES = [
        User.Role.ADMIN,
        User.Role.MANAGER,
    ]

    def post(self, request):
        validated_data, error = self.validate_data(request.data)

        if error:
            return error

        supplier = Supplier.objects.create(**validated_data)

        return self.success_response(
            data=self.serializer(supplier),
            message="Supplier successfully registered.",
        )


class SupplierView(BaseSupplierView):
    permission_classes = (HasRole,)
    ALLOWED_ROLES = [
        User.Role.ADMIN,
        User.Role.MANAGER,
    ]

    def get_supplier(self, id):
        return get_object_or_none(Supplier, id=id)

    def supplier_not_found(self):
        return self.error_response(
            message="Supplier not found.",
            reason=SupplierFailureReason.INVALID_SUPPLIER.value,
        )

    def get(self, request, id):
        supplier = self.get_supplier(id)

        if not supplier:
            return self.supplier_not_found()

        return self.success_response(data=self.serializer(supplier))

    def put(self, request, id):
        supplier = self.get_supplier(id)

        if not supplier:
            return self.supplier_not_found()

        data, error = self.validate_data(request.data, supplier_id=id)
        if error:
            return error

        for field, value in data.items():
            setattr(supplier, field, value)

        supplier.save()

        return self.success_response(
            data=self.serializer(supplier),
            message="Supplier updated successfully.",
        )

    def delete(self, request, id):
        supplier = self.get_supplier(id)

        if not supplier:
            return self.supplier_not_found()

        supplier.is_active = False
        supplier.save()

        return self.success_response(
            message="Supplier deleted successfully.",
        )
