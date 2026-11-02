"""Run scripted scenarios against the real agent and save them as examples.

    uv run python scripts/run_examples.py           # all scenarios
    uv run python scripts/run_examples.py 1 4       # only scenarios 1 and 4

Each scenario is a list of customer messages. The agent's replies and
the tools it called are written to examples/NN-name.md. The agent's
"now" comes from EMPORIO_NOW (see .env.example), so the scenarios are
reproducible. Replies still vary a little between runs, as with any LLM.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from emporio_agent.agent import Agent
from emporio_agent.config import load_settings
from emporio_agent.data import load_store
from emporio_agent.policies import load_policy_index

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES_DIR = ROOT / "examples"

SCENARIOS = [
    {
        "slug": "catalog-and-price",
        "title": "Catalog search and price quote",
        "goal": "Product search with a budget filter, then a price quote with PIX and installments computed in code.",
        "messages": [
            "Oi! Quais violões vocês têm até 1000 reais?",
            "E quanto custa o Takamine GD20?",
        ],
    },
    {
        "slug": "store-info",
        "title": "Address and opening hours",
        "goal": "Store information from the store_status tool, including 'are you open now?' in the store timezone.",
        "messages": [
            "Qual o endereço da loja?",
            "Vocês estão abertos agora?",
            "E no sábado, até que horas?",
        ],
    },
    {
        "slug": "return-policy",
        "title": "Return policy (right of withdrawal)",
        "goal": "A policy question answered from the manual through retrieval, not from the model's memory.",
        "messages": [
            "Comprei um ukulele no site, chegou ontem, mas me arrependi. Posso devolver?",
            "E se eu quiser trocar por outro modelo em vez de devolver?",
        ],
    },
    {
        "slug": "order-status",
        "title": "Order status with identity check",
        "goal": "The agent asks for identification before showing an order. A wrong attempt is refused without leaking data, then the correct data works.",
        "messages": [
            "Quero saber o status do meu pedido 8",
            "Ana Ferreira, ana@gmail.com",
            "Desculpa, é Ana Carolina Ferreira, anacarol.ferreira@coldmail.com",
        ],
    },
    {
        "slug": "out-of-scope-and-stock",
        "title": "Out of scope requests and out-of-stock product",
        "goal": "Accessories and unrelated topics are declined politely; an out-of-stock product gets alternatives.",
        "messages": [
            "Vocês vendem cordas de violão? E aproveitando, me passa uma receita de bolo de cenoura",
            "Então me vê o violão Giannini GF-3D",
        ],
    },
]


def _short(result: dict, limit: int = 240) -> str:
    text = json.dumps(result, ensure_ascii=False)
    return text if len(text) <= limit else text[:limit] + "..."


def run_scenario(number: int, scenario: dict, settings, store, index) -> Path:
    calls: list[tuple[str, dict, dict]] = []
    agent = Agent(
        settings,
        store,
        index,
        on_tool=lambda name, args, result: calls.append((name, args, result)),
    )

    lines = [
        f"# Example {number:02d}: {scenario['title']}",
        "",
        f"Goal: {scenario['goal']}",
        "",
        f"Agent time (EMPORIO_NOW): {settings.now:%Y-%m-%d %H:%M} ({settings.now.tzname()}). Model: {settings.model}.",
        "",
    ]
    for message in scenario["messages"]:
        calls.clear()
        reply = agent.chat(message)
        lines += [f"**Customer:** {message}", ""]
        if calls:
            lines.append("<details><summary>Tool calls</summary>")
            lines.append("")
            for name, args, result in calls:
                lines.append(f"- `{name}({json.dumps(args, ensure_ascii=False)})`")
                lines.append(f"  - result: `{_short(result)}`")
            lines += ["", "</details>", ""]
        lines += ["**Empório:**", "", reply.strip(), "", "---", ""]

    path = EXAMPLES_DIR / f"{number:02d}-{scenario['slug']}.md"
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return path


def main(argv: list[str]) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    settings = load_settings()
    if not settings.api_key:
        print("ANTHROPIC_API_KEY not set. Copy .env.example to .env and add your key.")
        return 1
    store = load_store(settings.data_dir)
    index = load_policy_index(settings.data_dir / "politicas_da_loja.md")
    EXAMPLES_DIR.mkdir(exist_ok=True)

    wanted = {int(a) for a in argv} if argv else set(range(1, len(SCENARIOS) + 1))
    for number, scenario in enumerate(SCENARIOS, start=1):
        if number not in wanted:
            continue
        print(f"Running scenario {number}: {scenario['title']} ...")
        path = run_scenario(number, scenario, settings, store, index)
        print(f"  saved {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
