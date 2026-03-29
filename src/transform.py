import pandas as pd
from pathlib import Path
from extract import load_csv, load_messages

BASE_DIR = Path(__file__).resolve().parent.parent
CLEAN_DATA_DIR = BASE_DIR / "data" / "clean"

def clean_debts(df: pd.DataFrame) -> pd.DataFrame:
    df_clean = df.copy()
    df_clean['due_date'] = pd.to_datetime(df_clean['due_date'])
    df_clean = df_clean.drop_duplicates(subset=['debt_id'])
    return df_clean

def clean_dispatches(df: pd.DataFrame) -> pd.DataFrame:
    df_clean = df.copy()
    df_clean['dispatched_at'] = pd.to_datetime(df_clean['dispatched_at'])
    return df_clean

def clean_messages(df: pd.DataFrame) -> pd.DataFrame:
    df_clean = df.copy()
    df_clean['sent_at'] = pd.to_datetime(df_clean['sent_at'])
    return df_clean

def clean_agreements(df_agreements: pd.DataFrame, df_debts: pd.DataFrame) -> pd.DataFrame:
    df_clean = df_agreements.copy()
    df_clean['agreed_at'] = pd.to_datetime(df_clean['agreed_at'])
    
    #Removendo acordos órfãos (sem dívida atrelada)
    valid_debts = df_debts['debt_id'].unique()
    df_clean = df_clean[df_clean['debt_id'].isin(valid_debts)]
    return df_clean

def clean_payments(df_payments: pd.DataFrame, df_agreements: pd.DataFrame) -> pd.DataFrame:
    df_clean = df_payments.copy()
    df_clean['paid_at'] = pd.to_datetime(df_clean['paid_at'])
    
    #Remove pagamentos negativos (erros de sistema/estorno)
    df_clean = df_clean[df_clean['amount'] > 0]
    
    #Remove pagamentos órfãos (sem acordo atrelado)
    valid_agreements = df_agreements['agreement_id'].unique()
    df_clean = df_clean[df_clean['agreement_id'].isin(valid_agreements)]
    return df_clean

def run_cleaning_pipeline():
    print("Iniciando pipeline de limpeza (Silver)...")
    
    raw_debts = load_csv("debts.csv")
    raw_dispatches = load_csv("dispatches.csv")
    raw_messages = load_messages()
    raw_agreements = load_csv("agreements.csv")
    raw_payments = load_csv("payments.csv")
    
    print("Aplicando regras de qualidade de dados originais...")
    clean_debts_df = clean_debts(raw_debts)
    clean_dispatches_df = clean_dispatches(raw_dispatches)
    clean_messages_df = clean_messages(raw_messages)
    
    clean_agreements_df = clean_agreements(raw_agreements, clean_debts_df)
    clean_payments_df = clean_payments(raw_payments, clean_agreements_df)
    
    CLEAN_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    clean_debts_df.to_csv(CLEAN_DATA_DIR / "clean_debts.csv", index=False)
    clean_dispatches_df.to_csv(CLEAN_DATA_DIR / "clean_dispatches.csv", index=False)
    clean_messages_df.to_csv(CLEAN_DATA_DIR / "clean_messages.csv", index=False)
    clean_agreements_df.to_csv(CLEAN_DATA_DIR / "clean_agreements.csv", index=False)
    clean_payments_df.to_csv(CLEAN_DATA_DIR / "clean_payments.csv", index=False)
    
    print("Dados limpos salvos com sucesso!")

if __name__ == "__main__":
    run_cleaning_pipeline()