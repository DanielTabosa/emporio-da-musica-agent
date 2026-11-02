# Example 04: Order status with identity check

Goal: The agent asks for identification before showing an order. A wrong attempt is refused without leaking data, then the correct data works.

Agent time (EMPORIO_NOW): 2026-03-16 10:00 (-04). Model: claude-sonnet-5-5.

**Customer:** Quero saber o status do meu pedido 8

**Empório:**

Claro, posso ver isso pra você. Para consultar o pedido, preciso confirmar alguns dados do cadastro:

- Seu nome completo
- O e-mail ou telefone que você usou no cadastro

Pode me passar?

---

**Customer:** Ana Ferreira, ana@gmail.com

<details><summary>Tool calls</summary>

- `order_status({"order_id": 8, "full_name": "Ana Ferreira", "contact": "ana@gmail.com"})`
  - result: `{"verified": false, "note": "Não foi possível confirmar a identidade com os dados informados. Peça ao cliente o número do pedido, o nome completo e o e-mail ou telefone do cadastro. Não revele nenhum dado do pedido."}`

</details>

**Empório:**

Ana, não consegui confirmar seus dados com as informações que você passou. Pode conferir o número do pedido, o nome completo e o e-mail ou telefone do cadastro e me mandar de novo?

Se preferir, também posso encaminhar você para um atendente humano.

---

**Customer:** Desculpa, é Ana Carolina Ferreira, anacarol.ferreira@coldmail.com

<details><summary>Tool calls</summary>

- `order_status({"order_id": 8, "full_name": "Ana Carolina Ferreira", "contact": "anacarol.ferreira@coldmail.com"})`
  - result: `{"verified": true, "order_id": 8, "customer_first_name": "Ana", "status": "enviado", "order_date": "2026-02-15", "payment_method": "cartão de débito", "total_brl": 349.9, "items": [{"product_id": 120, "name": "Kala KA-C Concert Mogno", "qua...`

</details>

**Empório:**

Pronto, Ana Carolina, encontrei seu pedido.

- Status: enviado
- Item: 1 ukulele Kala KA-C Concert Mogno
- Data do pedido: 15/02/2026
- Código de rastreio: BRJL5544332BR
- Previsão de entrega: 28/02/2026

A previsão já passou e o sistema ainda mostra o pedido como enviado, sem registro de entrega. Isso está atrasado. Pode ser que tenha acontecido algo com a transportadora. Vale conferir o rastreio com o código acima.

Se quiser, registro uma reclamação sobre o atraso. A equipe responsável retorna em até 24 horas úteis. Também posso encaminhar você para um atendente humano. Prefere qual dos dois?

---
