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
* **O Maestro (Airflow):** O Apache Airflow atua como o orquestrador do nosso pipeline. Ele possui uma DAG (grafo de tarefas) que dita a ordem exata do ETL: primeiro extrai, depois limpa (Silver) e, por último, constrói a tabela final (Gold).
* **Separação de Responsabilidades:** O Airflow roda nos bastidores (processamento *batch*) e desliga quando termina. Ele não interfere no Dashboard (Streamlit), que fica disponível 24/7 apenas consumindo os dados prontos da camada Gold. Se o Airflow falhar hoje, o painel continua no ar mostrando os dados de ontem.

---

## 3. Tratamento de Dados Inconsistentes (Data Quality)
Para que se confie nos números do painel, foram implementadas regras rigorosas de qualidade de dados durante a transição da camada Bronze para a Silver e Gold:

* **Validação Financeira:** Pagamentos com valores zerados ou negativos (que geralmente representam estornos ou erros de sistema) foram bloqueados para não inflar artificialmente o caixa.
* **Integridade Referencial (Órfãos):** Acordos vinculados a dívidas que não existem na base principal, ou pagamentos vinculados a acordos deletados, são removidos automaticamente do cálculo.
* **Tratamento de Valores Nulos:** Dados vazios (NaN) foram preenchidos com inteligência lógica. Valores financeiros vazios viram 0.0, contagens viram 0, e categorias sem nome viram 'Sem Campanha', evitando que o painel quebre ao tentar calcular médias.
* **Blindagem de Acordos Ativos:** Clientes que quebram acordos e renegociam a dívida geram múltiplas linhas. O pipeline foi programado para isolar apenas o "Último Acordo" como ativo, tratando os anteriores como "Cancelados". Isso evita que a dívida do cliente seja somada duas vezes no montante total.

---

## 4. Engenharia de Métricas e Lógica de Transformação
O pipeline não realiza apenas cruzamentos simples de tabelas (JOINs); ele aplica regras de negócio complexas durante a construção da OBT (Camada Gold) para entregar KPIs consolidados e prontos para uso analítico:

* **Cálculo de Time-to-Agreement:** Transformação temporal (manipulação de `datetime`) que subtrai a data do primeiro contato sistêmico da data de assinatura do acordo, gerando a cadência exata de conversão em dias.
* **Modelagem de Variação Financeira (Haircut):** Implementação de cálculo matemático dinâmico `((Dívida - Acordo) / Dívida * 100)`. A lógica foi estruturada na camada de transformação para identificar perfeitamente tanto o perdão de dívida (desconto concedido) quanto o acréscimo de juros em parcelamentos.
* **Flag de Churn (Índice de Renegociação):** Criação de uma variável analítica baseada no agrupamento de histórico do cliente. A regra de ETL identifica de forma automatizada se o cliente possui múltiplas repactuações (`num_agreements > 1`), sinalizando a quebra de contratos anteriores.
* **Isolamento de Domínios (Contábil vs. Operacional):** A modelagem de dados separou intencionalmente a regra de cálculo. A OBT foi desenhada para refletir o saldo da "Foto Atual" (isolando apenas a carteira vigente), enquanto a modelagem de pagamentos na Camada Silver foi projetada para auditoria do "Filme Completo", garantindo que a entrada de caixa histórico nunca se perca.

---

## 5. Visualização do Dashboard
O design do painel (front-end) foi construído em **Streamlit**. A regra de ouro aplicada foi evitar a "sobrecarga cognitiva": o painel não joga gráficos aleatórios na tela, ele conta uma história linear dividida em três atos (Abas):

### Ato 1: O Esforço e a Jornada (Aba 1 - Funil da Campanha)
Responde à pergunta *"O quanto estamos trabalhando e convertendo?"*.
* Inicia com o Funil de Conversão (do cliente contatado até a quitação), mostrando os gargalos da operação.
* Traz um gráfico de linha do tempo cruzando "Disparos vs. Respostas", provando visualmente se o volume de mensagens enviadas está gerando engajamento real no dia a dia.

### Ato 2: A Saúde do Negócio (Aba 2 - Saúde dos Acordos)
Responde à pergunta *"Quão bons são os acordos que estamos fechando?"*.
* Apresenta Sinais Vitais em cards diretos (Desconto concedido, Taxa de Quebra/Renegociação e Taxas de Pagamento).
* Utiliza gráficos de barras empilhadas e horizontais para ranquear Campanhas e Credores.
* **UX Avançada (Tooltips):** Os gráficos possuem caixas de informação customizadas. Ao passar o mouse sobre o Credor, o executivo vê não apenas o valor recuperado, mas o Desconto Médio e a Eficiência %, mantendo a tela limpa e entregando detalhes sob demanda.
* **Tabela de Auditoria:** Uma visão detalhada que mantém o histórico de acordos Cancelados, Quitações e Em Pagamento, permitindo auditoria rápida de qualquer ID sem sair da tela.

### Ato 3: O Bottom Line (Aba 3 - Explorador de Caixa)
Responde à pergunta *"Quanto dinheiro efetivamente entrou na conta?"*.
* Uma visão puramente financeira (Cash Flow), destacando o ticket médio, o método de pagamento preferido pelos devedores e uma matriz dinâmica para cruzar receitas por mês e por credor.

---

## 🛠️ Tecnologias Utilizadas
* **Python** (Pandas, Numpy)
* **Apache Airflow** (Orquestração de ETL)
* **Docker** (Containerização)
* **Streamlit & Plotly** (Desenvolvimento do Dashboard e Visualização de Dados)
