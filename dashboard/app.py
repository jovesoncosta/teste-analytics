
import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import numpy as np

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Monest | Analytics", layout="wide", page_icon="🚀")

# --- FUNÇÃO AUXILIAR DE FORMATAÇÃO ---
def formatar_moeda(valor):
    if pd.isna(valor): 
        return "R$ 0,00"
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# --- CARREGAMENTO DE DADOS COM CACHE (PERFORMANCE EXTREMA) ---
@st.cache_data
def load_data():
    base_dir = Path(__file__).resolve().parent.parent
    obt = pd.read_csv(base_dir / "data" / "final" / "obt_debts.csv")
    payments = pd.read_csv(base_dir / "data" / "clean" / "clean_payments.csv")
    agreements = pd.read_csv(base_dir / "data" / "clean" / "clean_agreements.csv")
    dispatches = pd.read_csv(base_dir / "data" / "clean" / "clean_dispatches.csv")
    messages = pd.read_csv(base_dir / "data" / "clean" / "clean_messages.csv")
    
    payments['paid_at'] = pd.to_datetime(payments['paid_at'])
    agreements['agreed_at'] = pd.to_datetime(agreements['agreed_at'])
    dispatches['dispatched_at'] = pd.to_datetime(dispatches['dispatched_at'])
    messages['sent_at'] = pd.to_datetime(messages['sent_at'])
    
    return obt, payments, agreements, dispatches, messages

# Carrega os dados na memória (Agora super rápido por causa do Cache!)
df_obt, df_pay, df_agr, df_disp, df_msg = load_data()

# --- TRADUÇÃO DE NOMES TÉCNICOS PARA O NEGÓCIO ---
mapa_campanhas = {
    'camp_inadiplencia': 'Campanha Inadimplência',
    'camp_inadimplencia': 'Campanha Inadimplência', 
    'camp_pme': 'Campanha PME',
    'camp_varejo': 'Campanha Varejo'
}
df_obt['campaign_id'] = df_obt['campaign_id'].replace(mapa_campanhas)
df_disp['campaign_id'] = df_disp['campaign_id'].replace(mapa_campanhas)


# --- CABEÇALHO ---
st.title("Inteligência de Cobrança - Visão")
st.markdown("Monitoramento estratégico: funil de conversão, saúde da carteira negociada e fluxo financeiro.")

# --- FILTROS GLOBAIS (BARRA LATERAL) ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/4762/4762311.png", width=80)
st.sidebar.header("Filtros Globais")
campanhas = sorted(df_obt['campaign_id'].unique().tolist())
camp_sel = st.sidebar.multiselect("Campanha Origem", campanhas, default=campanhas)

# Filtra a OBT e Pagamentos
df_filtered = df_obt[df_obt['campaign_id'].isin(camp_sel)]
pay_full = df_pay.merge(df_agr[['agreement_id', 'debt_id']], on='agreement_id', how='inner')
pay_full = pay_full.merge(df_obt[['debt_id', 'campaign_id', 'creditor']], on='debt_id', how='inner')
pay_filtered = pay_full[pay_full['campaign_id'].isin(camp_sel)].copy()

# Filtra Disparos e Mensagens para a Aba 1
disp_filtered = df_disp[df_disp['campaign_id'].isin(camp_sel)].copy()
msg_filtered = df_msg.merge(disp_filtered[['dispatch_id']], on='dispatch_id', how='inner')


# ==========================================
# CONSTRUÇÃO DAS ABAS (TABS)
# ==========================================
tab1, tab2, tab3 = st.tabs(["🎯 Funil da Campanha", "🤝 Saúde dos Acordos (Fluxo)", "📅 Explorador de Caixa"])

