# Empório da Música Agent

A text messaging agent for Empório da Música, a fictional musical instrument store in Campo Grande, Brazil. It answers customers in Portuguese, looks up products, prices, promotions and orders in the store data, and applies the store policies from the internal manual.

Built in Python for the Artefact AI Engineer technical case. Five example conversations are in [examples/](examples/).

## Quick start

Requirements: Python 3.11 or newer, [uv](https://docs.astral.sh/uv/) and an Anthropic API key.

```bash
git clone https://github.com/DanielTabosa/emporio-da-musica-agent.git
cd emporio-da-musica-agent
cp .env.example .env        # then put your ANTHROPIC_API_KEY in .env
uv sync
uv run emporio --verbose    # chat in the terminal, --verbose shows the tool calls
```

Other commands:

```bash
uv run pytest                              # 61 tests, no API key needed
uv run python scripts/run_examples.py      # regenerate examples/ with the real API
uv run emporio --session <id>              # resume a conversation saved in sessions/
```

Settings live in `.env` (see `.env.example`):

| Variable | Default | What it does |
|---|---|---|
| `ANTHROPIC_API_KEY` | none | Your key. Never commit `.env`. |
| `EMPORIO_MODEL` | `claude-sonnet-5-5` | Model used by the agent. |
| `EMPORIO_NOW` | `2026-03-16 10:00` | The agent's "now", in the store timezone. Leave empty to use the real clock. |

## How it works

```
terminal (cli.py)
   |
   v
Agent loop (agent.py)  <-->  Claude (Anthropic API, native tool calling)
   |
   | calls one of five tools
   v
search_products, product_details   -> tools.py   -> data.py (CSV) + pricing.py
order_status                       -> orders.py  -> data.py
store_status                       -> store_info.py (hours, address, timezone)
search_policy                      -> policies.py (BM25 over the manual sections)
```

The flow of one message:

1. The customer message is added to the conversation history.
2. The history, the system prompt (persona and rules) and the five tool definitions are sent to Claude.
3. If Claude asks for a tool, the agent runs it in Python and sends the result back as a `tool_result`. This repeats until Claude answers with text, with a limit of 6 rounds.
4. The reply is shown and the whole history is saved to `sessions/<id>.json`.

The model never calculates anything. Prices, discounts, installments and dates come from the tools, which call plain Python functions covered by tests.

## Decisions and why

**Native tool calling with a hand-written loop, no framework.** The agent has five tools and a linear flow: receive, maybe call tools, answer. For this size, LangChain or LangGraph would add layers to explain and debug without adding control. The loop is about 40 lines and every step is visible. I would reach for LangGraph when the flow needs explicit state and branches, for example a return process with several steps and a human approval in the middle. The Anthropic SDK also has a "tool runner" that drives the loop for you, but it is still in beta, so I kept the manual loop.

**Structured tools instead of a SQL agent.** Letting the model write SQL over the customer and order tables would be faster to build, but it is hard to make safe. A fixed set of tools decides what can be read and how. The `order_status` tool, for example, only returns an order after the identity check passes, and there is no way to list customers.

**BM25 retrieval over the policy manual, one chunk per section.** The manual has 8 pages, so putting all of it in the system prompt would also work. I chose retrieval because it keeps the prompt short, it is the technique the role asks about, and it can be tested without an LLM. Chunks follow the manual headings, so each chunk is one rule. BM25 is implemented in about 20 lines (`policies.py`) instead of importing a library that pulls in numpy. Words lose accents, stopwords are removed, and each word is cut to its first 5 letters so that "devolver" and "devolução" match. I did not use embeddings because the vocabulary is small and fixed, and lexical search needs no extra model or key.

**All money math in Python with `Decimal`.** `pricing.py` holds the PIX discount, promotional prices, installment tiers and shipping. Rounding is half up, like a cashier. The tools send ready numbers to the model, so the model only has to read them.

**A frozen "now".** The orders in the dataset end in March 2026. If the agent used the real clock, every open order would look months late and "are you open now?" would never match the examples. `EMPORIO_NOW` sets the agent's date and time in the store timezone (`America/Campo_Grande`, UTC-4). The default is a Monday morning in March 2026. Tests and examples use it, which makes them reproducible.

**History as JSON files.** Each conversation is saved after every turn in `sessions/<id>.json` and can be resumed with `--session`. SQLite would be the next step if several channels or users shared the agent.

**CSV loaded with the standard library.** With 65 products, pandas would be an extra dependency without benefit. `data.py` reads the six CSV files into frozen dataclasses and only converts types. It does not "fix" the data, so the inconsistencies below stay visible.

**Model.** `claude-sonnet-5-5` by default, chosen for cost and speed. The model id is a setting, so it is easy to compare with others.

## Business rules applied

These come from the policy manual (`data/politicas_da_loja.md`, transcribed from the PDF) and are enforced in code or in the system prompt:

- A product can be sold only if its status is `active` and stock is above zero.
- Only promotions with `is_active = 1` count. Promotional prices are always shown next to the list price and the percentage.
- PIX gives 5% off the list price and does not stack with a promotion. The customer gets the lower of the two.
- Installments without interest follow the tiers in section 3.1: up to 3x (minimum R$50 each), 4x to 6x (minimum R$80), 7x to 12x (minimum R$100).
- Shipping in the metro area of Campo Grande is free from R$500.00, otherwise R$35, in 1 to 3 business days. For other cities the agent informs the carriers and deadlines and says the price depends on the ZIP code.
- Order status is shown only after the customer gives the order number, the full name on file and the e-mail or phone on file. A failed check returns one generic message, so nothing leaks, not even whether the order exists.
- The 7-day withdrawal window is computed in code from the estimated delivery date.
- The store sells only instruments. Accessories are declined politely with a suggestion to look for a partner store. Unrelated topics are declined in one sentence.
- Opening hours use the store timezone and the fixed-date national holidays.

## Data issues found and how they are handled

Reading the data before coding showed several problems. I did not change the data; the code handles each case and this list documents them.

- The catalog has 65 products in 6 categories. The manual says "more than 300" and lists 9 categories. Wind instruments and orchestral strings have no products, so the agent says the category exists but has no items.
- Product 96 is `active` with stock 0. Product 136 is `discontinued` but has 13 units. Product 130 is `coming_soon` with 2 units and still appears in orders 3 and 14. The availability rule above handles all three: none of them is sold.
- Product 140 is named Pearl but described as Tama. The agent shows the data as it is.
- Orders 3 and 20 have totals that do not match the sum of their items. The agent shows the recorded total.
- Two customers (11 and 43) share the same e-mail. This is why the identity check needs the full name plus a contact, never the e-mail alone.
- There is no delivery date, only an estimated one. The withdrawal window uses the estimate as an approximation, and the agent is told it is an estimate.
- The manual has two phone numbers: (67) 3341-4444 on the cover and in the company data, and (67) 3321-4500 for WhatsApp in section 7. The agent shows both with their labels.
- The payment table says "12x with a minimum installment of R$100" while section 3.1 gives tiers by number of installments. I used section 3.1.
- Exchanges for defects are limited to 30 days, while the legal warranty is 90 days. The agent gives the conservative reading and offers a human attendant for anything unusual.
- The manual says free shipping "above R$500" and a fee "below R$500", so exactly R$500.00 is not covered. I read it in favor of the customer: R$500.00 is free, R$499.99 pays the fee.
- Black Friday and the Musician's Week exist in the manual but have no active promotion in the data, so the agent does not promise those discounts.

## Known limitations

- Retrieval is lexical. A question with no word in common with a section fails, for example "estão abertos agora?" does not match the opening hours section. In this project the `store_status` tool covers that case, but a larger manual would need a hybrid search with embeddings.
- The identity check is a simple match on name and contact. It stops casual leaks, it is not real authentication.
- Only fixed-date national holidays are known. Carnival, Good Friday and Corpus Christi are not.
- Search results are capped at 10 products per call to keep the context small.
- Replies vary a little between runs, as with any LLM. The files in `examples/` are one real run.
- No streaming: the reply appears when it is complete. I left it out because most replies need one or two tool calls first, and the final text only starts after the last tool result, so streaming would save little in a terminal. Adding it is small work: the SDK has `client.messages.stream()`, the loop stays the same, the text deltas of the last round are printed as they arrive and `get_final_message()` gives the tool calls. The care point is to not print the text of the rounds that end in a tool call.
- No memory across sessions beyond the saved JSON files.

## What I would do with more time

- An automated evaluation set: the scripted scenarios with checks on the tool calls and on key facts in the replies, run on every change.
- SQLite for history and a small API, so the agent could sit behind WhatsApp or a web chat.
- LangGraph for flows with state, such as a return request that collects data, confirms with a human and opens a ticket.
- Hybrid retrieval (BM25 plus embeddings) if the manual grows.
- Streaming replies and prompt caching for the system prompt and tool definitions.
- Cost and latency logging per conversation.

## Use of AI coding assistants

I used Claude Code (with the Claude model) throughout this project, as a pair programmer. How it was used:

- Planning: reading the case, splitting the work into small steps and keeping a handoff file between sessions.
- Data analysis: reading the CSV files and the policy manual, finding the inconsistencies listed above.
- Code: writing each module and its tests after I agreed on the design, then explaining the decisions so I could defend them. I reviewed every step and asked for changes when something was not clear or not justified.
- Testing: running the tests and the real scenarios against the API, and fixing what came up (for example a console encoding error on Windows).
- Writing: this README was drafted with Claude Code and revised by me.

The commit history shows the order in which the parts were built.

## Project layout

```
data/                     CSV files, the policy PDF and its markdown transcription
examples/                 five example conversations with the tool calls shown
scripts/run_examples.py   generates the examples with the real API
src/emporio_agent/
  config.py               settings from .env (model, data folder, frozen "now")
  data.py                 CSV loading and typing, availability rule
  pricing.py              PIX, promotions, installments, shipping
  tools.py                product search and product details
  orders.py               order status with identity check
  store_info.py           address, phones, opening hours, timezone
  policies.py             manual sections and BM25 search
  agent.py                system prompt, tool definitions, tool-calling loop
  cli.py                  terminal chat
tests/                    61 tests, all run without an API key
```
