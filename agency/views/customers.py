from django.db.models import Q
from django.core.exceptions import ValidationError
from agency.models import Customer
from agency.failures import CreateCustomerFailureReason
from core.views import BaseAPIView
from core.utils import get_object_or_none
from utils.validators import validate_email


class BaseCustomerView(BaseAPIView):
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
            return None, self.error_response(
                message=f"Required fields: {', '.join(missing_fields)}",
                reason=CreateCustomerFailureReason.MISSING_FIELDS.value,
            )

        name = data["name"]
        email = data["email"]
        phone = data["phone"]

        try:
            validate_email(email)
        except ValidationError:
            return None, self.error_response(
                message="The email address is not in a valid format.",
                reason=CreateCustomerFailureReason.INVALID_EMAIL.value,
            )

        existing = Customer.objects.filter(
            Q(email=email) | Q(phone=phone)
        )

        if customer_id:
            existing = existing.exclude(id=customer_id)

        if existing.exists():
            return None, self.error_response(
                message="A customer already exists with an email address or phone number provided.",
                reason=CreateCustomerFailureReason.ALREADY_REGISTERED.value,
            )

        return {
            "name": name,
            "email": email,
            "phone": phone,
        }, None


class CustomersView(BaseCustomerView):
    def get(self, request):
        customers = Customer.objects.all()
        data = [self.serializer(customer) for customer in customers]

        return self.success_response(data=data)

    def post(self, request):
        data, error = self.validate_data(request.data)

        if error:
            return error

        customer = Customer.objects.create(**data)

        return self.success_response(
            data=self.serializer(customer),
            message="Customer successfully registered.",
        )


class CustomerView(BaseCustomerView):
    def get_customer(self, id):
        return get_object_or_none(Customer, id=id)

    def customer_not_found(self):
        return self.error_response(
            message="Customer not found.",
            reason=CreateCustomerFailureReason.INVALID_CUSTOMER.value,
        )

    def get(self, request, id):
        customer = self.get_customer(id)

        if not customer:
            return self.customer_not_found()

        data = self.serializer(customer)

        return self.success_response(data=data)

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

        return self.success_response(
            data=self.serializer(customer),
            message="Customer successfully registered.",
        )

    def delete(self, request, id):
        customer = self.get_customer(id)

        if not customer:
            return self.customer_not_found()

        customer.is_active = False
        customer.save()

        return self.success_response(
            message="Customer deleted successfully.",
        )
