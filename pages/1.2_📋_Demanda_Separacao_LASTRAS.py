import streamlit as st
import pandas as pd
import plotly.express as px
from src.core.data_loader import carregar_dados_lastras_antigo

st.set_page_config(page_title="Capacidade de Lastras", layout="wide")

st.title("🪵 Planejamento de Demanda vs Capacidade (Lastras)")
st.write("Análise técnica de unitização e caixotes baseada no BI mestre antigo.")

# Carrega os dados usando a nova arquitetura unificada
df_realizado, df_tec = carregar_dados_lastras_antigo()

if df_tec.empty:
    st.warning("⚠️ Não foi possível carregar a base de planejamento de lastras (Aba LASTRAS vazia ou inacessível).")
else:
    # Sidebar de filtros específicos para esta página
    st.sidebar.header("Filtros do Planejamento")
    
    # Filtro de datas com base no sequenciamento
    datas_disponiveis = sorted(df_tec['DATA_SEQ'].dropna().unique())
    if datas_disponiveis:
        data_sel = st.sidebar.selectbox("Selecione a Data de Sequenciamento", datas_disponiveis, format_func=lambda x: x.strftime('%d/%M/%Y'))
        df_view = df_tec[df_tec['DATA_SEQ'] == data_sel]
    else:
        df_view = df_tec.copy()
        
    turnos_disponiveis = ["Todos"] + list(df_view['TURNO_CHAVE'].unique())
    turno_sel = st.sidebar.selectbox("Filtrar por Turno (Planejado)", turnos_disponiveis)
    
    if turno_sel != "Todos":
        df_view = df_view[df_view['TURNO_CHAVE'] == turno_sel]

    # Indicadores principais de Lastras
    st.markdown("### 📊 Indicadores Gerais do Período Selecionado")
    c1, c2, c3 = st.columns(3)
    
    total_120 = df_view['120X270'].sum()
    total_160 = df_view['160 X 160'].sum()
    total_pc = df_view['PC'].sum()
    
    c1.metric("📐 Total Formato 120X270", f"{int(total_120)} un")
    c2.metric("🟩 Total Formato 160 X 160", f"{int(total_160)} un")
    c3.metric("📦 Total de Caixotes (PC)", f"{int(total_pc)} cx")

    # Gráficos de distribuição por Turno
    st.write("---")
    st.markdown("### 🏢 Distribuição por Turno Alocado")
    
    df_turno_resumo = df_view.groupby('TURNO_CHAVE')[['120X270', '160 X 160', 'PC']].sum().reset_index()
    
    fig = px.bar(
        df_turno_resumo, 
        x='TURNO_CHAVE', 
        y=['120X270', '160 X 160'],
        title="Volume de Lastras por Turno",
        labels={'value': 'Quantidade', 'TURNO_CHAVE': 'Turno', 'variable': 'Formato'},
        barmode='group'
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Detalhamento em tabela
    st.write("---")
    st.markdown("### 📄 Listagem Analítica do Planejamento")
    st.dataframe(df_view, use_container_width=True)