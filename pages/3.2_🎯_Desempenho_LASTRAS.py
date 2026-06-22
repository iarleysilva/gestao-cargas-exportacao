import streamlit as st
import pandas as pd
from datetime import timedelta, datetime, time
import zoneinfo

# ─── BLOCO DE SEGURANÇA DE CAMINHOS ROBUSTO ───
import sys
from pathlib import Path
raiz = Path(__file__).resolve().parents[2]
if str(raiz) not in sys.path:
    sys.path.append(str(raiz))
# ──────────────────────────────────────────────

from src.core.data_loader import carregar_dados_lastras, carregar_dados_lastras_antigo

st.set_page_config(page_title="Desempenho Lastras", layout="wide")

st.title("🎯 Dashboard de Desempenho Operacional Geral")
st.write("Análise consolidada de produtividade e bipes gerados por cada turno.")

# Carrega os dados usando a nova arquitetura unificada
df_realizado, df_tec = carregar_dados_lastras_antigo()

if df_realizado.empty:
    st.error("❌ Erro ao carregar o histórico de bipes realizados dos turnos.")
else:
    # Sidebar de filtros específicos para esta página
    st.sidebar.header("Filtros de Desempenho")
    
    # Filtro de Turno Realizador
    turnos_ids = sorted(df_realizado['TURNO_ID'].unique())
    turno_sel = st.sidebar.multiselect("Filtrar Turno que Realizou", turnos_ids, default=turnos_ids)
    
    df_filtrado = df_realizado[df_realizado['TURNO_ID'].isin(turno_sel)]

    # KPIs de Performance
    st.markdown("### 🚀 Métricas de Execução dos Turnos")
    m1, m2, m3 = st.columns(3)
    
    total_mi = df_filtrado['MI_VAL'].sum()
    total_me = df_filtrado['ME_VAL'].sum()
    total_gatilhos = df_filtrado['GATILHO'].sum()
    
    m1.metric("📥 Total MI (Mercado Interno)", f"{int(total_mi)} bipes")
    m2.metric("🚢 Total ME (Mercado Externo)", f"{int(total_me)} bipes")
    m3.metric("⚡ Total Acessos / Gatilhos", f"{int(total_gatilhos)} bipes")

    # Gráfico de Linha / Evolução por data de referência
    st.write("---")
    st.markdown("### 📈 Tendência de Produtividade Diária por Turno")
    
    df_linha = df_filtrado.groupby(['DATA_REF', 'TURNO_ID'])[['MI_VAL', 'ME_VAL']].sum().reset_index()
    df_linha['TOTAL_BIPES'] = df_linha['MI_VAL'] + df_linha['ME_VAL']
    
    fig_linha = px.line(
        df_linha,
        x='DATA_REF',
        y='TOTAL_BIPES',
        color='TURNO_ID',
        title="Evolução de Bipes Diários (MI + ME)",
        labels={'DATA_REF': 'Data', 'TOTAL_BIPES': 'Volume Total', 'TURNO_ID': 'Turno'}
    )
    st.plotly_chart(fig_linha, use_container_width=True)

    # Tabela com ranking de percursos mais ativos
    st.write("---")
    st.markdown("### 🏆 Top Percursos com Maior Volume de Operação")
    
    df_ranking = df_filtrado.groupby('PERCURSO_LIMP')[['MI_VAL', 'ME_VAL', 'GATILHO']].sum().reset_index()
    df_ranking['TOTAL'] = df_ranking['MI_VAL'] + df_ranking['ME_VAL']
    df_ranking = df_ranking.sort_values(by='TOTAL', ascending=False).head(15)
    
    st.dataframe(df_ranking, use_container_width=True)