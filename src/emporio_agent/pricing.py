"""Price, discount, installment and shipping rules from the store manual.

All money math lives here, in plain Python. The LLM never calculates
prices; it only reads the numbers these functions return.

Rules come from the policy manual (data/politicas_da_loja.pdf):
- Section 3: PIX gives 5% off the list price.
- Section 3.1: installments without interest. Up to 3x with no minimum
  (except installments below R$50), 4x to 6x with a R$80 minimum
  installment, 7x to 12x with a R$100 minimum installment.
  The table in section 3 says "12x, minimum installment R$100". We use
  the detailed rule from 3.1 and document the conflict in the README.
- Section 5.1: metro region of Campo Grande, free shipping above R$500,
  flat R$35 below that, 1 to 3 business days.
- Section 5.2: other cities use PAC, SEDEX or Jadlog. Price depends on
  the ZIP code and size, so the agent only informs deadlines.
- Section 6.2: promotions are not cumulative. The PIX discount does not
  apply on top of a promotional price.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

PIX_DISCOUNT_PERCENT = 5
METRO_FREE_SHIPPING_ABOVE = 500.0
METRO_SHIPPING_FEE = 35.0
METRO_SHIPPING_DEADLINE = "1 a 3 dias úteis"
MAX_INSTALLMENTS = 12

# (max_installments, minimum_installment_value)
INSTALLMENT_TIERS = (
    (3, 50.0),
    (6, 80.0),
    (12, 100.0),
)

OTHER_CITIES_CARRIERS = (
    {"name": "PAC (Correios)", "deadline": "5 a 12 dias úteis"},
    {"name": "SEDEX (Correios)", "deadline": "2 a 5 dias úteis"},
    {"name": "Jadlog", "deadline": "3 a 8 dias úteis"},
)


def money(value: float | Decimal) -> float:
    """Round to cents the way a cashier does (half up), return a float."""
    cents = Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return float(cents)


def apply_discount(price: float, percent: float) -> float:
    return money(Decimal(str(price)) * (Decimal(100) - Decimal(str(percent))) / 100)


def pix_price(list_price: float) -> float:
    return apply_discount(list_price, PIX_DISCOUNT_PERCENT)


@dataclass(frozen=True)
class Quote:
    list_price: float
    promo_percent: float | None
    promo_price: float | None
    pix_price: float
    best_cash_price: float
    best_cash_label: str


def quote(list_price: float, promo_percent: float | None = None) -> Quote:
    """Return every price the customer may hear, following section 6.2.

    With no promotion: PIX price is 5% off the list price.
    With a promotion: the customer gets the promotional price OR the PIX
    discount on the list price, whichever is lower. Never both.
    """
    pix = pix_price(list_price)
    if promo_percent is None:
        return Quote(
            list_price=list_price,
            promo_percent=None,
            promo_price=None,
            pix_price=pix,
            best_cash_price=pix,
            best_cash_label="PIX (5% de desconto sobre o preço de tabela)",
        )

    promo = apply_discount(list_price, promo_percent)
    if promo <= pix:
        best, label = promo, (
            f"preço promocional ({promo_percent:g}% de desconto, "
            "o desconto do PIX não acumula)"
        )
    else:
        best, label = pix, "PIX (5% sobre o preço de tabela, maior que a promoção)"
    return Quote(
        list_price=list_price,
        promo_percent=promo_percent,
        promo_price=promo,
        pix_price=pix,
        best_cash_price=best,
        best_cash_label=label,
    )


@dataclass(frozen=True)
class Installments:
    max_installments: int
    installment_value: float  # value of each installment at max_installments


def installments(amount: float) -> Installments:
    """Biggest number of interest-free installments allowed for the amount.

    1x is always allowed. For n >= 2 the installment value must respect
    the minimum of its tier in INSTALLMENT_TIERS.
    """
    best_n = 1
    for n in range(2, MAX_INSTALLMENTS + 1):
        minimum = next(m for limit, m in INSTALLMENT_TIERS if n <= limit)
        if amount / n >= minimum:
            best_n = n
    return Installments(
        max_installments=best_n,
        installment_value=money(Decimal(str(amount)) / best_n),
    )


@dataclass(frozen=True)
class MetroShipping:
    cost: float
    is_free: bool
    deadline: str


def metro_shipping(subtotal: float) -> MetroShipping:
    """Shipping inside the metro region of Campo Grande (section 5.1).

    'Above R$500' is read literally: exactly R$500.00 still pays the fee.
    """
    free = subtotal > METRO_FREE_SHIPPING_ABOVE
    return MetroShipping(
        cost=0.0 if free else METRO_SHIPPING_FEE,
        is_free=free,
        deadline=METRO_SHIPPING_DEADLINE,
    )
