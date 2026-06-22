import streamlit as st

st.set_page_config(page_title="Portal PCO", layout="wide")

# 🔑 USUÁRIOS E SENHAS DA VERSÃO OPERACIONAL
USUARIOS_PERMITIDOS = {
    "Iarley,planejamento": "PCO,EIHJ",
    "pco_operador": "logistica2026"
}

# Inicializa o estado de autenticação
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

# Tela de Bloqueio antes de entrar no sistema
if not st.session_state["autenticado"]:
    st.markdown("<h2 style='text-align: center; color: #1e3a8a;'>🔐 Portal PCO — Controle de Acesso</h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    with st.form("form_login"):
        usuario = st.text_input("Usuário:").strip()
        senha = st.text_input("Senha:", type="password").strip()
        botao = st.form_submit_button("Entrar no Sistema")
        
        if botao:
            if usuario in USUARIOS_PERMITIDOS and USUARIOS_PERMITIDOS[usuario] == senha:
                st.session_state["autenticado"] = True
                st.session_state["usuario_logado"] = usuario
                st.success("Acesso liberado!")
                st.rerun()
            else:
                st.error("Usuário ou Senha inválidos.")
    st.stop()

# Se o usuário estiver autenticado, mostra as boas-vindas e instrui a usar o menu lateral
st.sidebar.markdown(f"👤 Conectado: `{st.session_state['usuario_logado']}`")
if st.sidebar.button("🚪 Sair"):
    st.session_state["autenticado"] = False
    st.rerun()

st.success(f"Olá, {st.session_state['usuario_logado']}! O sistema está liberado.")
st.markdown("### 👈 Utilize o menu lateral para acessar a tela de **Acompanhamento de Capacidade — MI**.")