# ----------------- ABA 1: FUNIL CUMULATIVO -----------------
with tab1:
    st.markdown("### 🎯 Jornada e Velocidade da Operação")
    
    col_tempo, col_funil = st.columns([3, 7])
    
    with col_tempo:
        st.markdown("#### ⏱️ Velocidade de Conversão")
        st.info("O **Time-to-Agreement** mede a agilidade da operação: quantos dias, em média, levamos para fechar um acordo após o 1º contato via sistema.")
        
        tempo_medio = df_filtered['days_to_agreement'].mean()
        if pd.isna(tempo_medio):
            st.metric("Tempo Médio de Acordo", "N/D")
        else:
            st.metric("Tempo Médio (1º Contato ➔ Acordo)", f"{tempo_medio:.1f} dias")
    
    with col_funil:
        st.markdown("#### Jornada de Conversão (Funil)")
        
        contatados = len(df_filtered[df_filtered['num_dispatches'] > 0])
        engajados = len(df_filtered[df_filtered['has_response'] == True])
        acordos = len(df_filtered[df_filtered['num_agreements'] > 0])
        pagantes = len(df_filtered[(df_filtered['num_agreements'] > 0) & (df_filtered['total_paid'] > 0)])
        quitados = len(df_filtered[(df_filtered['num_agreements'] > 0) & (df_filtered['total_paid'] >= df_filtered['agreed_amount'])])

        funnel_data = pd.DataFrame({
            'Etapa': ['1. Contatados', '2. Engajados', '3. Acordo Fechado', '4. Fizeram Pagamento', '5. Acordo Quitado'],
            'Quantidade': [contatados, engajados, acordos, pagantes, quitados]
        })
        
        fig_funnel = px.funnel(funnel_data, x='Quantidade', y='Etapa', color='Etapa', color_discrete_sequence=px.colors.sequential.Blues_r)
        fig_funnel.update_traces(textinfo="value", textposition="inside")
        fig_funnel.update_layout(showlegend=False, yaxis_title="", xaxis_title="Volume de Dívidas Únicas", hovermode="y unified", yaxis={'categoryorder': 'array', 'categoryarray': funnel_data['Etapa']})
        
        st.plotly_chart(fig_funnel, use_container_width=True)

    st.divider()


    st.markdown("#### 📈 Volume de Esforço Operacional (Interações Totais)")
    st.caption("Acompanhe o total de disparos enviados pelo sistema e o total de respostas recebidas (inclui mensagens repetidas do mesmo cliente no mesmo dia).")
    
    if not disp_filtered.empty:
        disp_filtered['Data'] = disp_filtered['dispatched_at'].dt.date
        daily_disp = disp_filtered.groupby('Data').size().reset_index(name='Disparos')
        
        msg_inbound = msg_filtered[msg_filtered['direction'] == 'inbound'].copy()
        msg_inbound['Data'] = msg_inbound['sent_at'].dt.date
        daily_msg = msg_inbound.groupby('Data').size().reset_index(name='Respostas')
        
        daily_trend = pd.merge(daily_disp, daily_msg, on='Data', how='outer').fillna(0).sort_values('Data')
        
        fig_trend = px.line(
            daily_trend, 
            x='Data', 
            y=['Disparos', 'Respostas'],
            markers=True,
            color_discrete_map={'Disparos': '#a6bddb', 'Respostas': '#08519c'}
        )
        
        fig_trend.update_layout(
            xaxis_title="",
            yaxis_title="Volume de Interações",
            hovermode="x unified",
            legend_title_text="Tipo de Ação",
            margin=dict(t=20, b=20, l=0, r=0)
        )
        
        fig_trend.update_traces(hovertemplate="Data: <b>%{x}</b><br>Volume: <b>%{y}</b><extra></extra>")
        st.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.info("Nenhum dado de engajamento disponível para os filtros selecionados.")


