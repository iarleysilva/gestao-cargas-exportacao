import streamlit as st
import pandas as pd
from src.core.data_loader import carregar_matriz_capacidade

st.set_page_config(page_title="Painel de Controle PCO", layout="wide")

st.title("⚙️ Painel de Controle & Parametrização Dinâmica")
st.write("Configuração restrita de capacidades operacionais e limites de mix.")
st.markdown("---")

# ─── 🔐 SISTEMA DE AUTENTICAÇÃO COM OCULTAÇÃO TOTAL ───
st.sidebar.header("🔐 Acesso Restrito")
senha_pco = st.sidebar.text_input("Digite a senha master PCO:", type="password")

# Defina a sua senha de preferência aqui
SENHA_CORRETA = "pco123" 

# Verifica se a senha está correta para liberar o estado da sessão
if senha_pco != SENHA_CORRETA:
    if senha_pco:
        st.sidebar.error("❌ Senha incorreta!")
    
    # Mensagem amigável de bloqueio
    st.warning("🔒 Os valores e métricas de capacidade estão ocultos para sua segurança. "
               "Insira a senha master do PCO na barra lateral para revelar e editar os dados.")
    
    # Interrompe a execução aqui. Ninguém vê nada abaixo desta linha!
    st.stop()

# ─── 🔓 SE PASSAREM DA SENHA, O SISTEMA PROCESSA E REVELA O CONTEÚDO ───
st.sidebar.success("🔓 Acesso Liberado! Modo PCO Ativo.")

# Carrega os dados mais recentes do Sheets (Matriz de capacidade viva)
df_pco, mapa_metricas = carregar_matriz_capacidade()

if df_pco is None or df_pco.empty:
    st.error("⚠️ Não foi possível carregar a matriz mestre de capacidades.")
    st.stop()

# Links de Destino para o Cadastro Oficial
ID_PLANILHA = "1BYnAn1HYGkrJgCC-L0TCKVepLt3do6zqCPJvYhzcq_Y"
link_sheets = f"https://docs.google.com/spreadsheets/d/{ID_PLANILHA}/edit#gid=1318835351"

st.info("💡 **Modo de Operação:** Os valores abaixo foram revelados com sucesso. "
        "Use os simuladores locais para analisar impactos ou clique no botão abaixo para aplicar o `OVERRIDE_VALOR` definitivo na planilha mestre.")

st.markdown(
    f'<a href="{link_sheets}" target="_blank" style="text-decoration:none;">'
    f'<div style="text-align:center; background-color:#1E3A8A; color:white; padding:12px; border-radius:6px; font-weight:bold; margin-bottom:25px;">'
    f'🟢 ABRIR PLANILHA MESTRE DE PARAMETRIZAÇÃO (CADASTRO OFICIAL)'
    f'</div></a>', 
    unsafe_allow_html=True
)

# Criando as Abas Operacionais apenas para quem logou
tab_me, tab_mi, tab_ht = st.tabs(["🚢 Mercado Externo (ME)", "📥 Mercado Interno (MI)", "🪵 Estufas (HT)"])

