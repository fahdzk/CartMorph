"""Tests for the unified mapper."""

import pytest

from src.unify.mapper import (
    map_kroger_product,
    map_kroger_products,
    map_walmart_product,
    map_walmart_products,
    map_instacart_product,
    map_instacart_products,
    map_target_product,
    map_target_products,
)
from src.unify.models import Product


class TestMapKrogerProduct:
    def test_full_product(self, kroger_product_response):
        raw = kroger_product_response["data"][0]
        product = map_kroger_product(raw)
        assert isinstance(product, Product)
        assert product.name == "Kroger Brand Whole Milk Gallon - 128 Fl Oz"
        assert product.price == 3.99
        assert product.sku == "0001111041700"
        assert product.upc == "0001111041700"
        assert product.brand == "Kroger"
        assert product.image_url == "https://example.com/large.jpg"
        assert product.store_id == "kroger"
        assert product.store_name == "Kroger"

    def test_no_images(self, kroger_product_response):
        raw = kroger_product_response["data"][1]
        product = map_kroger_product(raw)
        assert product.image_url is None
        assert product.price == 3.79

    def test_products_list(self, kroger_product_response):
        products = map_kroger_products(kroger_product_response["data"])
        assert len(products) == 2
        assert all(isinstance(p, Product) for p in products)


class TestMapWalmartProduct:
    def test_full_product(self, walmart_product_response):
        raw = walmart_product_response["items"][0]
        product = map_walmart_product(raw)
        assert isinstance(product, Product)
        assert product.name == "Great Value Whole Milk, 1 Gallon"
        assert product.price == 3.68
        assert product.sku == "12345678"
        assert product.brand == "Great Value"
        assert product.image_url == "https://i5.walmartimages.com/milk.jpg"
        assert product.store_id == "walmart"

    def test_simple_price(self):
        raw = {"name": "Test", "price": 2.50, "sku": "999"}
        product = map_walmart_product(raw)
        assert product.price == 2.50

    def test_products_list(self, walmart_product_response):
        products = map_walmart_products(walmart_product_response["items"])
        assert len(products) == 1


class TestMapInstacartProduct:
    def test_full_product(self, instacart_product_response):
        raw = instacart_product_response["products"][0]
        product = map_instacart_product(raw)
        assert isinstance(product, Product)
        assert product.name == "Organic Valley Whole Milk, 64 fl oz"
        assert product.price == 4.59
        assert product.brand == "Organic Valley"
        assert product.store_id == "instacart"


class TestMapTargetProduct:
    def test_full_product(self, target_product_response):
        raw = target_product_response["search_response"]["items"]["Item"][0]
        product = map_target_product(raw)
        assert isinstance(product, Product)
        assert "Horizon" in product.name
        assert product.price == 4.99
        assert product.sku == "12345678"
        assert product.store_id == "target"
