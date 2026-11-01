"""Load and type the store CSV files.

This module only reads the CSVs and converts the columns to the right
Python types. It does not change or "fix" the data. Business rules
(like "is this product available?") live in small properties here so
that the rest of the code uses one definition.
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

DEFAULT_DATA_DIR = Path(__file__).resolve().parents[2] / "data"


@dataclass(frozen=True)
class Category:
    category_id: int
    name: str
    description: str


@dataclass(frozen=True)
class Product:
    product_id: int
    name: str
    category_id: int
    description: str
    price_brl: float
    stock_quantity: int
    status: str  # active, discontinued, coming_soon
    specs: dict = field(default_factory=dict)
    created_at: date | None = None

    @property
    def is_available(self) -> bool:
        """A product can be sold only if it is active and has stock."""
        return self.status == "active" and self.stock_quantity > 0


@dataclass(frozen=True)
class Customer:
    customer_id: int
    name: str
    phone: str
    email: str
    city: str


@dataclass(frozen=True)
class OrderItem:
    order_id: int
    product_id: int
    quantity: int


@dataclass(frozen=True)
class Order:
    order_id: int
    customer_id: int
    order_date: date
    status: str  # pending, confirmed, shipped, delivered, cancelled
    total_brl: float
    payment_method: str
    tracking_code: str | None
    estimated_delivery: date | None
    notes: str | None
    items: tuple[OrderItem, ...] = ()


@dataclass(frozen=True)
class Promotion:
    promotion_id: int
    product_id: int
    discount_percent: float
    description: str
    is_active: bool


@dataclass
class Store:
    """All store data, indexed by id."""

    categories: dict[int, Category]
    products: dict[int, Product]
    customers: dict[int, Customer]
    orders: dict[int, Order]
    promotions: list[Promotion]

    def active_promotion(self, product_id: int) -> Promotion | None:
        """Return the active promotion for a product, or None.

        If the data ever has more than one active promotion for the same
        product, the biggest discount is used. We prefer this over raising
        an error because the agent must keep answering customers.
        """
        active = [
            p for p in self.promotions if p.product_id == product_id and p.is_active
        ]
        if not active:
            return None
        return max(active, key=lambda p: p.discount_percent)


# ---------------------------------------------------------------------------
# Small parsing helpers. Each one handles the "empty cell" case explicitly.
# ---------------------------------------------------------------------------


def _text(value: str | None) -> str | None:
    value = (value or "").strip()
    return value or None


def _date(value: str | None) -> date | None:
    value = _text(value)
    return date.fromisoformat(value) if value else None


def _specs(value: str | None) -> dict:
    """Parse the specs JSON string. Bad or empty JSON becomes an empty dict."""
    value = _text(value)
    if not value:
        return {}
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------


def load_store(data_dir: Path | str = DEFAULT_DATA_DIR) -> Store:
    data_dir = Path(data_dir)

    categories = {
        int(r["category_id"]): Category(
            category_id=int(r["category_id"]),
            name=r["name"].strip(),
            description=r["description"].strip(),
        )
        for r in _read_csv(data_dir / "categories.csv")
    }

    products = {
        int(r["product_id"]): Product(
            product_id=int(r["product_id"]),
            name=r["name"].strip(),
            category_id=int(r["category_id"]),
            description=r["description"].strip(),
            price_brl=float(r["price_brl"]),
            stock_quantity=int(r["stock_quantity"] or 0),
            status=r["status"].strip().lower(),
            specs=_specs(r["specs"]),
            created_at=_date(r.get("created_at")),
        )
        for r in _read_csv(data_dir / "products.csv")
    }

    customers = {
        int(r["customer_id"]): Customer(
            customer_id=int(r["customer_id"]),
            name=r["name"].strip(),
            phone=r["phone"].strip(),
            email=r["email"].strip().lower(),
            city=r["city"].strip(),
        )
        for r in _read_csv(data_dir / "customers.csv")
    }

    items_by_order: dict[int, list[OrderItem]] = {}
    for r in _read_csv(data_dir / "order_items.csv"):
        item = OrderItem(
            order_id=int(r["order_id"]),
            product_id=int(r["product_id"]),
            quantity=int(r["quantity"]),
        )
        items_by_order.setdefault(item.order_id, []).append(item)

    orders = {}
    for r in _read_csv(data_dir / "orders.csv"):
        order_id = int(r["order_id"])
        orders[order_id] = Order(
            order_id=order_id,
            customer_id=int(r["customer_id"]),
            order_date=date.fromisoformat(r["order_date"]),
            status=r["status"].strip().lower(),
            total_brl=float(r["total_brl"]),
            payment_method=r["payment_method"].strip().lower(),
            tracking_code=_text(r.get("tracking_code")),
            estimated_delivery=_date(r.get("estimated_delivery")),
            notes=_text(r.get("notes")),
            items=tuple(items_by_order.get(order_id, [])),
        )

    promotions = [
        Promotion(
            promotion_id=int(r["promotion_id"]),
            product_id=int(r["product_id"]),
            discount_percent=float(r["discount_percent"]),
            description=r["description"].strip(),
            is_active=r["is_active"].strip() == "1",
        )
        for r in _read_csv(data_dir / "promotions.csv")
    ]

    return Store(
        categories=categories,
        products=products,
        customers=customers,
        orders=orders,
        promotions=promotions,
    )
