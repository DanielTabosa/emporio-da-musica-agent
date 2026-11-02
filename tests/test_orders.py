from datetime import datetime

import pytest

from emporio_agent.config import STORE_TZ
from emporio_agent.data import load_store
from emporio_agent.orders import NOT_VERIFIED, order_status, verify_customer

NOW = datetime(2026, 3, 16, 10, 0, tzinfo=STORE_TZ)


@pytest.fixture(scope="module")
def store():
    return load_store()


def test_verify_customer_name_and_email(store):
    c = store.customers[3]  # Pedro Henrique Oliveira
    assert verify_customer(c, "Pedro Henrique Oliveira", "pedro.oliveira@jmail.com")
    assert verify_customer(c, "  pedro henrique OLIVEIRA ", "PEDRO.OLIVEIRA@jmail.com")


def test_verify_customer_name_and_phone_any_format(store):
    c = store.customers[3]  # (67) 98432-1098
    assert verify_customer(c, "Pedro Henrique Oliveira", "67984321098")
    assert verify_customer(c, "Pedro Henrique Oliveira", "(67) 98432-1098")
    assert not verify_customer(c, "Pedro Henrique Oliveira", "")


def test_verify_customer_rejects_partial_name_or_wrong_contact(store):
    c = store.customers[3]
    assert not verify_customer(c, "Pedro", "pedro.oliveira@jmail.com")
    assert not verify_customer(c, "Pedro Henrique Oliveira", "outro@jmail.com")


def test_shared_email_is_not_enough(store):
    # customers 11 and 43 share bruno.martins@jmail.com; order 10 belongs to 11
    assert order_status(store, 10, "Bruno Martins", "bruno.martins@jmail.com", NOW) == NOT_VERIFIED
    ok = order_status(store, 10, "Bruno Carvalho Martins", "bruno.martins@jmail.com", NOW)
    assert ok["verified"]


def test_unknown_order_and_failed_check_give_same_message(store):
    missing = order_status(store, 999, "Pedro Henrique Oliveira", "pedro.oliveira@jmail.com", NOW)
    wrong = order_status(store, 1, "Pedro Henrique Oliveira", "x@y.com", NOW)
    bad_id = order_status(store, "abc", "Pedro Henrique Oliveira", "pedro.oliveira@jmail.com", NOW)
    assert missing == wrong == bad_id == NOT_VERIFIED
    assert "order_id" not in missing


def test_delivered_order_details(store):
    r = order_status(store, 1, "Pedro Henrique Oliveira", "pedro.oliveira@jmail.com", NOW)
    assert r["verified"]
    assert r["customer_first_name"] == "Pedro"
    assert r["status"] == "entregue"
    assert r["payment_method"] == "PIX"
    assert r["tracking_code"] == "BRAB1234567BR"
    assert r["estimated_delivery"] == "2025-10-25"
    assert r["items"] == [{"product_id": 93, "name": store.products[93].name, "quantity": 1}]
    w = r["withdrawal"]
    assert w["applies"] and w["deadline"] == "2025-11-01" and w["within_deadline"] is False


def test_withdrawal_within_deadline(store):
    soon = datetime(2025, 10, 30, 12, 0, tzinfo=STORE_TZ)
    r = order_status(store, 1, "Pedro Henrique Oliveira", "pedro.oliveira@jmail.com", soon)
    assert r["withdrawal"]["within_deadline"] is True


def test_confirmed_order_has_no_tracking(store):
    # order 9 belongs to customer 6
    c = store.customers[6]
    r = order_status(store, 9, c.name, c.email, NOW)
    assert r["status"].startswith("confirmado")
    assert r["tracking_code"] is None
    assert r["withdrawal"]["applies"] is False
    assert r["payment_method"] == "cartão de crédito em 6x"


def test_cancelled_order_keeps_note(store):
    c = store.customers[15]
    r = order_status(store, 17, c.name, c.phone, NOW)
    assert r["status"] == "cancelado"
    assert "cancelado pelo cliente" in r["notes"]
