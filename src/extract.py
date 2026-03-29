import pandas as pd
import json
from pathlib import Path

#Definindo o caminho base do projeto para não termos erro de diretório
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = BASE_DIR / "data" / "raw"

def load_csv(file_name: str) -> pd.DataFrame:
    file_path = RAW_DATA_DIR / file_name
    try:
        df = pd.read_csv(file_path)
        print(f"Sucesso: {file_name} carregado com {len(df)} linhas.")
        return df
    except FileNotFoundError:
        print(f"Erro: Arquivo {file_name} não encontrado em {file_path}")
        return pd.DataFrame()

def load_messages() -> pd.DataFrame:
    file_path = RAW_DATA_DIR / "messages.json"
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        df = pd.DataFrame(data)
        print(f"Sucesso: messages.json carregado com {len(df)} linhas.")
        return df
    except FileNotFoundError:
        print(f"Erro: messages.json não encontrado em {file_path}")
        return pd.DataFrame()

if __name__ == "__main__":
    #Testando a extração
    print("Iniciando extração dos dados brutos...\n")
    df_debts = load_csv("debts.csv")
    df_dispatches = load_csv("dispatches.csv")
    df_agreements = load_csv("agreements.csv")
    df_payments = load_csv("payments.csv")
    df_messages = load_messages()