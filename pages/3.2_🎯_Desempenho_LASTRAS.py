import streamlit as st
import pandas as pd
from src.core.data_loader import carregar_dados_lastras_novas

st.set_page_config(page_title="Desempenho Lastras", page_icon="🎯", layout="wide")

st.markdown("<h1 style='text-align: center; color: #0F766E;'>🎯 Analisador de Complexidade e Mix de Formatos — Lastras</h1>", unsafe_allow_html=True)
st.markdown("---")

_, df_lastras = carregar_dados_lastras_novas()

if df_lastras is not None and not df_lastras.empty:
    
    # Tratamentos Estatísticos de Complexidade
    df_lastras['RESTO_MAQUINA'] = df_lastras.apply(lambda r: int(r['120X270'] % 20) if r['tipo_unitizacao'] == 'CAIXOTE' else 0, axis=1)
    df_lastras['RESTO_PAPELAO'] = df_lastras.apply(lambda r: int(r['160X160'] % 23) if r['tipo_unitizacao'] == 'CAIXOTE' else 0, axis=1)
    df_lastras['TOTAL_FRACOES'] = df_lastras['RESTO_MAQUINA'] + df_lastras['RESTO_PAPELAO']
    
    st.subheader("📊 Diagnóstico Técnico de Esforço Invisível (Carteira Ativa)")
    
    # Mix de Formatos Global
    tot_maquina = df_lastras['120X270'].sum()
    tot_papelao = df_lastras['160X160'].sum()
    tot_itens_acessos = df_lastras['qtd_itens'].sum()
    tot_fracoes_un = df_lastras['TOTAL_FRACOES'].sum()
    
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Mix Formato Máquina", f"{int(tot_maquina)} pçs", "120x270 (Pesado)")
    k2.metric("Mix Formato Papelão", f"{int(tot_papelao)} pçs", "160x160 (Leve)")
    k3.metric("Fração Residual Gerada", f"{int(tot_fracoes_un)} peças soltas", "Esforço de Estoque")
    k4.metric("Índice de Acessos/Hora", f"{int(tot_itens_acessos)} itens", "Grau de Complexidade")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Tabela Analítica de Perfis de Cubagem
    st.subheader("📋 Auditoria de Cubagem e Esforço por Roteiro")
    
    df_lastras['MIX_MÁQUINA_%'] = ((df_lastras['120X270'] / df_lastras['TOTAL_GERAL'].replace(0, 1)) * 100).astype(int)
    
    st.dataframe(
        df_lastras[['PERCURSO', 'CANAL', 'tipo_unitizacao', 'TOTAL_GERAL', 'MIX_MÁQUINA_%', 'TOTAL_FRACOES', 'qtd_itens', 'STATUS']].rename(columns={
            'PERCURSO': 'Percurso', 'CANAL': 'Canal/Operação', 'tipo_unitizacao': 'Tipo Unitização',
            'TOTAL_GERAL': 'Total Peças', 'MIX_MÁQUINA_%': '% Mix Máquina', 'TOTAL_FRACOES': 'Peças Fração',
            'qtd_itens': 'Dificuldade (Itens)', 'STATUS': 'Status PCO'
        }), use_container_width=True, hide_index=True
    )
else:
    st.error("Nenhum dado integrado para gerar a matriz de Desempenho Lastras.")