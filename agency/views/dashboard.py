from django.db.models import Sum, Count, F
from datetime import date, timedelta, datetime
from agency.models import Reservation, Sale
from core.views import BaseAPIView
from users.models import User


def get_date_range(request):
    period = request.GET.get("period")
    start = request.GET.get("start")
    end = request.GET.get("end")

    today = date.today()

    if start and end:
        try:
            start_date = datetime.strptime(start, "%Y-%m-%d").date()
            end_date = datetime.strptime(end, "%Y-%m-%d").date()
            return start_date, end_date
        except ValueError:
            pass

    if period == "7d":
        return today - timedelta(days=6), today

    if period == "30d":
        return today - timedelta(days=29), today

    if period == "month":
        return today.replace(day=1), today

    if period == "year":
        return today.replace(month=1, day=1), today

    return today - timedelta(days=6), today


class DashboardView(BaseAPIView):
    def get_base_queryset(self, request, start_date, end_date):
        query = Sale.objects.filter(
            sale_date__range=[start_date, end_date]
        )

        user = request.user

        if user.role in [User.Role.ADMIN, User.Role.MANAGER]:
            return query, "admin"

        if user.role == User.Role.SELLER:
            return query.filter(seller=user), "seller"

        return query.none(), "seller"

    def get_reservation_queryset(self, request, start_date, end_date):
        query = Reservation.objects.filter(
            sale__sale_date__range=[start_date, end_date]
        )

        user = request.user

        if user.role in [User.Role.ADMIN, User.Role.MANAGER]:
            return query

        if user.role == User.Role.SELLER:
            return query.filter(sale__seller=user)

        return query.none()

    def get_kpis(self, query, reservation_query, mode):
        aggregated = query.aggregate(
            total_sold=Sum("amount_received"),
            total_profit=Sum(F("amount_received") - F("cost")),
            total_sales=Count("id"),
        )

        total_sold = aggregated["total_sold"] or 0
        total_sales = aggregated["total_sales"] or 0

        avg_ticket = (
            total_sold / total_sales
        ) if total_sales else 0

        data = {
            "total_sold": total_sold,
            "total_sales": total_sales,
            "total_reservations": reservation_query.count(),
            "avg_ticket": float(avg_ticket)
        }

        if mode == "admin":
            data["total_profit"] = aggregated["total_profit"] or 0

        return data

    def get_charts(self, query, start_date, end_date, mode):
        annotations = {
            "sales": Sum("amount_received"),
        }

        if mode == "admin":
            annotations["profit"] = Sum(
                F("amount_received") - F("cost")
            )

        aggregated = (
            query
            .values("sale_date")
            .annotate(**annotations)
            .order_by("sale_date")
        )

        data_map = {
            item["sale_date"]: item
            for item in aggregated
        }

        delta = (end_date - start_date).days
        days = [start_date + timedelta(days=i) for i in range(delta + 1)]

        sales_chart = []
        profit_chart = []

        for d in days:
            item = data_map.get(d, {})
            sales_chart.append({
                "label": d.strftime("%Y-%m-%d"),
                "value": float(item.get("sales") or 0)
            })

            if mode == "admin":
                profit_chart.append({
                    "label": d.strftime("%Y-%m-%d"),
                    "value": float(item.get("profit") or 0)
                })

        data = {"sales": sales_chart}
        if mode == "admin":
            data["profit"] = profit_chart

        return data

    def get_tables(self, query, reservation_query, mode):
        if mode == "admin":
            sellers_query = (
                query.values("seller_id", "seller__name")
                .annotate(
                    total_value=Sum("amount_received"),
                    sales=Count("id"),
                )
                .order_by("-total_value")
            )

            reservations_by_seller = {
                row["sale__seller_id"]: row["reservations"]
                for row in (
                    reservation_query
                    .values("sale__seller_id")
                    .annotate(reservations=Count("id"))
                )
            }

            sellers = [
                {
                    "name": s["seller__name"],
                    "total": float(s["total_value"] or 0),
                    "sales": s["sales"],
                    "reservations": reservations_by_seller.get(s["seller_id"], 0),
                }
                for s in sellers_query
            ]

        customers = (
            query.values("customer_id", "customer__name")
            .annotate(
                total_value=Sum("amount_received"),
                sales=Count("id"),
            )
            .order_by("-total_value")
        )

        reservations_by_customer = {
            row["sale__customer_id"]: row["reservations"]
            for row in (
                reservation_query
                .values("sale__customer_id")
                .annotate(reservations=Count("id"))
            )
        }

        customers = [
            {
                "name": c["customer__name"],
                "total": float(c["total_value"] or 0),
                "sales": c["sales"],
                "reservations": reservations_by_customer.get(c["customer_id"], 0),
            }
            for c in customers
        ]

        data = {"customers": customers}
        if mode == "admin":
            data["sellers"] = sellers

        return data

    def get(self, request):
        start_date, end_date = get_date_range(request)

        query, mode = self.get_base_queryset(request, start_date, end_date)
        reservation_query = self.get_reservation_queryset(
            request,
            start_date,
            end_date
        )

        data = {
            "kpis": self.get_kpis(query, reservation_query, mode),
            "charts": self.get_charts(query, start_date, end_date, mode),
            "tables": self.get_tables(query, reservation_query, mode),
            "mode": mode,
        }

        return self.success_response(data=data)
