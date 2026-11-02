import pytest

from emporio_agent.policies import load_policy_index, load_sections, search_policy, tokenize


@pytest.fixture(scope="module")
def index():
    return load_policy_index()


def test_tokenize_stems_and_drops_stopwords():
    assert tokenize("Me arrependi da compra, posso devolver?") == ["arrep", "compr", "posso", "devol"]
    assert tokenize("Devolução") == ["devol"]
    assert tokenize("") == []


def test_sections_are_split_by_heading():
    sections = load_sections()
    ids = [s.section_id for s in sections]
    assert "4.1" in ids and "7.1" in ids and "10" in ids
    assert len(sections) >= 25
    s41 = next(s for s in sections if s.section_id == "4.1")
    assert s41.title.startswith("Direito de Arrependimento")
    assert "7 (sete) dias corridos" in s41.text


def top_ids(index, query, k=3):
    return [r["section"] for r in search_policy(index, query, k)["results"]]


def test_withdrawal_question_finds_section_4_1(index):
    assert top_ids(index, "me arrependi da compra, posso devolver?")[0] == "4.1"


def test_hours_question_finds_section_2(index):
    assert top_ids(index, "qual o horário de funcionamento da loja?")[0] == "2"


def test_free_shipping_finds_section_5_1(index):
    assert top_ids(index, "frete grátis em Campo Grande")[0] == "5.1"


def test_pix_discount_with_promotion_finds_6_2(index):
    ids = top_ids(index, "desconto do pix acumula com promoção?")
    assert "6.2" in ids


def test_accessories_scope_finds_1_or_7_1(index):
    ids = top_ids(index, "vocês vendem cordas de violão?")
    assert ids[0] in ("1", "7.1")
    ids = top_ids(index, "tem amplificador?")
    assert "1" in ids or "7.1" in ids


def test_defect_warranty(index):
    ids = top_ids(index, "meu violão veio com defeito, qual a garantia?")
    assert "4.2" in ids or "8.1" in ids


def test_tracking_code(index):
    assert top_ids(index, "código de rastreamento do pedido")[0] == "5.3"


def test_no_match_returns_empty(index):
    out = search_policy(index, "receita de bolo de chocolate")
    assert out["results"] == [] or out["results"][0]["score"] < 2
