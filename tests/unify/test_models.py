"""Tests for the unified models."""

from src.unify.models import Product, CartItem, Cart, StoreInfo


class TestProduct:
    def test_basic_creation(self):
        p = Product(name="Milk", price=3.99, store_name="Kroger")
        assert str(p) == "Milk  ($3.99)  [Kroger]"

    def test_no_price(self):
        p = Product(name="Unknown", store_name="Test")
        assert "price N/A" in str(p)


class TestCart:
    def test_add_item(self):
        cart = Cart(store_id="kroger", store_name="Kroger")
        p = Product(name="Milk", price=3.99, sku="123", store_id="kroger", store_name="Kroger")
        cart.add_item(p, quantity=2)
        assert len(cart.items) == 1
        assert cart.items[0].quantity == 2
        assert cart.total == 7.98

    def test_add_same_item_merges(self):
        cart = Cart(store_id="kroger", store_name="Kroger")
        p1 = Product(name="Milk", price=3.99, sku="123", store_id="kroger", store_name="Kroger")
        p2 = Product(name="Milk", price=3.99, sku="123", store_id="kroger", store_name="Kroger")
        cart.add_item(p1, quantity=1)
        cart.add_item(p2, quantity=3)
        assert len(cart.items) == 1
        assert cart.items[0].quantity == 4

    def test_total_unknown_price(self):
        cart = Cart(store_id="k", store_name="K")
        p = Product(name="Unknown", price=None, store_id="k", store_name="K")
        cart.add_item(p)
        assert cart.total is None  # if any item has no price, total is unknown

    def test_item_count(self):
        cart = Cart(store_id="k", store_name="K")
        p = Product(name="X", price=1.0, sku="1", store_id="k", store_name="K")
        cart.add_item(p, quantity=5)
        assert cart.item_count == 5


class TestStoreInfo:
    def test_creation(self):
        info = StoreInfo(
            store_id="kroger",
            name="Kroger",
            base_url="https://api.kroger.com/v1",
            auth_type="oauth2",
            enabled=True,
        )
        assert info.store_id == "kroger"
        assert info.enabled is True
