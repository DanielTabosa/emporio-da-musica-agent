"""Tools the agent can call to look at the catalog.

Each function receives the Store and plain arguments, and returns plain
dicts and lists. The agent layer turns these into JSON for the model.
Prices, discounts and installments are computed by pricing.py; the model
only reads the numbers.
"""

from __future__ import annotations

import unicodedata

from .data import Product, Store
from .pricing import installments, quote

MAX_SEARCH_RESULTS = 10
MAX_ALTERNATIVES = 3

# Words a customer may use for each category id. Keys are normalized.
CATEGORY_ALIASES: dict[str, int] = {
    "guitarra": 1,
    "guitarras": 1,
    "baixo": 2,
    "baixos": 2,
    "contrabaixo": 2,
    "bateria": 3,
    "baterias": 3,
    "percussao": 3,
    "teclado": 4,
    "teclados": 4,
    "piano": 4,
    "pianos": 4,
    "sintetizador": 4,
    "violao": 5,
    "violoes": 5,
    "sopro": 6,
    "madeiras": 6,
    "metais": 7,
    "cordas orquestrais": 8,
    "violino": 8,
    "ukulele": 9,
    "ukuleles": 9,
}

STATUS_LABELS = {
    "active": "ativo",
    "discontinued": "descontinuado",
    "coming_soon": "em breve",
}


def normalize(text: str) -> str:
    """Lowercase and strip accents so 'Violão' == 'violao'."""
    text = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in text if not unicodedata.combining(c)).lower().strip()


def resolve_category(store: Store, text: str | int | None) -> int | None:
    """Turn a category id, name or common word into a category id."""
    if text is None or text == "":
        return None
    if isinstance(text, int) or str(text).isdigit():
        cid = int(text)
        return cid if cid in store.categories else None
    key = normalize(str(text))
    for cid, cat in store.categories.items():
        if normalize(cat.name) == key:
            return cid
    for alias, cid in CATEGORY_ALIASES.items():
        if alias in key or key in alias:
            return cid
    return None


def _availability(product: Product) -> str:
    if product.is_available:
        return "disponível"
    if product.status == "discontinued":
        return "descontinuado"
    if product.status == "coming_soon":
        return "em breve (ainda não está à venda)"
    return "sem estoque no momento"


def _summary(store: Store, product: Product) -> dict:
    """Short view used in search results."""
    promo = store.active_promotion(product.product_id)
    q = quote(product.price_brl, promo.discount_percent if promo else None)
    return {
        "product_id": product.product_id,
        "name": product.name,
        "category": store.categories[product.category_id].name,
        "list_price_brl": q.list_price,
        "promo_percent": q.promo_percent,
        "promo_price_brl": q.promo_price,
        "pix_price_brl": q.pix_price,
        "best_cash_price_brl": q.best_cash_price,
        "availability": _availability(product),
        "stock_quantity": product.stock_quantity,
    }


def search_products(
    store: Store,
    category: str | int | None = None,
    max_price: float | None = None,
    query: str | None = None,
    only_available: bool = True,
) -> dict:
    """Filter the catalog. Returns a dict with results and a note."""
    cid = resolve_category(store, category)
    if category and cid is None:
        return {
            "results": [],
            "note": f"Categoria '{category}' não encontrada. "
            f"Categorias: {', '.join(c.name for c in store.categories.values())}.",
        }

    q = normalize(query) if query else ""
    found: list[Product] = []
    for p in store.products.values():
        if cid is not None and p.category_id != cid:
            continue
        if max_price is not None and p.price_brl > max_price:
            continue
        if q and q not in normalize(p.name) and q not in normalize(p.description):
            continue
        if only_available and not p.is_available:
            continue
        found.append(p)

    found.sort(key=lambda p: p.price_brl)
    total = len(found)
    results = [_summary(store, p) for p in found[:MAX_SEARCH_RESULTS]]
    note = f"{total} produto(s) encontrado(s)."
    if total > MAX_SEARCH_RESULTS:
        note += f" Mostrando os {MAX_SEARCH_RESULTS} mais baratos."
    if total == 0 and cid in (6, 7, 8):
        note += " Esta categoria está no catálogo mas não tem produtos cadastrados no momento."
    return {"results": results, "note": note}


def _alternatives(store: Store, product: Product) -> list[dict]:
    """Available products of the same category, closest in price."""
    others = [
        p
        for p in store.products.values()
        if p.category_id == product.category_id
        and p.product_id != product.product_id
        and p.is_available
    ]
    others.sort(key=lambda p: abs(p.price_brl - product.price_brl))
    return [_summary(store, p) for p in others[:MAX_ALTERNATIVES]]


def _find_product(store: Store, name_or_id: str | int) -> list[Product]:
    if isinstance(name_or_id, int) or str(name_or_id).strip().isdigit():
        p = store.products.get(int(name_or_id))
        return [p] if p else []
    key = normalize(str(name_or_id))
    exact = [p for p in store.products.values() if normalize(p.name) == key]
    if exact:
        return exact
    return [p for p in store.products.values() if key in normalize(p.name)]


def product_details(store: Store, name_or_id: str | int) -> dict:
    """Full view of one product, with prices computed in code."""
    matches = _find_product(store, name_or_id)
    if not matches:
        return {"found": False, "note": f"Nenhum produto encontrado para '{name_or_id}'."}
    if len(matches) > 1:
        return {
            "found": False,
            "note": "Mais de um produto corresponde. Pergunte ao cliente qual ele quer.",
            "candidates": [
                {"product_id": p.product_id, "name": p.name} for p in matches
            ],
        }

    p = matches[0]
    promo = store.active_promotion(p.product_id)
    q = quote(p.price_brl, promo.discount_percent if promo else None)
    inst = installments(p.price_brl)
    result = {
        "found": True,
        "product_id": p.product_id,
        "name": p.name,
        "category": store.categories[p.category_id].name,
        "description": p.description,
        "specs": p.specs,
        "status": STATUS_LABELS.get(p.status, p.status),
        "availability": _availability(p),
        "stock_quantity": p.stock_quantity,
        "list_price_brl": q.list_price,
        "promotion": (
            {
                "description": promo.description,
                "discount_percent": promo.discount_percent,
                "promo_price_brl": q.promo_price,
            }
            if promo
            else None
        ),
        "pix_price_brl": q.pix_price,
        "best_cash_price_brl": q.best_cash_price,
        "best_cash_label": q.best_cash_label,
        "installments": {
            "max_installments": inst.max_installments,
            "installment_value_brl": inst.installment_value,
            "note": "sem juros no cartão de crédito, sobre o preço de tabela",
        },
    }
    if not p.is_available:
        result["alternatives"] = _alternatives(store, p)
    return result
