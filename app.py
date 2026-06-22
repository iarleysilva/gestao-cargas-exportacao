import streamlit as st

# ─── 1. CONFIGURAÇÃO DA PÁGINA (OBRIGATORIAMENTE A PRIMEIRA LINHA) ───
st.set_page_config(
    page_title="Portal de Gestão - Exportação",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── 🔑 SISTEMA DE LOGIN GLOBAL DO PORTAL ───
USUARIOS_PERMITIDOS = {
    "Iarley,planejamento": "PCO.EIHJ",
    "pco_operador": "logistica2026"
}

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    # Esconde o menu lateral inteiramente até que o login seja feito com sucesso
    st.markdown(
        """
        <style>
            [data-testid="stSidebar"] {display: none;}
        </style>
        """, 
        unsafe_allow_html=True
    )
    
    st.markdown("<h2 style='text-align: center; color: #1e3a8a; margin-top: 50px;'>🔐 Portal PCO — Controle de Acesso Geral</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #4b5563;'>Insira suas credenciais mestre para liberar os módulos operacionais do pátio.</p>", unsafe_allow_html=True)
    st.markdown("---")
    
    with st.form("login_global_portal"):
        col_u, col_p = st.columns(2)
        with col_u:
            usuario_input = st.text_input("Usuário Master:", placeholder="Ex: nome,setor").strip()
        with col_p:
            senha_input = st.text_input("Senha de Fábrica:", type="password").strip()
            
        botao_entrar = st.form_submit_button("🔑 Autenticar e Liberar Portal")
        
        if botao_entrar:
            if usuario_input in USUARIOS_PERMITIDOS and USUARIOS_PERMITIDOS[usuario_input] == senha_input:
                st.session_state["autenticado"] = True
                st.session_state["usuario_logado"] = usuario_input
                st.success("✅ Acesso autorizado!")
                st.rerun()
            else:
                st.error("❌ Credenciais incorretas. Verifique o usuário e a senha informados.")
    st.stop()  # Trava o carregamento do portal aqui caso não esteja logado
# ───────────────────────────────────────────────────────────────────────────────────

# Menu lateral liberado após o login bem-sucedido
if st.sidebar.button("🚪 Encerrar Sessão"):
    st.session_state["autenticado"] = False
    st.rerun()

st.sidebar.markdown(f"👤 **Usuário Ativo:** `{st.session_state['usuario_logado']}`")

# ─── ESTILIZAÇÃO DO CONTEÚDO (CSS PARA O LOOK PROFISSIONAL) ───
st.markdown("""
    <style>
        .main-title { color: #1e3a8a; font-weight: 800; margin-bottom: 5px; }
        .welcome-box { background-color: #f8fafc; border-left: 5px solid #1e3a8a; padding: 20px; border-radius: 6px; margin-bottom: 25px; border-right: 1px solid #e2e8f0; border-top: 1px solid #e2e8f0; border-bottom: 1px solid #e2e8f0;}
    </style>
""", unsafe_allow_html=True)

# ─── CORPO DA PÁGINA HOME ───
st.markdown("<h1 class='main-title'>🚀 Portal de Gestão e Operações - PCO</h1>", unsafe_allow_html=True)
st.markdown("---")

st.markdown(f"""
<div class='welcome-box'>
    <h3>Sincronização Integrada de Cargas Comercial — MI</h3>
    <p>Olá, <b>{st.session_state['usuario_logado']}</b>! O ecossistema está ativo e pronto. Utilize o menu lateral esquerdo para navegar entre as telas operacionais.</p>
</div>
""", unsafe_allow_html=True)

# 🔥 TERMÔMETRO VISUAL: DEMONSTRAÇÃO DO PODER DO SISTEMA EM LOGÍSTICA
st.markdown("### 📊 Termômetro de Ocupação da Fábrica (Simulação Consolidada)")
m1, m2, m3 = st.columns(3)
with m1:
    st.metric("📦 Capacidade Total Alocada", "1.240 Acessos", "Janelas Ativas")
with m2:
    st.metric("🪵 Saldo Restante em Sobras", "662 Acessos", "-15 un de Ontem", delta_color="inverse")
with m3:
    st.metric("📈 Eficiência de Separação (SLA)", "94.2%", "+2.1% no Turno")

# Barra de Progresso Real do Dia
st.markdown("**Taxa de Ocupação Crítica do Pátio (Geral):** 81%")
st.progress(0.81)
st.markdown("<br>", unsafe_allow_html=True)

st.markdown("### 📋 Estrutura de Módulos Ativos")
col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    * ⚙️ **Configurações PCO**
        * Parametrização dinâmica de capacidades e turnos operacionais.
    * 🪵 **Módulos de Demanda**
        * Planejamento técnico de volumes, cubagem e gargalos (HT, Lastras, ME, MI).
    """)

with col2:
    st.markdown("""
    * 📊 **Módulos de Capacidade**
        * Simulação de janelas de escoamento e balanceamento de pátio.
    * 🎯 **Módulos de Desempenho**
        * Dashboards de produtividade e consolidação de bipes em tempo real.
    """)

st.markdown("---")
st.info("💡 **Acesso Restrito:** Os dados são atualizados dinamicamente através da integração direta com as planilhas mestres do Google Sheets.")