# ----------------- ABA 2: SAÚDE DOS ACORDOS E CREDORES -----------------
with tab2:
    st.markdown("### 🤝 Acompanhamento de Acordos e Performance de Credores")
    
    df_acordos = df_filtered[df_filtered['num_agreements'] > 0].copy()
    
    if not df_acordos.empty:
        st.markdown("#### 📉 Sinais Vitais da Carteira")
        
        r1_col1, r1_col2, r1_col3, r1_col4 = st.columns(4)
        
        total_due = df_filtered["debt_amount"].sum()
        total_agreed = df_filtered["agreed_amount"].sum()
        total_paid = df_filtered["total_paid"].sum()
        dividas_negociadas = len(df_filtered[df_filtered["num_agreements"] > 0])
        
        pct_renegociado = (total_agreed / total_due * 100) if total_due > 0 else 0
        gap_pagamento = total_agreed - total_paid

        r1_col1.metric("Montante Original Devido", formatar_moeda(total_due))
        r1_col2.metric("Valor Renegociado (Acordos)", formatar_moeda(total_agreed), f"Representa {pct_renegociado:.1f}% do Original", delta_color="off")
        r1_col3.metric("Total Já Pago", formatar_moeda(total_paid), f"Restam {formatar_moeda(gap_pagamento)}", delta_color="off")
        r1_col4.metric("Dívidas Negociadas", f"{dividas_negociadas}")
        
        st.write("") 
        
        r2_col1, r2_col2, r2_col3, r2_col4 = st.columns(4)
        
        haircut_medio = df_acordos['discount_percentage'].mean()
        taxa_renegociacao = (df_acordos['is_renegotiated'].sum() / len(df_acordos)) * 100
        taxa_pagantes = (len(df_acordos[df_acordos['total_paid'] > 0]) / len(df_acordos)) * 100
        
        qtd_quitados = len(df_acordos[df_acordos['status_fluxo'] == 'Quitado'])
        taxa_quitados = (qtd_quitados / len(df_acordos)) * 100
        
        r2_col1.metric("✂️ Desconto Médio", f"{haircut_medio:.1f}%", "Perdão concedido s/ a dívida", delta_color="off")
        r2_col2.metric("🔄 Índice de Renegociação", f"{taxa_renegociacao:.1f}%", "Clientes que refizeram acordo", delta_color="off")
        r2_col3.metric("⏳ Taxa de Acordos Pagantes", f"{taxa_pagantes:.1f}%", "Já pagaram ao menos 1 parcela", delta_color="off")
        r2_col4.metric("✅ Taxa de Quitação", f"{taxa_quitados:.1f}%", f"{qtd_quitados} acordos 100% liquidados", delta_color="off")
        
        st.divider()

        col_bar, col_creditor = st.columns(2)
        
        with col_bar:
            st.markdown("#### Progresso Financeiro por Campanha")
            progresso = df_acordos.groupby('campaign_id').agg(
                Agordado=('agreed_amount', 'sum'),
                Pago=('total_paid', 'sum'),
                Saldo_Devedor=('remaining_balance', 'sum')
            ).reset_index()
            
            progresso_melted = progresso.melt(
                id_vars=['campaign_id', 'Agordado'], 
                value_vars=['Pago', 'Saldo_Devedor'], 
                var_name='Status', 
                value_name='Valor'
            )
            progresso_melted['Status'] = progresso_melted['Status'].replace({'Saldo_Devedor': 'Saldo Devedor'})
            progresso_melted['Valor_R$'] = progresso_melted['Valor'].apply(formatar_moeda)
            progresso_melted['Total_R$'] = progresso_melted['Agordado'].apply(formatar_moeda)
            
            fig_bar = px.bar(
                progresso_melted, x='campaign_id', y='Valor', color='Status', text_auto='.2s', 
                barmode='stack', color_discrete_map={'Pago': '#08519c', 'Saldo Devedor': '#bdd7e7'}, custom_data=['Valor_R$', 'Total_R$'] 
            )
            fig_bar.update_traces(hovertemplate="<b>%{x}</b><br><br>Status: <b>%{data.name}</b><br>Volume: %{customdata[0]}<br>---<br><b>Total Acordado: %{customdata[1]}</b><extra></extra>")
            fig_bar.update_layout(xaxis_title="", yaxis_title="Volume (R$)", hovermode="closest", legend_title_text="")
            st.plotly_chart(fig_bar, use_container_width=True)
            
        with col_creditor:
            st.markdown("#### Ranking de Recuperação por Credor")
            creditor_stats = df_acordos.groupby('creditor').agg(
                Valor_Acordado=('agreed_amount', 'sum'),
                Valor_Pago=('total_paid', 'sum'),
                Desconto_Medio=('discount_percentage', 'mean')
            ).reset_index()
            
            creditor_stats['Taxa_Recuperacao'] = (creditor_stats['Valor_Pago'] / creditor_stats['Valor_Acordado']) * 100
            creditor_stats['Taxa_Recuperacao'] = creditor_stats['Taxa_Recuperacao'].fillna(0).round(1)
            creditor_stats = creditor_stats.sort_values('Valor_Pago', ascending=True)
            
            creditor_stats['Pago_R$'] = creditor_stats['Valor_Pago'].apply(formatar_moeda)
            creditor_stats['Acordado_R$'] = creditor_stats['Valor_Acordado'].apply(formatar_moeda)
            
            fig_cred = px.bar(
                creditor_stats, y='creditor', x='Valor_Pago', orientation='h', color='Taxa_Recuperacao', 
                color_continuous_scale='Blues', text_auto='.2s', custom_data=['Pago_R$', 'Acordado_R$', 'Taxa_Recuperacao', 'Desconto_Medio'] 
            )
            fig_cred.update_traces(hovertemplate="<b>Credor: %{y}</b><br><br>Caixa Realizado: <b>%{customdata[0]}</b><br>---<br>Total Acordado: %{customdata[1]}<br><b>Eficiência: %{customdata[2]:.1f}%</b><br>Desconto Médio: <b>%{customdata[3]:.1f}%</b><extra></extra>")
            fig_cred.update_layout(yaxis_title="", xaxis_title="Caixa Realizado (R$)", coloraxis_colorbar_title="Eficiência<br>(%)", hovermode="closest")
            st.plotly_chart(fig_cred, use_container_width=True)
            
        st.divider()
        
        st.markdown("#### 📋 Detalhamento Crítico (Histórico Completo de Acordos)")
        
        all_agreements = df_agr[df_agr['debt_id'].isin(df_filtered['debt_id'])].copy()
        
        # ---> ALTERAÇÃO AQUI: Trazendo as novas colunas da OBT <---
        colunas_obt = ['debt_id', 'creditor', 'debt_amount', 'juros_pagamento_atraso', 'flag_cobranca_indevida']
        all_agreements = all_agreements.merge(df_filtered[colunas_obt], on='debt_id', how='left')
        
        pay_agg_detalhe = df_pay.groupby('agreement_id').agg(
            total_paid=('amount', 'sum'),
            installments_paid=('installment_number', 'count')
        ).reset_index()
        
        all_agreements = all_agreements.merge(pay_agg_detalhe, on='agreement_id', how='left')
        all_agreements['total_paid'] = all_agreements['total_paid'].fillna(0.0)
        all_agreements['installments_paid'] = all_agreements['installments_paid'].fillna(0).astype(int)
        
        # BLINDAGEM DE PONTO FLUTUANTE E FORMATAÇÃO DAS NOVAS COLUNAS
        all_agreements['amount'] = all_agreements['amount'].round(2)
        all_agreements['total_paid'] = all_agreements['total_paid'].round(2)
        all_agreements['remaining_balance'] = (all_agreements['amount'] - all_agreements['total_paid']).clip(lower=0)
        all_agreements['juros_pagamento_atraso'] = all_agreements['juros_pagamento_atraso'].fillna(0.0).round(2)
        
        # Transformando True/False em ícones visuais
        all_agreements['flag_cobranca_indevida'] = all_agreements['flag_cobranca_indevida'].apply(lambda x: '🚨 Sim' if x == True else '✅ Não')
        
        all_agreements['discount_percentage'] = np.where(
            all_agreements['debt_amount'] > 0,
            ((all_agreements['debt_amount'] - all_agreements['amount']) / all_agreements['debt_amount']) * 100,
            0.0
        )
        
        all_agreements = all_agreements.sort_values('agreed_at')
        ultimos_acordos = all_agreements.drop_duplicates(subset=['debt_id'], keep='last')['agreement_id'].tolist()
        
        conditions_acordo = [
            (~all_agreements['agreement_id'].isin(ultimos_acordos)), 
            (all_agreements['total_paid'] >= all_agreements['amount']),
            (all_agreements['total_paid'] > 0)
        ]
        choices_acordo = ['❌ Cancelado', '✅ Quitado', '⏳ Em Pagamento']
        all_agreements['Status'] = np.select(conditions_acordo, choices_acordo, default='📝 Acordo Fechado')
        
        # ---> ALTERAÇÃO AQUI: Inserindo as colunas na visão final <---
        df_detalhe = all_agreements[['debt_id', 'agreement_id', 'creditor', 'amount', 'discount_percentage', 'total_paid', 'remaining_balance', 'juros_pagamento_atraso', 'installments', 'installments_paid', 'flag_cobranca_indevida', 'Status']]
        df_detalhe.columns = ['ID Dívida', 'ID Acordo', 'Credor', 'Valor Acordado', '% Variação', 'Total Pago', 'Saldo Devedor', 'Juros/Overpayment', 'Qtd Parcelas', 'Parcelas Pagas', 'Cobrança Indevida', 'Status']
        
        df_sorted = df_detalhe.sort_values(by=['ID Dívida', 'Status'], ascending=[True, False])
        
        st.dataframe(
            df_sorted.style.format({
                'Valor Acordado': formatar_moeda,
                'Total Pago': formatar_moeda,
                'Saldo Devedor': formatar_moeda,
                'Juros/Overpayment': formatar_moeda, # Nova formatação de moeda
                '% Variação': "{:.1f}%"
            }), 
            hide_index=True, 
            use_container_width=True
        )
    else:
        st.info("Nenhum acordo encontrado para os filtros selecionados.")


