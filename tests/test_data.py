from datetime import date

import pytest

from emporio_agent.data import load_store, _specs


@pytest.fixture(scope="module")
def store():
    return load_store()


def test_counts(store):
    assert len(store.categories) == 9
    assert len(store.products) == 65
    assert len(store.customers) == 50
    assert len(store.orders) == 20
    assert len(store.promotions) == 25


def test_product_types_and_specs(store):
    p = store.products[81]
    assert p.name == "Yamaha C40 Nylon Natural"
    assert p.price_brl == 599.9
    assert p.stock_quantity == 12
    assert p.status == "active"
    assert p.specs["strings"] == "nylon"
    assert p.created_at == date(2021, 3, 15)


def test_specs_parse_handles_bad_input():
    assert _specs(None) == {}
    assert _specs("") == {}
    assert _specs("not json") == {}
    assert _specs("[1, 2]") == {}
    assert _specs('{"a": 1}') == {"a": 1}


def test_availability_rules(store):
    assert store.products[81].is_available
    # active but stock 0
    assert not store.products[96].is_available
    # discontinued, stock 0
    assert not store.products[113].is_available
    # discontinued but still has stock: must not be sold
    assert not store.products[136].is_available
    # coming_soon with stock: not for sale yet
    assert not store.products[130].is_available


def test_active_promotions(store):
    active_ids = {p.product_id for p in store.promotions if p.is_active}
    assert active_ids == {127, 121, 90, 94}
    assert store.active_promotion(127).discount_percent == 10
    assert store.active_promotion(81) is None
    # product 96 has two expired promotions and no active one
    assert store.active_promotion(96) is None


def test_orders_and_items(store):
    delivered = store.orders[1]
    assert delivered.status == "delivered"
    assert delivered.tracking_code == "BRAB1234567BR"
    assert delivered.estimated_delivery == date(2025, 10, 25)
    assert delivered.notes is None
    assert [i.product_id for i in delivered.items] == [93]

    confirmed = store.orders[9]
    assert confirmed.tracking_code is None
    assert confirmed.estimated_delivery is None

    cancelled = store.orders[17]
    assert cancelled.notes.startswith("Pedido cancelado")

    two_items = store.orders[15]
    assert sorted(i.product_id for i in two_items.items) == [82, 106]


def test_customer_email_is_normalized(store):
    assert store.customers[1].email == "lucas.mendes@jmail.com"
    assert store.customers[1].city == "Campo Grande"
