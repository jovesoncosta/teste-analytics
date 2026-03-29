
import pandas as pd
from pathlib import Path
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent
CLEAN_DATA_DIR = BASE_DIR / "data" / "clean"
FINAL_DATA_DIR = BASE_DIR / "data" / "final"

def build_obt():
    print("Iniciando modelagem da Camada Gold (Visão C-Level com Novas Métricas)...")
    
    debts = pd.read_csv(CLEAN_DATA_DIR / "clean_debts.csv")
    dispatches = pd.read_csv(CLEAN_DATA_DIR / "clean_dispatches.csv")
    messages = pd.read_csv(CLEAN_DATA_DIR / "clean_messages.csv")
    agreements = pd.read_csv(CLEAN_DATA_DIR / "clean_agreements.csv")
    payments = pd.read_csv(CLEAN_DATA_DIR / "clean_payments.csv")
    
    #Datas para datetime (medir tempo de conversão e cobrar indevida)
    dispatches['dispatched_at'] = pd.to_datetime(dispatches['dispatched_at'])
    agreements['agreed_at'] = pd.to_datetime(agreements['agreed_at'])
    
    #1 Campanhas, Engajamento e Data do Primeiro Disparo
    disp_agg = dispatches.groupby('debt_id').agg(
        num_dispatches=('dispatch_id', 'count'),
        campaign_id=('campaign_id', 'first'),
        first_dispatch_date=('dispatched_at', 'min'),
        last_dispatch_date=('dispatched_at', 'max') # Adicionado para checar cobrança indevida
    ).reset_index()
    
    msg_disp = messages.merge(dispatches[['dispatch_id', 'debt_id']], on='dispatch_id', how='inner')
    inbound_msgs = msg_disp[msg_disp['direction'] == 'inbound']
    eng_agg = inbound_msgs.groupby('debt_id').agg(has_response=('message_id', 'count')).reset_index()
    eng_agg['has_response'] = eng_agg['has_response'] > 0
    
    #2 Histórico e Filtro do Acordo Mais Recente
    hist_agr = agreements.groupby('debt_id').agg(num_agreements=('agreement_id', 'count')).reset_index()
    latest_agreements = agreements.sort_values('agreed_at').drop_duplicates(subset=['debt_id'], keep='last')
    
    #3 Agregando Pagamentos
    pay_agg = payments.groupby('agreement_id').agg(
        total_paid=('amount', 'sum'),
        installments_paid=('installment_number', 'count')
    ).reset_index()
    
    #4 Cruzando Acordo Ativo com seus pagamentos
    agr_active = latest_agreements.merge(pay_agg, on='agreement_id', how='left')
    agr_active['total_paid'] = agr_active['total_paid'].fillna(0.0)
    agr_active['installments_paid'] = agr_active['installments_paid'].fillna(0)
    
    #Selecionando colunas finais do acordo, incluindo a data (agreed_at)
    agr_agg = agr_active[['debt_id', 'amount', 'installments', 'installments_paid', 'total_paid', 'agreed_at']].copy()
    agr_agg = agr_agg.rename(columns={
        'amount': 'agreed_amount', 
        'installments': 'total_installments',
        'agreed_at': 'active_agreed_at' 
    })
    
    #Devolvendo histórico (Para o cálculo de Churn/Renegociação)
    agr_agg = agr_agg.merge(hist_agr, on='debt_id', how='left')
    
    agr_agg['agreed_amount'] = agr_agg['agreed_amount'].round(2)
    agr_agg['total_paid'] = agr_agg['total_paid'].round(2)
    
    #5 CONSTRUINDO A OBT (Tabela Final)
    obt = debts.merge(disp_agg, on='debt_id', how='left')
    obt = obt.merge(eng_agg, on='debt_id', how='left')
    obt = obt.merge(agr_agg, on='debt_id', how='left')
    
    #Tratamento de Nulos
    obt['num_dispatches'] = obt['num_dispatches'].fillna(0).astype(int)
    obt['has_response'] = obt['has_response'].fillna(False)
    obt['num_agreements'] = obt['num_agreements'].fillna(0).astype(int)
    obt['agreed_amount'] = obt['agreed_amount'].fillna(0.0)
    obt['total_paid'] = obt['total_paid'].fillna(0.0)
    obt['total_installments'] = obt['total_installments'].fillna(0).astype(int)
    obt['installments_paid'] = obt['installments_paid'].fillna(0).astype(int)
    obt['campaign_id'] = obt['campaign_id'].fillna('Sem Campanha')
    
    #Time-to-Agreement (Dias entre o 1º disparo e a assinatura do acordo)
    obt['days_to_agreement'] = (obt['active_agreed_at'] - obt['first_dispatch_date']).dt.days
    obt['days_to_agreement'] = np.where(obt['days_to_agreement'] < 0, np.nan, obt['days_to_agreement'])
    
    #(Desconto concedido no acordo em %)
    obt['discount_percentage'] = np.where(
        (obt['num_agreements'] > 0) & (obt['debt_amount'] > 0),
        ((obt['debt_amount'] - obt['agreed_amount']) / obt['debt_amount']) * 100,
        0.0
    )
    obt['discount_percentage'] = obt['discount_percentage'].round(2)
    
    #Churn de Acordo (Renegociação)
    #Criado uma flag (True/False) indicando se o cliente quebrou o acordo anterior
    obt['is_renegotiated'] = obt['num_agreements'] > 1
    
    # ---------------------------------------------------------------------
    # NOVAS MÉTRICAS DE NEGÓCIO (ANOMALIAS)
    # ---------------------------------------------------------------------
    
    # 1. Juros por Atraso de Pagamento (Overpayment)
    # Se o total pago for maior que o acordado, a diferença vai para cá
    obt['juros_pagamento_atraso'] = np.where(
        (obt['num_agreements'] > 0) & (obt['total_paid'] > obt['agreed_amount']),
        obt['total_paid'] - obt['agreed_amount'],
        0.0
    ).round(2)
    
    # 2. Cobrança Indevida (Disparo de Marketing após o Acordo)
    # Se a data do último disparo for MAIOR que a data de fechamento do acordo ativo
    obt['flag_cobranca_indevida'] = np.where(
        (obt['num_agreements'] > 0) & 
        (pd.notna(obt['last_dispatch_date'])) & 
        (obt['last_dispatch_date'] > obt['active_agreed_at']),
        True,
        False
    )
    
    # Limpando a coluna de last_dispatch_date para manter a OBT enxuta
    obt = obt.drop(columns=['last_dispatch_date'])
    
    # ---------------------------------------------------------------------

    #MÉTRICAS FINANCEIRAS CLÁSSICAS
    obt['remaining_balance'] = np.where(obt['num_agreements'] > 0, 
                                        obt['agreed_amount'] - obt['total_paid'], 
                                        obt['debt_amount'])
    # Se o cliente pagou a mais (overpayment), o saldo não pode ficar negativo, ele zera (clip)
    obt['remaining_balance'] = obt['remaining_balance'].clip(lower=0).round(2)
    
    obt['agreement_recovery_rate'] = np.where(obt['agreed_amount'] > 0, 
                                              (obt['total_paid'] / obt['agreed_amount']) * 100, 0)
    obt['agreement_recovery_rate'] = obt['agreement_recovery_rate'].round(2)
    
    conditions = [
        (obt['num_agreements'] > 0) & (obt['total_paid'] >= obt['agreed_amount']),
        (obt['num_agreements'] > 0) & (obt['total_paid'] > 0),
        (obt['num_agreements'] > 0) & (obt['total_paid'] == 0),
        (obt['has_response'] == True),
        (obt['num_dispatches'] > 0)
    ]
    choices = ['Quitado', 'Em Pagamento', 'Acordo Fechado', 'Engajado', 'Contatado']
    obt['status_fluxo'] = np.select(conditions, choices, default='Não Contatado')
    
    FINAL_DATA_DIR.mkdir(parents=True, exist_ok=True)
    obt.to_csv(FINAL_DATA_DIR / "obt_debts.csv", index=False)
    print("Sucesso! OBT gerada com as novas métricas (Time-to-Agreement, Haircut e Renegociação).")

if __name__ == "__main__":
    build_obt()