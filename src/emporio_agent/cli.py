"""Terminal chat with the Empório da Música agent.

    uv run emporio            # start a new conversation
    uv run emporio --verbose  # also print each tool call
    uv run emporio --session 20260316-100000-ab12cd  # resume a saved session
"""

from __future__ import annotations

import argparse
import json
import sys

from .agent import Agent
from .config import load_settings
from .data import load_store
from .policies import load_policy_index


def _print_tool(name: str, args: dict, result: dict) -> None:
    short = json.dumps(result, ensure_ascii=False)
    if len(short) > 300:
        short = short[:300] + "..."
    print(f"  [tool] {name}({json.dumps(args, ensure_ascii=False)}) -> {short}")


def main(argv: list[str] | None = None) -> int:
    # Windows consoles may default to cp1252, which cannot print every character.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Chat with the Empório da Música agent.")
    parser.add_argument("--verbose", action="store_true", help="print tool calls")
    parser.add_argument("--session", help="resume a saved session id")
    args = parser.parse_args(argv)

    settings = load_settings()
    if not settings.api_key:
        print("ANTHROPIC_API_KEY not set. Copy .env.example to .env and add your key.")
        return 1

    agent = Agent(
        settings,
        load_store(settings.data_dir),
        load_policy_index(settings.data_dir / "politicas_da_loja.md"),
        on_tool=_print_tool if args.verbose else None,
    )
    if args.session:
        agent.load(args.session)
        for role, text in agent.transcript():
            print(f"{'Você' if role == 'user' else 'Empório'}: {text}\n")

    print(f"Empório da Música | modelo {settings.model} | agora: {settings.now:%d/%m/%Y %H:%M}")
    print("Digite sua mensagem. Comandos: /novo (nova conversa), /sair.\n")

    while True:
        try:
            text = input("Você: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not text:
            continue
        if text == "/sair":
            break
        if text == "/novo":
            agent = Agent(settings, agent.store, agent.policy_index, on_tool=agent.on_tool)
            print("(nova conversa)\n")
            continue
        reply = agent.chat(text)
        print(f"\nEmpório: {reply}\n")

    print(f"Conversa salva em sessions/{agent.session_id}.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
