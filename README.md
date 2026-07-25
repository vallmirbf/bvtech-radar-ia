# BV-TECH Radar IA

MVP para coletar ofertas de canais/grupos autorizados do Telegram, extrair produto/preço/link, calcular oportunidade de revenda e gerar alertas.

## O que já está implementado

- Coletor Telegram com Telethon.
- Leitura somente dos canais configurados.
- Extração de preço, link e descrição.
- Banco SQLite.
- Motor de pontuação BV-TECH.
- Critérios configuráveis:
  - custo de R$ 500 a R$ 5.000;
  - desconto mínimo de 40%;
  - ROI mínimo de 20%;
  - lucro líquido mínimo de R$ 300;
  - limite sugerido de concorrência;
- Dashboard web em Streamlit.
- Alerta pelo Telegram quando uma oferta é aprovada.
- Estrutura para integrar comparadores do Mercado Livre e outras fontes.

## Limitação inevitável

O Telegram exige autorização do titular da conta. Na primeira execução, será necessário informar:
1. `TELEGRAM_API_ID`;
2. `TELEGRAM_API_HASH`;
3. número de telefone;
4. código enviado pelo Telegram.

Essa autorização não pode ser feita por terceiros nem contornada com segurança. Depois da primeira autorização, a sessão fica salva localmente e o radar funciona de forma automática.

## Inicialização

1. Copie `.env.example` para `.env`.
2. Preencha as credenciais.
3. Rode:

```bash
docker compose up --build
```

Dashboard: `http://localhost:8501`

## Fontes de preço

O módulo `app/market.py` está preparado para receber:
- API oficial do Mercado Livre;
- provedores de busca;
- feeds de distribuidores;
- scraping permitido pelas regras de cada site.

Por padrão, o sistema aceita um preço de mercado informado por um adaptador. Não inventa preços quando a fonte não responde.
