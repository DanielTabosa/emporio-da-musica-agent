"""Light retrieval over the store policy manual.

The manual (data/politicas_da_loja.md) is split into one chunk per
section heading. Each chunk is scored with BM25, a classic lexical
ranking: a section scores high when it contains the query words, with
more weight for words that are rare across the manual and a small
penalty for very long sections.

BM25 is implemented here (about 20 lines) instead of importing a
library, because the library pulls numpy to rank 29 short sections.

Why not embeddings: the manual has 8 pages and a fixed vocabulary.
BM25 needs no API key, no model download, runs offline and is easy to
test. The trade-off is that it matches words, not meaning, so we use a
tiny prefix stemmer ('devolver' and 'devolução' both become 'devol').
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from .data import DEFAULT_DATA_DIR
from .tools import normalize

DEFAULT_POLICY_FILE = DEFAULT_DATA_DIR / "politicas_da_loja.md"
STEM_LENGTH = 5
DEFAULT_TOP_K = 3

STOPWORDS = {
    "a", "o", "as", "os", "um", "uma", "de", "do", "da", "dos", "das", "em",
    "no", "na", "nos", "nas", "e", "ou", "que", "com", "para", "por", "se",
    "ao", "aos", "é", "ser", "ter", "meu", "minha", "eu", "voce", "vocês",
    "me", "sobre", "pelo", "pela", "este", "esta", "isso", "como", "mais",
}


@dataclass(frozen=True)
class Section:
    section_id: str  # e.g. "4.1"
    title: str  # e.g. "Direito de Arrependimento (Compras Online)"
    text: str


def tokenize(text: str) -> list[str]:
    words = re.findall(r"[a-z0-9]+", normalize(text))
    return [w[:STEM_LENGTH] for w in words if w not in STOPWORDS]


_HEADING = re.compile(r"^(#{2,3})\s+(\d+(?:\.\d+)?)\.?\s+(.*)$")


def load_sections(path: Path | str = DEFAULT_POLICY_FILE) -> list[Section]:
    """Split the markdown manual into sections, one per '##' or '###' heading."""
    sections: list[Section] = []
    current: tuple[str, str] | None = None
    body: list[str] = []

    def flush() -> None:
        if current is not None:
            text = "\n".join(body).strip()
            if text:
                sections.append(Section(current[0], current[1], text))

    for line in Path(path).read_text(encoding="utf-8").splitlines():
        m = _HEADING.match(line)
        if m:
            flush()
            current = (m.group(2), m.group(3).strip())
            body = []
        elif current is not None:
            body.append(line)
    flush()
    return sections


class PolicyIndex:
    """BM25 (Okapi) over the manual sections.

    score(section, query) = sum over query terms of
        idf(term) * tf * (k1 + 1) / (tf + k1 * (1 - b + b * len / avg_len))

    tf is how many times the term appears in the section, idf grows for
    terms that appear in few sections, and the length part keeps long
    sections from winning only because they have more words.
    """

    K1 = 1.5
    B = 0.75

    def __init__(self, sections: list[Section]):
        if not sections:
            raise ValueError("policy manual has no sections")
        self.sections = sections
        self._docs = [Counter(tokenize(f"{s.title} {s.text}")) for s in sections]
        self._lengths = [sum(d.values()) for d in self._docs]
        self._avg_len = sum(self._lengths) / len(self._lengths)
        n = len(sections)
        df = Counter(term for d in self._docs for term in d)
        self._idf = {
            term: math.log((n - count + 0.5) / (count + 0.5) + 1)
            for term, count in df.items()
        }

    def _score(self, i: int, tokens: list[str]) -> float:
        doc, length = self._docs[i], self._lengths[i]
        norm = self.K1 * (1 - self.B + self.B * length / self._avg_len)
        total = 0.0
        for term in tokens:
            tf = doc.get(term, 0)
            if tf:
                total += self._idf[term] * tf * (self.K1 + 1) / (tf + norm)
        return total

    def search(self, query: str, k: int = DEFAULT_TOP_K) -> list[dict]:
        tokens = tokenize(query)
        if not tokens:
            return []
        scores = [self._score(i, tokens) for i in range(len(self.sections))]
        ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        results = []
        for i in ranked[:k]:
            if scores[i] <= 0:
                break
            s = self.sections[i]
            results.append(
                {
                    "section": s.section_id,
                    "title": s.title,
                    "text": s.text,
                    "score": round(float(scores[i]), 3),
                }
            )
        return results


def load_policy_index(path: Path | str = DEFAULT_POLICY_FILE) -> PolicyIndex:
    return PolicyIndex(load_sections(path))


def search_policy(index: PolicyIndex, query: str, k: int = DEFAULT_TOP_K) -> dict:
    """Tool entry point: top-k manual sections for a question."""
    results = index.search(query, k)
    note = (
        f"{len(results)} seção(ões) do manual encontrada(s)."
        if results
        else "Nenhuma seção do manual corresponde à pergunta."
    )
    return {"results": results, "note": note}
