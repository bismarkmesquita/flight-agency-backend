from django.db.models import Q
from django.core.exceptions import ValidationError
from rest_framework import permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from agency.models import Customer
from agency.failures import CreateCustomerFailureReason
from core.utils import get_object_or_none
from utils.validators import validate_email


class CustomerMixin:
    def serializer(self, obj):
        return {
            "id": obj.id,
            "name": obj.name,
            "email": obj.email,
            "phone": obj.phone,
        }

    def validate_data(self, data, customer_id=None):
        required_fields = ["name", "email", "phone"]

        missing_fields = [
            field for field in required_fields
            if not data.get(field)
        ]

        if missing_fields:
            return None, Response({
                "success": False,
                "message": f"Required fields: {', '.join(missing_fields)}",
                "reason": CreateCustomerFailureReason.MISSING_FIELDS.value,
            })

        name = data["name"]
        email = data["email"]
        phone = data["phone"]

        try:
            validate_email(email)
        except ValidationError:
            return None, Response({
                "success": False,
                "message": "The email address is not in a valid format.",
                "reason": CreateCustomerFailureReason.INVALID_EMAIL.value,
            })

        existing = Customer.objects.filter(
            Q(email=email) | Q(phone=phone)
        )

        if customer_id:
            existing = existing.exclude(id=customer_id)

        if existing.exists():
            return None, Response({
                "success": False,
                "message": (
                    "A customer already exists with an email "
                    "address or phone number provided."
                ),
                "reason": CreateCustomerFailureReason.ALREADY_REGISTERED.value,
            })

        return {
            "name": name,
            "email": email,
            "phone": phone,
        }, None


class CustomersView(CustomerMixin, APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        customers = Customer.objects.all()
        data = [self.serializer(customer) for customer in customers]

        return Response({"success": True, "items": data})

    def post(self, request):
        data, error = self.validate_data(request.data)

        if error:
            return error

        customer = Customer.objects.create(**data)

        return Response({
            "success": True,
            "message": "Customer successfully registered.",
            "customer": self.serializer(customer),
        })


class CustomerView(CustomerMixin, APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get_customer(self, id):
        return get_object_or_none(Customer, id=id)

    def customer_not_found(self):
        return Response({
            "success": False,
            "message": "Customer not found.",
            "reason": CreateCustomerFailureReason.INVALID_CUSTOMER.value,
        })

    def get(self, request, id):
        customer = self.get_customer(id)

        if not customer:
            return self.customer_not_found()

        return Response({
            "success": True,
            "customer": self.serializer(customer),
        })

    def put(self, request, id):
        customer = self.get_customer(id)

        if not customer:
            return self.customer_not_found()

        data, error = self.validate_data(request.data, customer_id=id)
        if error:
            return error

        customer.name = data["name"]
        customer.email = data["email"]
        customer.phone = data["phone"]
        customer.save()

        return Response({
            "success": True,
            "message": "Customer updated successfully.",
            "customer": self.serializer(customer),
        })

    def delete(self, request, id):
        customer = self.get_customer(id)

        if not customer:
            return self.customer_not_found()

        customer.is_active = False
        customer.save()

        return Response({
            "success": True,
            "message": "Customer deleted successfully.",
        })
