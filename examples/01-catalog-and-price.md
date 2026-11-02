# Example 01: Catalog search and price quote

Goal: Product search with a budget filter, then a price quote with PIX and installments computed in code.

Agent time (EMPORIO_NOW): 2026-03-16 10:00 (-04). Model: claude-sonnet-5-5.

**Customer:** Oi! Quais violões vocês têm até 1000 reais?

<details><summary>Tool calls</summary>

- `search_products({"category": "violão", "max_price": 1000})`
  - result: `{"results": [{"product_id": 83, "name": "Tagima Memphis AC-39 Nylon Natural", "category": "Violões", "list_price_brl": 429.9, "promo_percent": null, "promo_price_brl": null, "pix_price_brl": 408.41, "best_cash_price_brl": 408.41, "availabil...`

</details>

**Empório:**

Oi! Tenho bastante opção até R$ 1.000. Os 10 mais em conta, com preço de tabela e preço no PIX (nenhum está em promoção agora):

Nylon:
- Tagima Memphis AC-39: R$ 429,90 (PIX R$ 408,41)
- Rozini RC-104 Estudante: R$ 459,90 (PIX R$ 436,91)
- Yamaha C40: R$ 599,90 (PIX R$ 569,91)
- Giannini GN-15 Cedro: R$ 689,00 (PIX R$ 654,55)
- Yamaha C70: R$ 849,00 (PIX R$ 806,55)

Aço:
- Shelby SN-100 Folk Preto: R$ 549,00 (PIX R$ 521,55)
- Giannini GF-1R Folk Sunburst: R$ 579,90 (PIX R$ 550,91)
- Yamaha F310: R$ 699,90 (PIX R$ 664,91)
- Tagima Dallas Tuner: R$ 749,00 (PIX R$ 711,55)

Elétrico (aço):
- Shelby SGD-195E Sunburst: R$ 799,00 (PIX R$ 759,05)

Todos estão disponíveis. Existem mais 2 modelos até esse valor, se quiser que eu procure.

Você está buscando para iniciar, ou já toca? E prefere corda de nylon ou de aço? Com isso eu te ajudo a escolher.

---

**Customer:** E quanto custa o Takamine GD20?

<details><summary>Tool calls</summary>

- `product_details({"name_or_id": "Takamine GD20"})`
  - result: `{"found": true, "product_id": 95, "name": "Takamine GD20 Dreadnought Natural", "category": "Violões", "description": "Violão dreadnought Takamine com tampo sólido em cedro. Excelente para fingerstyle com timbre quente e definido.", "specs":...`

</details>

**Empório:**

O Takamine GD20 Dreadnought Natural está disponível, com 5 unidades em estoque.

- Preço de tabela: R$ 2.199,00
- No PIX: R$ 2.089,05 (5% de desconto)
- No cartão: até 12x de R$ 183,25 sem juros

Ele não tem promoção ativa no momento. É um violão de aço com tampo sólido de cedro, costas e laterais em sapele e braço de mogno. Não tem eletrônica. O timbre é quente e definido, e funciona muito bem para fingerstyle.

Quer que eu compare com algum outro violão ou te ajude com mais alguma coisa?

---
