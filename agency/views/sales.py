from rest_framework.views import APIView
from rest_framework import permissions
from rest_framework.response import Response
from core.utils import get_object_or_none
from users.models import User
from agency.models import Customer, Sale
from agency.failures import CreateSaleFailureReason
from decimal import Decimal, InvalidOperation


class SaleMixin:
    def error_response(self, message, reason):
        return Response({
            "success": False,
            "message": message,
            "reason": reason,
        })

    def validate_data(self, request, data):
        required_fields = [
            "payment",
            "amount_received",
            "cost",
            "sale_date",
            "type",
            "customer_id",
        ]

        missing_fields = [
            field
            for field in required_fields
            if data.get(field) is None
        ]

        if missing_fields:
            return None, self.error_response(
                f"Campos obrigatórios: {', '.join(missing_fields)}",
                CreateSaleFailureReason.MISSING_FIELDS.value,
            )

        sale_type = data["type"]
        payment = data["payment"]
        sale_date = data["sale_date"]
        amount_received = data["amount_received"]
        cost = data["cost"]
        seller_id = data["seller_id"]
        customer_id = data["customer_id"]

        seller_id = data.get("seller_id")
        indication = data.get("indication")

        # Validade values
        try:
            amount_received = Decimal(str(amount_received))
            cost = Decimal(str(cost))
        except InvalidOperation:
            return None, self.error_response(
                "Invalid numeric values.",
                CreateSaleFailureReason.VALIDATION_ERROR.value,
            )

        if amount_received <= 0:
            return None, self.error_response(
                "Amount received must be greater than zero.",
                CreateSaleFailureReason.VALIDATION_ERROR.value,
            )

        if cost < 0:
            return None, self.error_response(
                "Cost cannot be negative.",
                CreateSaleFailureReason.VALIDATION_ERROR.value,
            )

        # Validade customer
        customer = get_object_or_none(Customer, id=customer_id)
        if not customer:
            return None, self.error_response(
                "Customer not found.",
                CreateSaleFailureReason.OBJECT_NOT_FOUND.value,
            )

        # Validade seller
        seller = request.user

        if request.user.role in [User.Role.ADMIN, User.Role.MANAGER]:
            if not seller_id:
                return None, self.error_response(
                    "A seller needs to be provided.",
                    CreateSaleFailureReason.MISSING_FIELDS.value,
                )

            seller = get_object_or_none(User, id=seller_id)

            if not seller:
                return None, self.error_response(
                    "Seller not found.",
                    CreateSaleFailureReason.OBJECT_NOT_FOUND.value,
                )

        return {
            "type": sale_type,
            "payment": payment,
            "sale_date": sale_date,
            "seller": seller,
            "customer": customer,
            "amount_received": amount_received,
            "cost": cost,
            "indication": indication,
        }, None


class SalesView(SaleMixin, APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        validated_data, error = self.validate_data(request, request.data)

        if error:
            return error

        sale = Sale.objects.create(**validated_data)

        return Response({
            "success": True,
            "message": "Sale successfully registered.",
            "sale_id": sale.id
        })