# ----------------- ABA 3: EXPLORADOR DE CAIXA (DESIGN LIMPO) -----------------
with tab3:
    st.markdown("### 📅 Explorador de Fluxo de Caixa")
    st.markdown("Analise o volume financeiro liquidado e as transações processadas.")
    
    if not pay_filtered.empty:
        pay_filtered['mes_ano_dt'] = pay_filtered['paid_at'].dt.to_period('M').astype(str) 
        pay_filtered['mes_ano_str'] = pay_filtered['paid_at'].dt.strftime('%m/%Y')         
        
        st.markdown("#### 🎯 Visão Geral do Período")
        c1, c2, c3 = st.columns(3)
        meses_agrupados = pay_filtered.groupby('mes_ano_str')['amount'].sum()
        melhor_mes = meses_agrupados.idxmax()
        melhor_mes_val = meses_agrupados.max()
        
        # BLINDAGEM DE VALOR NULO AQUI
        ticket_medio = pay_filtered['amount'].mean()
        ticket_medio = 0 if pd.isna(ticket_medio) else ticket_medio
        metodo_top = pay_filtered.groupby('method')['amount'].sum().idxmax()
        
        c1.metric("🏆 Melhor Mês (Arrecadação)", f"{melhor_mes}", formatar_moeda(melhor_mes_val))
        c2.metric("💳 Método Predominante", f"{metodo_top.upper()}")
        c3.metric("🏷️ Ticket Médio por Parcela", formatar_moeda(ticket_medio))
        
        st.write("") 
        
        st.markdown("#### 📊 Transações por Método de Pagamento")
        metodos_qtd = pay_filtered['method'].value_counts().reset_index()
        metodos_qtd.columns = ['method', 'quantidade']
        cols_metodos = st.columns(len(metodos_qtd))
        
        for idx, row in metodos_qtd.iterrows():
            nome_metodo = str(row['method']).upper()
            qtd = row['quantidade']
            valor_total = pay_filtered[pay_filtered['method'] == row['method']]['amount'].sum()
            cols_metodos[idx].metric(label=f"🔄 {nome_metodo}", value=f"{qtd} pagamentos", delta=f"Total: {formatar_moeda(valor_total)}", delta_color="off")
        
        st.divider()
        
        st.markdown("#### 📋 Matriz de Entradas Financeiras")
        visao_selecionada = st.radio("Agrupar colunas por:", ["Credor", "Campanha", "Método de Pagamento"], horizontal=True)
        mapa_colunas = {"Credor": "creditor", "Campanha": "campaign_id", "Método de Pagamento": "method"}
        coluna_alvo = mapa_colunas[visao_selecionada]
        
        pivot_matriz = pay_filtered.pivot_table(index='mes_ano_str', columns=coluna_alvo, values='amount', aggfunc='sum', fill_value=0)
        pivot_matriz['Total Geral'] = pivot_matriz.sum(axis=1)
        
        ordem_meses = pay_filtered.sort_values('mes_ano_dt')['mes_ano_str'].unique()
        pivot_matriz = pivot_matriz.reindex(ordem_meses)
        
        st.dataframe(pivot_matriz.style.format(formatar_moeda), use_container_width=True, height=400)
                
    else:
        st.info("Nenhum dado de pagamento registrado para os filtros selecionados.")