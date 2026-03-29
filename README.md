# 📊 Monest Analytics: Pipeline de Dados e Inteligência de Cobrança

Este projeto é uma solução completa de Engenharia e Análise de Dados ponta a ponta (End-to-End). O objetivo é processar dados brutos de uma operação de cobrança e entregá-los em um Dashboard, focado em eficiência de recuperação de crédito, fluxo de caixa e jornada do devedor.

---

## 1. Funcionamento do Pipeline (ETL e Camadas de Dados)
A arquitetura do projeto foi desenhada utilizando o conceito de **Arquitetura Medalhão**, que organiza os dados em camadas de maturidade, garantindo rastreabilidade e organização.

* **Camada Bronze (Extract):** É o ponto de partida. Aqui recebemos os dados brutos nos arquivos CSV (Dívidas, Acordos, Pagamentos, Disparos e Mensagens). Eles refletem exatamente o que está no banco de dados da empresa, sem nenhum filtro.
* **Camada Silver (Transform):** É a fase de higienização. Os scripts Python processam a camada Bronze para corrigir formatos de datas, remover linhas duplicadas e padronizar as tabelas para que conversem entre si perfeitamente.
* **Camada Gold (Load/Business):** É a camada de ouro. O script `build_obt.py` cruza todas as tabelas limpas da camada Silver e gera uma **OBT (One Big Table)**. Esta é uma tabela única, desnormalizada e pronta para o consumo, contendo apenas as métricas que importam para o negócio.

---

## 2. Clareza da Orquestração (Docker e Apache Airflow)
Para garantir que o processamento dos dados ocorra de forma automática e isolada, utilizamos o **Docker** e o **Apache Airflow**.

* **O Ambiente (Docker):** Todo o motor de processamento roda dentro de contêineres Docker. Isso significa que a infraestrutura é replicável; qualquer pessoa pode baixar este projeto e rodá-lo sem se preocupar com conflitos de versão no próprio computador.
  
<img width="309" height="372" alt="image" src="https://github.com/user-attachments/assets/54f328c1-e74c-4535-878c-6579b0f68086" />

* **O Maestro (Airflow):** O Apache Airflow atua como o orquestrador do nosso pipeline. Ele possui uma DAG (grafo de tarefas) que dita a ordem exata do ETL: primeiro extrai, depois limpa (Silver) e, por último, constrói a tabela final (Gold).

<img width="1864" height="666" alt="image" src="https://github.com/user-attachments/assets/c30da26f-110b-49ca-a0e5-b1585edefb49" />


* **Separação de Responsabilidades:** O Airflow roda nos bastidores (processamento *batch*) e desliga quando termina.

---

## 3. Tratamento de Dados e Regras de Negócio (Data Quality)

Para garantir a confiabilidade dos indicadores no dashboard, implementamos um rigoroso processo de qualidade de dados utilizando a Arquitetura Medalhão (Bronze ➔ Silver ➔ Gold).

### Camada Silver: Limpeza e Integridade
Nesta etapa, os dados brutos foram higienizados para corrigir falhas operacionais e de exportação do sistema legado:
* **Remoção de "Lixo" do Sistema:** Bloqueio de linhas de subtotal exportadas indevidamente que duplicavam o montante da carteira.
* **Integridade Referencial:** Exclusão de dados órfãos (ex: acordos atrelados a dívidas inexistentes ou pagamentos sem acordo válido).
* **Filtro Financeiro:** Remoção de pagamentos zerados ou negativos (identificados como estornos ou falhas de sistema).
* **Desduplicação:** Correção de falhas de retentativa do gateway de pagamento, mantendo apenas a transação válida mais recente por parcela.
* **Tratamento de Nulos (NaN):** Padronização de campos vazios para não quebrar os cálculos do painel (ex: nulos financeiros viraram `0.0`).

### Camada Gold: Regras de Negócio e Anomalias
Nesta etapa, aplicamos a inteligência de negócios para gerar as métricas finais consumidas pelos executivos (C-Level):
* **Blindagem de Acordos (Churn):** Clientes que renegociam a dívida geram múltiplas linhas históricas. O pipeline isola apenas o "Último Acordo" como ativo, evitando a duplicação do saldo devedor.
* **Captura de Juros (Overpayment):** Identificação de parcelas pagas com atraso cujo valor superou o acordado. A diferença foi separada na coluna `juros_pagamento_atraso` para mapear receitas extras.
* **Auditoria de Marketing (Cobrança Indevida):** Criação de uma flag automática (`flag_cobranca_indevida`) que cruza as datas e alerta quando o sistema disparou mensagens para clientes que já haviam fechado acordo.

---

