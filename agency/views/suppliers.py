from django.db.models import Q
from rest_framework import permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from agency.models import Supplier
from agency.failures import CreateSupplierFailureReason, SupplierFailureReason
from core.utils import get_object_or_none
from users.models import User
from users.permissions import HasRole


class SupplierMixin:
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

    def error_response(self, message, reason):
        return Response({
            "success": False,
            "message": message,
            "reason": reason,
        })

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
                f"Required fields: {', '.join(missing_fields)}",
                CreateSupplierFailureReason.MISSING_FIELDS.value,
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
                "A supplier already exists with the"
                "provided phone number or tax ID.",
                CreateSupplierFailureReason.ALREADY_REGISTERED.value,
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


class SuppliersView(SupplierMixin, APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        suppliers = Supplier.objects.all().order_by("name")
        data = [self.serializer(supplier) for supplier in suppliers]

        return Response({"success": True, "suppliers": data})


class CreateSupplierView(SupplierMixin, APIView):
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

        return Response({
            "success": True,
            "message": "Supplier successfully registered.",
            "supplier": self.serializer(supplier),
        })


class SupplierView(SupplierMixin, APIView):
    permission_classes = (HasRole,)
    ALLOWED_ROLES = [
        User.Role.ADMIN,
        User.Role.MANAGER,
    ]

    def get_supplier(self, id):
        return get_object_or_none(Supplier, id=id)

    def supplier_not_found(self):
        return self.error_response(
            "Supplier not found.",
            SupplierFailureReason.INVALID_SUPPLIER.value,
        )

    def get(self, request, id):
        supplier = self.get_supplier(id)

        if not supplier:
            return self.supplier_not_found()

        return Response({
            "success": True,
            "supplier": self.serializer(supplier),
        })

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

        return Response({
            "success": True,
            "message": "Supplier updated successfully.",
            "supplier": self.serializer(supplier),
        })

    def delete(self, request, id):
        supplier = self.get_supplier(id)

        if not supplier:
            return self.supplier_not_found()

        supplier.is_active = False
        supplier.save()

        return Response({
            "success": True,
            "message": "Supplier deleted successfully.",
        })
