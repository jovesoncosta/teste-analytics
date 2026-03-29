# import os
# from datetime import datetime, timedelta
# from airflow import DAG
# from airflow.operators.bash import BashOperator

# #Descobre automaticamente a pasta raiz do projeto (dois níveis acima deste arquivo)
# DAGS_FOLDER = os.path.dirname(os.path.abspath(__file__))
# PROJECT_ROOT = os.path.dirname(DAGS_FOLDER)

# default_args = {
#     'owner': 'analytics_engineer',
#     'depends_on_past': False,
#     'start_date': datetime(2026, 3, 1),
#     'retries': 1,
#     'retry_delay': timedelta(minutes=1),
# }

# with DAG(
#     'monest_daily_billing_pipeline',
#     default_args=default_args,
#     description='Pipeline de ETL de cobrança da Monest',
#     schedule_interval='0 6 * * *', #Roda todo dia às 06:00
#     catchup=False,
#     tags=['monest', 'billing'],
# ) as dag:

#     #Aponta exatamente para o executável Python do nosso ambiente virtual
#     PYTHON_EXEC = "python" 

#     #Camada Silver
#     run_silver_layer = BashOperator(
#         task_id='run_cleaning_silver',
#         bash_command=f'cd {PROJECT_ROOT} && {PYTHON_EXEC} src/transform.py'
#     )

#     #Camada Gold
#     run_gold_layer = BashOperator(
#         task_id='run_modeling_gold',
#         bash_command=f'cd {PROJECT_ROOT} && {PYTHON_EXEC} src/build_obt.py'
#     )

#     #Dependências
#     run_silver_layer >> run_gold_layer

import os
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

# Descobre automaticamente a pasta raiz do projeto (dois níveis acima deste arquivo)
DAGS_FOLDER = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(DAGS_FOLDER)

default_args = {
    'owner': 'analytics_engineer',
    'depends_on_past': False,
    'start_date': datetime(2026, 3, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
}

with DAG(
    'monest_daily_billing_pipeline',
    default_args=default_args,
    description='Pipeline de ETL de cobrança da Monest',
    schedule_interval='0 6 * * *', # Roda todo dia às 06:00
    catchup=False,
    tags=['monest', 'billing', 'medallion'],
) as dag:

    # Aponta exatamente para o executável Python do nosso ambiente virtual
    PYTHON_EXEC = "python" 

    # 1. Camada Bronze (Extração e Ingestão)
    run_bronze_layer = BashOperator(
        task_id='run_extraction_bronze',
        bash_command=f'cd {PROJECT_ROOT} && {PYTHON_EXEC} src/extract.py'
    )

    # 2. Camada Silver (Limpeza e Qualidade de Dados)
    run_silver_layer = BashOperator(
        task_id='run_cleaning_silver',
        bash_command=f'cd {PROJECT_ROOT} && {PYTHON_EXEC} src/transform.py'
    )

    # 3. Camada Gold (Regras de Negócio e OBT)
    run_gold_layer = BashOperator(
        task_id='run_modeling_gold',
        bash_command=f'cd {PROJECT_ROOT} && {PYTHON_EXEC} src/build_obt.py'
    )

    # Definindo as Dependências (A mágica da orquestração)
    run_bronze_layer >> run_silver_layer >> run_gold_layer