# Teste Técnico — Engenheiro de Dados @ Monest

## Sobre a Monest
Fazemos cobrança com IA via WhatsApp. São mais de 1 milhão de conversas por mês, vindas de múltiplas fontes de dados.

## Contexto
Você recebeu cinco conjuntos de dados simulados:

| Arquivo | Origem simulada | Descrição |
|---|---|---|
| `data/debts.csv` | MySQL | Dívidas em cobrança |
| `data/dispatches.csv` | MySQL | Disparos enviados por campanha |
| `data/messages.json` | DynamoDB | Mensagens trocadas nas conversas |
| `data/agreements.csv` | MySQL | Acordos fechados |
| `data/payments.csv` | MySQL | Pagamentos realizados |

## O desafio
Um cliente quer entender a performance das campanhas de cobrança — do disparo até o pagamento.

Você define o que faz sentido entregar.

## Requisitos
- Pipeline em Python que consolide as fontes e exporte um CSV
- Dashboard a partir do CSV processado (Streamlit, Metabase, ou ferramenta de sua escolha)
- DAG no Airflow para a orquestração
- Schema documentado do CSV de saída

## Pontos de avaliação
1. Funcionamento do pipeline
2. Qualidade das métricas escolhidas e da transformação
3. Tratamento de dados inconsistentes
4. Clareza da DAG
5. Visualização e storytelling do dashboard

## Entrega
Fork este repositório, implemente, e envie o link para matheus.morett@monest.com.br com o assunto **Teste AE - Monest**.

Se o repositório for privado, adicione **matheusmorett2** como colaborador.