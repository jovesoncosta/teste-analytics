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

## 4. Qualidade das Métricas Escolhidas e da Transformação
O Dashboard construído em **Streamlit** não foca apenas em volumes, mas na eficiência real da operação de cobrança. As métricas foram desenhadas para responder às perguntas de negócio mais críticas:

* **Time-to-Agreement (Velocidade):** Mede em dias a agilidade da operação. É o tempo entre a primeira mensagem enviada (disparo) e a data da assinatura do acordo.
* **Desconto Médio vs. Variação:** O pipeline calcula a diferença entre o valor original devido e o valor acordado. O painel foi ajustado para mostrar isso como "% Variação", permitindo ver tanto os descontos concedidos (perdão de dívida) quanto os juros aplicados em parcelamentos longos.
* **Índice de Renegociação (Churn):** Identifica a taxa de clientes que precisaram refazer o acordo mais de uma vez, servindo como termômetro da qualidade da negociação inicial.
* **Visão Dupla (Caixa vs. Carteira):** O painel resolve a divergência clássica de CRM. A "Saúde dos Acordos" mostra o dinheiro atrelado apenas aos contratos vigentes (Camada Gold). O "Explorador de Caixa" mostra absolutamente todo o dinheiro recebido na conta bancária (Camada Silver), incluindo pagamentos de acordos que já foram cancelados no passado.

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
