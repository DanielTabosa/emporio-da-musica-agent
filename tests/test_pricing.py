from emporio_agent.pricing import (
    apply_discount,
    installments,
    metro_shipping,
    money,
    pix_price,
    quote,
)


def test_money_rounds_half_up():
    assert money(569.905) == 569.91
    assert money(0.125) == 0.13
    assert money(10) == 10.0


def test_pix_is_five_percent_off_list_price():
    assert pix_price(1000) == 950.0
    assert pix_price(599.9) == 569.91


def test_apply_discount():
    assert apply_discount(1000, 10) == 900.0
    assert apply_discount(849, 20) == 679.2


def test_quote_without_promotion():
    q = quote(1000)
    assert q.promo_price is None
    assert q.pix_price == 950.0
    assert q.best_cash_price == 950.0
    assert "PIX" in q.best_cash_label


def test_quote_with_promotion_bigger_than_pix():
    # promotion 20% beats PIX 5%; the two never stack (section 6.2)
    q = quote(1000, promo_percent=20)
    assert q.promo_price == 800.0
    assert q.pix_price == 950.0
    assert q.best_cash_price == 800.0
    assert "não acumula" in q.best_cash_label


def test_quote_with_promotion_smaller_than_pix():
    q = quote(1000, promo_percent=3)
    assert q.promo_price == 970.0
    assert q.best_cash_price == 950.0


def test_installments_tiers():
    # 12x of 100 = 1200 is the smallest amount that allows 12x
    assert installments(1200).max_installments == 12
    assert installments(1199.99).max_installments == 11
    # 7x needs 100 each: 700 ok, 699 falls to 6x (needs 80 each)
    assert installments(700).max_installments == 7
    assert installments(699).max_installments == 6
    # 4x needs 80 each: 320 ok, 319 falls to 3x (needs 50 each)
    assert installments(320).max_installments == 4
    assert installments(319).max_installments == 3
    # 2x needs 50 each
    assert installments(100).max_installments == 2
    assert installments(99).max_installments == 1
    assert installments(30).max_installments == 1


def test_installment_value_is_rounded():
    i = installments(1000)
    assert i.max_installments == 10
    assert i.installment_value == 100.0
    i = installments(599.9)
    assert i.max_installments == 6
    assert i.installment_value == 99.98


def test_metro_shipping_rules():
    assert metro_shipping(500.01).is_free
    assert metro_shipping(500.01).cost == 0.0
    # exactly R$500.00 is free (read in favor of the customer)
    assert metro_shipping(500).is_free
    assert not metro_shipping(499.99).is_free
    assert metro_shipping(499.99).cost == 35.0
    assert metro_shipping(10).deadline == "1 a 3 dias úteis"
