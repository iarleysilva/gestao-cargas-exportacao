import streamlit as st
import pandas as pd
from src.core.data_loader import carregar_dados_lastras_novas

st.set_page_config(page_title="Demanda Separação Lastras", page_icon="📋", layout="wide")

st.markdown("<h1 style='text-align: center; color: #0F766E;'>📋 Carteira de Demanda e Fluxo de Lastras</h1>", unsafe_allow_html=True)
st.markdown("---")

# Carga do Motor de Dados Blindado v7.0
_, df_lastras = carregar_dados_lastras_novas()

if df_lastras is not None and not df_lastras.empty:
    
    # KPIs de Cabeçalho (Filtro Global)
    st.subheader("📌 Resumo Estratégico da Carteira")
    m1, m2, m3, m4 = st.columns(4)
    
    total_percursos = df_lastras['PERCURSO'].nunique()
    total_pecas = df_lastras['TOTAL_GERAL'].sum()
    total_sequenciado = df_lastras[df_lastras['STATUS'] == 'SEQUENCIADO']['TOTAL_GERAL'].sum()
    total_pendente = df_lastras[df_lastras['STATUS'] == 'NÃO SEQUENCIADO']['TOTAL_GERAL'].sum()
    
    m1.metric("Total de Percursos", f"{total_percursos} rotas")
    m2.metric("Volume Total da Carteira", f"{int(total_pecas)} peças")
    m3.metric("Volume Sequenciado (Garantido)", f"{int(total_sequenciado)} peças", delta=f"{int(total_sequenciado)} un")
    m4.metric("Carteira Pendente (PCO)", f"{int(total_pendente)} peças", delta=f"-{int(total_pendente)} un" if total_pendente > 0 else "Zerado")
    
    st.markdown("---")
    
    # Divisão por Status de Atendimento
    col_seq, col_nao_seq = st.columns(2)
    
    with col_seq:
        st.markdown("### ✅ Percursos Sequenciados")
        df_seq = df_lastras[df_lastras['STATUS'] == 'SEQUENCIADO']
        if not df_seq.empty:
            st.dataframe(
                df_seq[['PERCURSO', 'CANAL', 'tipo_unitizacao', 'TOTAL_GERAL', 'TURNO_ALOCADO', 'MOTIVO']],
                column_config={
                    "PERCURSO": "Roteiro/Percurso", "CANAL": "Canal", "tipo_unitizacao": "Unitização",
                    "TOTAL_GERAL": "Peças", "TURNO_ALOCADO": "Turno", "MOTIVO": "Prioridade"
                }, use_container_width=True, hide_index=True
            )
        else:
            st.info("Nenhuma carga sequenciada para este horizonte.")
            
    with col_nao_seq:
        st.markdown("### ⏳ Carteira Não Sequenciada (Aguardando PCO)")
        df_ns = df_lastras[df_lastras['STATUS'] == 'NÃO SEQUENCIADO']
        if not df_ns.empty:
            st.dataframe(
                df_ns[['PERCURSO', 'CANAL', 'tipo_unitizacao', 'TOTAL_GERAL', 'MERCADO']],
                column_config={
                    "PERCURSO": "Roteiro/Percurso", "CANAL": "Canal", 
                    "tipo_unitizacao": "Unitização", "TOTAL_GERAL": "Peças", "MERCADO": "Mkt"
                }, use_container_width=True, hide_index=True
            )
        else:
            st.success("Parabéns! Toda a carteira de lastras foi sequenciada pelo PCO. 🚀")
else:
    st.warning("Nenhum registro encontrado na aba Sequenciamento_Lastras.")