# Example 03: Return policy (right of withdrawal)

Goal: A policy question answered from the manual through retrieval, not from the model's memory.

Agent time (EMPORIO_NOW): 2026-03-16 10:00 (-04). Model: claude-sonnet-5-5.

**Customer:** Comprei um ukulele no site, chegou ontem, mas me arrependi. Posso devolver?

<details><summary>Tool calls</summary>

- `search_policy({"query": "devolução arrependimento compra online"})`
  - result: `{"results": [{"section": "4.1", "title": "Direito de Arrependimento (Compras Online)", "text": "- O cliente pode solicitar a devolução em até 7 (sete) dias corridos após o recebimento do produto, sem necessidade de justificativa.\n- O produ...`

</details>

**Empório:**

Pode sim. Como a compra foi online, você tem direito de arrependimento: são 7 dias corridos a partir do recebimento, e não precisa justificar. Como o ukulele chegou ontem, você está dentro do prazo.

Condições:
- O ukulele precisa estar na embalagem original, sem sinais de uso, com todos os acessórios e manuais.
- O reembolso é feito na mesma forma de pagamento da compra, em até 10 dias úteis.
- O frete da devolução é por conta da loja.

Para abrir a solicitação, o melhor é falar com a nossa equipe pelo WhatsApp ou pelo telefone da loja. Se quiser, passo os contatos e o horário de atendimento. Posso ajudar em mais alguma coisa?

---

**Customer:** E se eu quiser trocar por outro modelo em vez de devolver?

<details><summary>Tool calls</summary>

- `search_policy({"query": "troca por outro modelo produto sem defeito"})`
  - result: `{"results": [{"section": "4.3", "title": "Trocas por Preferência", "text": "- Trocas por preferência (cor, modelo, tamanho) são permitidas em até 7 dias, mediante disponibilidade do produto desejado.\n- O produto deve estar em perfeito esta...`

</details>

**Empório:**

Dá para trocar também. A troca por preferência (modelo, cor, tamanho) vale por até 7 dias, e você está dentro do prazo.

- O outro modelo precisa estar disponível em estoque.
- O ukulele que você recebeu tem que estar em perfeito estado e na embalagem original.
- Se os valores forem diferentes, você paga a diferença ou recebe o reembolso dela.

Se você já tiver um modelo em mente, me diga qual. Eu consulto se tem em estoque e o preço. Se ainda não escolheu, posso mostrar as opções de ukulele que temos.

---