## 4. Engenharia de Métricas e Lógica de Transformação
O pipeline não realiza apenas cruzamentos simples de tabelas (JOINs); ele aplica regras de negócio complexas durante a construção da OBT (Camada Gold) para entregar KPIs consolidados e prontos para uso analítico:

* **Cálculo de Time-to-Agreement:** Transformação temporal (manipulação de `datetime`) que subtrai a data do primeiro contato sistêmico da data de assinatura do acordo, gerando a cadência exata de conversão em dias.
* **Modelagem de Variação Financeira:** Implementação de cálculo matemático dinâmico `((Dívida - Acordo) / Dívida * 100)`. A lógica foi estruturada na camada de transformação para identificar perfeitamente tanto o perdão de dívida (desconto concedido) quanto o acréscimo de juros em parcelamentos.
* **Flag de Churn (Índice de Renegociação):** Criação de uma variável analítica baseada no agrupamento de histórico do cliente. A regra de ETL identifica de forma automatizada se o cliente possui múltiplas repactuações (`num_agreements > 1`), sinalizando a quebra de contratos anteriores.
* **Isolamento de Domínios (Contábil vs. Operacional):** A modelagem de dados separou intencionalmente a regra de cálculo. A OBT foi desenhada para refletir o saldo da "Foto Atual" (isolando apenas a carteira vigente), enquanto a modelagem de pagamentos na Camada Silver foi projetada para auditoria do "Filme Completo", garantindo que a entrada de caixa histórico nunca se perca.

---

## 5. Visualização do Dashboard
O design do painel (front-end) foi construído em **Streamlit**. A regra de ouro aplicada foi evitar a "sobrecarga cognitiva": o painel não joga gráficos aleatórios na tela, ele conta uma história linear dividida em três atos (Abas):

### Ato 1: O Esforço e a Jornada (Aba 1 - Funil da Campanha)
Responde à pergunta *"O quanto estamos trabalhando e convertendo?"*.
* Inicia com o Funil de Conversão (do cliente contatado até a quitação), mostrando os gargalos da operação.

<img width="1062" height="390" alt="image" src="https://github.com/user-attachments/assets/0f3660d0-370a-4a82-bc54-49c4e846f3a9" />


* Traz um gráfico de linha do tempo cruzando "Disparos vs. Respostas", provando visualmente se o volume de mensagens enviadas está gerando engajamento real no dia a dia.

<img width="1571" height="439" alt="image" src="https://github.com/user-attachments/assets/c67a066e-0e37-4d6b-9cd3-8369159d746b" />



### Ato 2: A Saúde do Negócio (Aba 2 - Saúde dos Acordos)
Responde à pergunta *"Quão bons são os acordos que estamos fechando?"*.
* Apresenta Sinais Vitais em cards diretos (Desconto concedido, Taxa de Quebra/Renegociação e Taxas de Pagamento).

<img width="1395" height="319" alt="image" src="https://github.com/user-attachments/assets/0058c391-e6d1-4819-a060-6eff9b331c04" />

* Utiliza gráficos de barras empilhadas e horizontais para ranquear Campanhas e Credores.

<img width="1550" height="418" alt="image" src="https://github.com/user-attachments/assets/0e18dc0d-f287-4bdf-880c-55f298bbc628" />

* **UX Avançada (Tooltips):** Os gráficos possuem caixas de informação customizadas. Ao passar o mouse sobre o Credor, o executivo vê não apenas o valor recuperado, mas o Desconto Médio e a Eficiência %, mantendo a tela limpa e entregando detalhes sob demanda.
* **Tabela de Auditoria:** Uma visão detalhada que mantém o histórico de acordos Cancelados, Quitações e Em Pagamento, permitindo auditoria rápida de qualquer ID sem sair da tela.

<img width="1557" height="403" alt="image" src="https://github.com/user-attachments/assets/e93bb3d4-3890-4c41-979e-567c336692a0" />


### Ato 3: O Bottom Line (Aba 3 - Explorador de Caixa)
Responde à pergunta *"Quanto dinheiro efetivamente entrou na conta?"*.
* Uma visão puramente financeira (Cash Flow), destacando o ticket médio, o método de pagamento preferido pelos devedores e uma matriz dinâmica para cruzar receitas por mês e por credor.

<img width="1568" height="868" alt="image" src="https://github.com/user-attachments/assets/1c1655f6-13b1-450b-83b0-b935d5def9c1" />


---

## 🛠️ Tecnologias Utilizadas
* **Python** (Pandas, Numpy)
* **Apache Airflow** (Orquestração de ETL)
* **Docker** (Containerização)
* **Streamlit & Plotly** (Desenvolvimento do Dashboard e Visualização de Dados)
