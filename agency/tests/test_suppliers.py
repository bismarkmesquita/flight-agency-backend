from agency.failures import CreateSupplierFailureReason, SupplierFailureReason
from agency.models import Supplier
from core.tests import BaseTestCase


class GetSuppliersTests(BaseTestCase):
    def setUp(self):
        super().setUp()

    def test_get_suppliers_list(self):
        """try get suppliers list"""
        response = self.client.get(
            "/agency/suppliers/", headers=self.admin_token)

        self.assertTrue(response.data["success"])
        self.assertEqual(len(response.data["data"]), 1)

    def test_cannot_access_without_auth(self):
        """try accessing without authentication."""
        response = self.client.get("/agency/suppliers/")

        assert response.status_code == 401


class CreateSupplierTests(BaseTestCase):
    def setUp(self):
        super().setUp()

        self.data = {
            "name": "supplier",
            "tax_id": "15350946056",
            "phone": "83988887777",
            "country": "Brazil",
            "postal_code": "58000000",
            "neighborhood": "neighborhood",
            "city": "city",
            "state": "state",
            "address": "address",
            "address_number": "100",
            "complement": "",
        }

        self.url = "/agency/suppliers/create/"

    def test_create_without_auth(self):
        response = self.client.post(self.url, data=self.data)

        self.assertEqual(response.status_code, 401)

    def test_seller_cannot_create_supplier(self):
        response = self.client.post(
            self.url,
            data=self.data,
            headers=self.seller_token,
        )

        self.assertEqual(response.status_code, 403)

    def test_create_supplier_success(self):
        """Create supplier successfully."""

        response = self.client.post(
            self.url,
            data=self.data,
            headers=self.admin_token,
        )

        data = response.data

        self.assertTrue(data["success"])

        supplier = Supplier.objects.get(tax_id=self.data["tax_id"])
        self.assertEqual(supplier.id, data["data"]["id"])

    def test_missing_fields(self):
        """Create supplier without required fields."""

        data = {"name": "Mark"}
        response = self.client.post(
            self.url,
            data=data,
            headers=self.admin_token,
        )

        self.assertFalse(response.data["success"])
        self.assertEqual(
            response.data["reason"],
            CreateSupplierFailureReason.MISSING_FIELDS.value
        )
        self.assertIn("Required fields", response.data["message"])

    def test_existing_supplier(self):
        """Supplier already registered."""

        Supplier.objects.create(
            name="Marks",
            phone=self.data["phone"],
        )

        response = self.client.post(
            self.url,
            data=self.data,
            headers=self.admin_token,
        )

        data = response.data

        self.assertFalse(data["success"])
        self.assertEqual(
            data["reason"],
            CreateSupplierFailureReason.ALREADY_REGISTERED.value
        )
        self.assertIn("A supplier already exists", data["message"])


class GetSupplierTests(BaseTestCase):
    def get_url(self, supplier_id):
        return f"/agency/suppliers/{supplier_id}/"

    def test_get_supplier_success(self):
        response = self.client.get(
            self.get_url(self.supplier.id),
            headers=self.admin_token,
        )

        self.assertTrue(response.data["success"])
        self.assertEqual(
            response.data["data"]["id"],
            self.supplier.id,
        )

    def test_get_supplier_not_found(self):
        response = self.client.get(
            self.get_url(999),
            headers=self.admin_token,
        )

        self.assertFalse(response.data["success"])


class UpdateSupplierTests(BaseTestCase):
    def setUp(self):
        super().setUp()

        self.data = {
            "name": "Updated Supplier",
            "tax_id": "15350946056",
            "phone": "83988887777",
            "country": "Brazil",
            "postal_code": "58000000",
            "neighborhood": "neighborhood",
            "city": "city",
            "state": "state",
            "address": "address",
            "address_number": "100",
            "complement": "",
        }

    def get_url(self, supplier_id):
        return f"/agency/suppliers/{supplier_id}/"

    def test_update_without_auth(self):
        response = self.client.put(
            self.get_url(self.supplier.id),
            data=self.data,
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 401)

    def test_seller_cannot_update_supplier(self):
        response = self.client.put(
            self.get_url(self.supplier.id),
            data=self.data,
            headers=self.seller_token,
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 403)

    def test_update_supplier_success(self):
        """Update supplier successfully."""

        response = self.client.put(
            self.get_url(self.supplier.id),
            data=self.data,
            headers=self.admin_token,
            content_type="application/json",
        )

        self.assertTrue(response.data["success"])

        self.supplier.refresh_from_db()
        self.assertEqual(self.supplier.name, self.data["name"])
        self.assertEqual(self.supplier.phone, self.data["phone"])

    def test_update_supplier_not_found(self):
        """Trying to update a non-existing supplier."""

        response = self.client.put(
            self.get_url(999),
            data=self.data,
            headers=self.admin_token,
            content_type="application/json",
        )

        self.assertFalse(response.data["success"])
        self.assertEqual(
            response.data["reason"],
            SupplierFailureReason.INVALID_SUPPLIER.value,
        )

    def test_update_missing_fields(self):
        response = self.client.put(
            self.get_url(self.supplier.id),
            data={"name": "Updated"},
            headers=self.admin_token,
            content_type="application/json",
        )

        self.assertFalse(response.data["success"])
        self.assertEqual(
            response.data["reason"],
            CreateSupplierFailureReason.MISSING_FIELDS.value,
        )

    def test_tax_id_already_exists(self):
        Supplier.objects.create(
            name="Customer 2",
            tax_id="98765432100",
            phone="22222222222",
            country="Brazil",
            postal_code="58000000",
            neighborhood="neighborhood",
            city="city",
            state="state",
            address="address",
            address_number="100",
            complement="",
        )

        self.data["tax_id"] = "98765432100"

        response = self.client.put(
            self.get_url(self.supplier.id),
            data=self.data,
            headers=self.admin_token,
            content_type="application/json",
        )

        self.assertFalse(response.data["success"])
        self.assertEqual(
            response.data["reason"],
            CreateSupplierFailureReason.ALREADY_REGISTERED.value
        )

    def test_phone_already_exists(self):
        Supplier.objects.create(
            name="Customer 2",
            tax_id="98765432100",
            phone="22222222222",
            country="Brazil",
            postal_code="58000000",
            neighborhood="neighborhood",
            city="city",
            state="state",
            address="address",
            address_number="100",
            complement="",
        )

        self.data["phone"] = "22222222222"

        response = self.client.put(
            self.get_url(self.supplier.id),
            data=self.data,
            headers=self.admin_token,
            content_type="application/json",
        )

        self.assertFalse(response.data["success"])
        self.assertEqual(
            response.data["reason"],
            CreateSupplierFailureReason.ALREADY_REGISTERED.value
        )


class DeleteSupplierTests(BaseTestCase):
    def get_url(self, supplier_id):
        return f"/agency/suppliers/{supplier_id}/"

    def test_delete_supplier_success(self):
        response = self.client.delete(
            self.get_url(self.supplier.id),
            headers=self.admin_token,
        )

        self.assertTrue(response.data["success"])

        self.supplier.refresh_from_db()
        self.assertFalse(self.supplier.is_active)

    def test_delete_supplier_not_found(self):
        response = self.client.delete(
            self.get_url(999),
            headers=self.admin_token,
        )

        self.assertFalse(response.data["success"])
