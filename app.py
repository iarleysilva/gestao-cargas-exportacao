import streamlit as st

# ─── CONFIGURAÇÃO DA PÁGINA (OBRIGATORIAMENTE A PRIMEIRA LINHA DO STREAMLIT) ───
st.set_page_config(
    page_title="Portal de Gestão - Exportação",
    layout="wide",
    initial_sidebar_state="expanded"  # Força o menu lateral a iniciar SEMPRE aberto
)

# ─── ESTILIZAÇÃO DO CONTEÚDO (CSS OPCIONAL PARA MELHORAR O VISUAL) ───
st.markdown("""
    <style>
        .main-title {
            color: #1c3d5a;
            font-weight: bold;
            margin-bottom: 5px;
        }
        .welcome-box {
            background-color: #f8f9fa;
            border-left: 5px solid #007ebd;
            padding: 15px;
            border-radius: 4px;
            margin-bottom: 20px;
        }
    </style>
""", unsafe_allow_html=True)

# ─── CORPO DA PÁGINA HOME ───
st.markdown("<h1 class='main-title'>🚀 Portal de Gestão e Operações - Exportação</h1>", unsafe_allow_html=True)
st.markdown("---")

st.markdown("""
<div class='welcome-box'>
    <h3>Bem-vindo ao Sistema Integrado de Cargas</h3>
    <p>Utilize o menu lateral esquerdo para navegar entre os módulos operacionais disponíveis.</p>
</div>
""", unsafe_allow_html=True)

# Descrição dos módulos principais
st.markdown("### 📋 Módulos Ativos de Sistema")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    * 📊 **Módulo 5: Desempenho Turnos HT**
        * Monitoramento de tratamentos operacionais por equipe.
        * Contabilidade direta e espelhamento lógico de Ciclos (`CONCAT`) e Pallets.
    * 🪵 **Módulo 1: Demanda HT**
        * Planejamento de capacidade, consulta de faturas e volumetria por percurso.
    """)

with col2:
    st.markdown("""
    * 📦 **Módulo de Separação**
        * Avaliação antecipada de capacidade versus demanda logística (em estruturação).
    """)

st.markdown("---")
st.info("💡 **Acesso Restrito:** Os módulos utilizam sincronização em tempo real diretamente com os bancos de dados do Google Sheets.")