import pytest

from emporio_agent.data import load_store
from emporio_agent.tools import (
    normalize,
    product_details,
    resolve_category,
    search_products,
)


@pytest.fixture(scope="module")
def store():
    return load_store()


def test_normalize():
    assert normalize("Violão Clássico") == "violao classico"
    assert normalize("  GD20 ") == "gd20"


def test_resolve_category(store):
    assert resolve_category(store, "violão") == 5
    assert resolve_category(store, "violoes") == 5
    assert resolve_category(store, "Violões") == 5
    assert resolve_category(store, "ukulele") == 9
    assert resolve_category(store, 1) == 1
    assert resolve_category(store, "5") == 5
    assert resolve_category(store, "cordas orquestrais") == 8
    assert resolve_category(store, "bicicleta") is None
    assert resolve_category(store, None) is None


def test_search_guitars_under_1000(store):
    out = search_products(store, category="violão", max_price=1000)
    assert out["results"]
    for r in out["results"]:
        assert r["category"] == "Violões"
        assert r["list_price_brl"] <= 1000
        assert r["availability"] == "disponível"
    prices = [r["list_price_brl"] for r in out["results"]]
    assert prices == sorted(prices)
    assert len(out["results"]) <= 10


def test_search_hides_unavailable_by_default(store):
    ids = {r["product_id"] for r in search_products(store, query="Giannini GF-3D")["results"]}
    assert 96 not in ids
    ids = {
        r["product_id"]
        for r in search_products(store, query="Giannini GF-3D", only_available=False)["results"]
    }
    assert 96 in ids


def test_search_unknown_category(store):
    out = search_products(store, category="bicicleta")
    assert out["results"] == []
    assert "não encontrada" in out["note"]


def test_search_empty_category_note(store):
    out = search_products(store, category="violino")
    assert out["results"] == []
    assert "não tem produtos" in out["note"]


def test_details_takamine_gd20_without_promotion(store):
    d = product_details(store, "Takamine GD20")
    assert d["found"]
    assert d["name"] == "Takamine GD20 Dreadnought Natural"
    assert d["promotion"] is None
    assert d["pix_price_brl"] == round(d["list_price_brl"] * 0.95, 2)
    assert d["best_cash_price_brl"] == d["pix_price_brl"]
    assert d["installments"]["max_installments"] >= 1
    assert "alternatives" not in d


def test_details_ambiguous_name_returns_candidates(store):
    d = product_details(store, "Takamine")
    assert not d["found"]
    assert len(d["candidates"]) == 4


def test_details_not_found(store):
    d = product_details(store, "Stradivarius")
    assert not d["found"]
    assert "candidates" not in d


def test_details_with_active_promotion(store):
    d = product_details(store, 127)
    assert d["promotion"]["discount_percent"] == 10
    assert d["promotion"]["promo_price_brl"] == round(d["list_price_brl"] * 0.9, 2)
    assert d["best_cash_price_brl"] == d["promotion"]["promo_price_brl"]


def test_details_out_of_stock_suggests_alternatives(store):
    d = product_details(store, 96)
    assert d["availability"] == "sem estoque no momento"
    assert d["promotion"] is None  # its two promotions are expired
    alts = d["alternatives"]
    assert 1 <= len(alts) <= 3
    for a in alts:
        assert a["category"] == "Violões"
        assert a["availability"] == "disponível"
        assert a["product_id"] != 96


def test_details_discontinued_with_stock_is_not_available(store):
    d = product_details(store, "136")
    assert d["status"] == "descontinuado"
    assert d["availability"] == "descontinuado"
    assert d["stock_quantity"] == 13
    assert d["alternatives"]