# 🌐 ABA ME (MERCADO EXTERNO)
with tab_me:
    st.subheader("📊 Métricas de Escoamento - ME")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### 🕒 Turno 1")
        op_t1 = st.number_input("Operadores T1 (ME):", value=int(mapa_metricas.get(('ME', '1', 'OPERADORES', 'QTD'), 2)), step=1)
        cap_t1 = st.number_input("Capacidade/OP T1 (ME):", value=int(mapa_metricas.get(('ME', '1', 'CAPACIDADE', 'POR_OPERADOR'), 130)), step=5)
        st.metric("Capacidade Total T1", f"{op_t1 * cap_t1} acessos")
        
    with col2:
        st.markdown("#### 🦅 Turno 2")
        op_t2 = st.number_input("Operadores T2 (ME):", value=int(mapa_metricas.get(('ME', '2', 'OPERADORES', 'QTD'), 2)), step=1)
        cap_t2 = st.number_input("Capacidade/OP T2 (ME):", value=int(mapa_metricas.get(('ME', '2', 'CAPACIDADE', 'POR_OPERADOR'), 130)), step=5)
        st.metric("Capacidade Total T2", f"{op_t2 * cap_t2} acessos")
        
    with col3:
        st.markdown("#### 🦉 Turno 3")
        op_t3 = st.number_input("Operadores T3 (ME):", value=int(mapa_metricas.get(('ME', '3', 'OPERADORES', 'QTD'), 0)), step=1)
        cap_t3 = st.number_input("Capacidade/OP T3 (ME):", value=int(mapa_metricas.get(('ME', '3', 'CAPACIDADE', 'POR_OPERADOR'), 0)), step=5)
        st.metric("Capacidade Total T3", f"{op_t3 * cap_t3} acessos")

# 🌐 ABA MI (MERCADO INTERNO)
with tab_mi:
    st.subheader("📊 Métricas de Escoamento - MI")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### 🕒 Turno 1")
        op_mi_t1 = st.number_input("Operadores T1 (MI):", value=int(mapa_metricas.get(('MI', '1', 'OPERADORES', 'QTD'), 4)), step=1)
        cap_mi_t1 = st.number_input("Capacidade/OP T1 (MI):", value=int(mapa_metricas.get(('MI', '1', 'CAPACIDADE', 'POR_OPERADOR'), 85)), step=5)
        st.metric("Capacidade Total T1 MI", f"{op_mi_t1 * cap_mi_t1} acessos")
        
    with col2:
        st.markdown("#### 🦅 Turno 2")
        op_mi_t2 = st.number_input("Operadores T2 (MI):", value=int(mapa_metricas.get(('MI', '2', 'OPERADORES', 'QTD'), 4)), step=1)
        cap_mi_t2 = st.number_input("Capacidade/OP T2 (MI):", value=int(mapa_metricas.get(('MI', '2', 'CAPACIDADE', 'POR_OPERADOR'), 85)), step=5)
        st.metric("Capacidade Total T2 MI", f"{op_mi_t2 * cap_mi_t2} acessos")
        
    with col3:
        st.markdown("#### 🦉 Turno 3")
        op_mi_t3 = st.number_input("Operadores T3 (MI):", value=int(mapa_metricas.get(('MI', '3', 'OPERADORES', 'QTD'), 6)), step=1)
        cap_mi_t3 = st.number_input("Capacidade/OP T3 (MI):", value=int(mapa_metricas.get(('MI', '3', 'CAPACIDADE', 'POR_OPERADOR'), 85)), step=5)
        st.metric("Capacidade Total T3 MI", f"{op_mi_t3 * cap_mi_t3} acessos")

# 🌐 ABA HT (ESTUFAS)
with tab_ht:
    st.subheader("🪵 Restrições de Fornadas e Estrados HT")
    cc1, cc2 = st.columns(2)
    with cc1:
        ciclos_ht = st.number_input("Ciclos por Turno (Fornadas):", value=int(mapa_metricas.get(('HT', '1', 'CICLOS', 'POR_TURNO'), 4)), step=1)
    with cc2:
        rend_ht = st.number_input("Rendimento por Ciclo (Pallets):", value=int(mapa_metricas.get(('HT', '1', 'RENDIMENTO', 'PLTS_POR_CICLO'), 27)), step=1)
    st.metric("Capacidade Teórica HT", f"{ciclos_ht * rend_ht} Pallets por Turno")

# ─── INSPEÇÃO ANALÍTICA COMPLETA NO RODAPÉ ───
st.markdown("---")
st.markdown("### 🔍 Matriz de Configuração Bruta (Planilha)")
st.dataframe(df_pco, use_container_width=True, hide_index=True)