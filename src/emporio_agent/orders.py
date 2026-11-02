"""Order status with a simple identity check (manual section 9, LGPD).

Before showing anything about an order, the customer must give the full
name on the order AND the e-mail or phone on file. One field alone is not
enough: two customers in the dataset share the same e-mail.

When the check fails we return one generic message. We do not say which
field was wrong and we do not say whether the order exists.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta

from .data import Customer, Store
from .tools import normalize

WITHDRAWAL_DAYS = 7  # section 4.1: 7 calendar days after delivery

STATUS_LABELS = {
    "pending": "pendente (aguardando confirmação do pagamento)",
    "confirmed": "confirmado (em separação)",
    "shipped": "enviado",
    "delivered": "entregue",
    "cancelled": "cancelado",
}

PAYMENT_LABELS = {
    "pix": "PIX",
    "boleto": "boleto bancário",
    "debit": "cartão de débito",
}

NOT_VERIFIED = {
    "verified": False,
    "note": (
        "Não foi possível confirmar a identidade com os dados informados. "
        "Peça ao cliente o número do pedido, o nome completo e o e-mail ou "
        "telefone do cadastro. Não revele nenhum dado do pedido."
    ),
}


def _digits(value: str | None) -> str:
    return re.sub(r"\D", "", value or "")


def verify_customer(customer: Customer, full_name: str, contact: str) -> bool:
    name_ok = normalize(full_name) == normalize(customer.name)
    contact = (contact or "").strip()
    email_ok = normalize(contact) == normalize(customer.email)
    phone_ok = bool(_digits(contact)) and _digits(contact) == _digits(customer.phone)
    return name_ok and (email_ok or phone_ok)


def _payment_label(method: str) -> str:
    if method in PAYMENT_LABELS:
        return PAYMENT_LABELS[method]
    m = re.fullmatch(r"credit_(\d+)x", method)
    if m:
        return f"cartão de crédito em {m.group(1)}x"
    return method


def _withdrawal(order, now: datetime) -> dict:
    """Section 4.1 window, using estimated_delivery as the delivery date.

    The dataset has no real delivery date, so estimated_delivery is the
    best approximation we have. This is documented as an assumption.
    """
    if order.status != "delivered" or order.estimated_delivery is None:
        return {
            "applies": False,
            "note": "O prazo de arrependimento só começa a contar após o recebimento.",
        }
    deadline = order.estimated_delivery + timedelta(days=WITHDRAWAL_DAYS)
    within = now.date() <= deadline
    return {
        "applies": True,
        "assumed_delivery_date": order.estimated_delivery.isoformat(),
        "deadline": deadline.isoformat(),
        "within_deadline": within,
        "note": (
            "Dentro do prazo de 7 dias corridos para devolução por arrependimento."
            if within
            else "Prazo de 7 dias corridos para arrependimento já encerrado "
            "(contado a partir da data prevista de entrega)."
        ),
    }


def order_status(
    store: Store,
    order_id: int | str,
    full_name: str,
    contact: str,
    now: datetime,
) -> dict:
    try:
        order = store.orders.get(int(order_id))
    except (TypeError, ValueError):
        order = None
    if order is None:
        return dict(NOT_VERIFIED)

    customer = store.customers[order.customer_id]
    if not verify_customer(customer, full_name, contact):
        return dict(NOT_VERIFIED)

    items = [
        {
            "product_id": i.product_id,
            "name": store.products[i.product_id].name
            if i.product_id in store.products
            else f"produto {i.product_id}",
            "quantity": i.quantity,
        }
        for i in order.items
    ]
    return {
        "verified": True,
        "order_id": order.order_id,
        "customer_first_name": customer.name.split()[0],
        "status": STATUS_LABELS.get(order.status, order.status),
        "order_date": order.order_date.isoformat(),
        "payment_method": _payment_label(order.payment_method),
        "total_brl": order.total_brl,
        "items": items,
        "tracking_code": order.tracking_code,
        "estimated_delivery": (
            order.estimated_delivery.isoformat() if order.estimated_delivery else None
        ),
        "notes": order.notes,
        "withdrawal": _withdrawal(order, now),
    }
