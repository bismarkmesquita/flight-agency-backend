from core.tests import BaseTestCase


class DashboardTests(BaseTestCase):
    def setUp(self):
        super().setUp()

        self.url = "/agency/dashboard/"

    def test_dashboard_requires_authentication(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)

    def test_dashboard_admin_mode(self):
        response = self.client.get(self.url, headers=self.admin_token)

        data = response.data["data"]
        self.assertEqual(data["mode"], "admin")

        # KPIs
        kpis = data["kpis"]
        self.assertIn("total_sales", kpis)
        self.assertIn("total_sold", kpis)
        self.assertIn("avg_ticket", kpis)
        self.assertIn("total_profit", kpis)

        # Charts
        self.assertIn("sales", data["charts"])
        self.assertIn("profit", data["charts"])

        # Tables
        self.assertIn("customers", data["tables"])
        self.assertIn("sellers", data["tables"])

    def test_dashboard_seller_mode(self):
        response = self.client.get(self.url, headers=self.seller_token)

        data = response.data["data"]
        self.assertEqual(data["mode"], "seller")

        # KPIs
        kpis = data["kpis"]
        self.assertIn("total_sales", kpis)
        self.assertIn("total_sold", kpis)
        self.assertNotIn("total_profit", kpis)

        # Charts
        self.assertIn("sales", data["charts"])
        self.assertNotIn("profit", data["charts"])

        # Tables
        self.assertIn("customers", data["tables"])
        self.assertNotIn("sellers", data["tables"])
