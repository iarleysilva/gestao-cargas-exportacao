import streamlit as st

# ─── 1. CONFIGURAÇÃO DA PÁGINA ───
st.set_page_config(
    page_title="Módulo Lastras - Em Manutenção",
    layout="wide"
)

# ─── 2. TRAVA DE SEGURANÇA GLOBAL (LOGIN) ───
if "autenticado" not in st.session_state or not st.session_state["autenticado"]:
    st.warning("⚠️ Por favor, faça o login na página inicial antes de acessar este módulo.")
    st.stop()

# ─── 3. TELA DE AVISO DE MANUTENÇÃO PROFISSIONAL ───
st.title("🪵 Módulo: Demanda Separação — LASTRAS")
st.markdown("---")

# Caixa de Alerta Estilizada
st.warning("### 🛠️ Módulo em Manutenção Técnica")

st.markdown("""
<div style="background-color: #fffbeb; border-left: 5px solid #d97706; padding: 20px; border-radius: 6px; margin-bottom: 25px; border-right: 1px solid #fef3c7; border-top: 1px solid #fef3c7; border-bottom: 1px solid #fef3c7;">
    <h4 style="color: #b45309; margin-top: 0;">⚙️ Engenharia de Dados PCO em Andamento</h4>
    <p style="color: #78350f;">Este módulo está passando por uma calibração nas regras de cubagem, parametrização de lastras e acoplamento com a esteira contínua.</p>
    <hr style="border-top: 1px solid #fcd34d;">
    <p style="font-size: 0.9rem; color: #78350f; margin-bottom: 0;">
        👤 <b>Responsável Técnico:</b> Iarley (Planejamento / PCO)<br>
        📅 <b>Previsão de Liberação:</b> Próxima Janela de Homologação
    </p>
</div>
""", unsafe_allow_html=True)

# Um loading visual discreto para dar a cara de sistema trabalhando no background
with st.spinner("Sincronizando novas chaves de dados com as tabelas mestres..."):
    st.info("💡 **Nota para a Operação:** Os demais módulos de Demanda (HT, ME, MI) e as telas de Capacidade continuam operando normalmente com dados em tempo real.")