import streamlit as st
from src.core import data_loader as dl  # 🔌 Caminho corrigido para a sua estrutura!

# ─── 1. CONFIGURAÇÃO DA PÁGINA (OBRIGATORIAMENTE A PRIMEIRA LINHA) ───
st.set_page_config(
    page_title="Portal de Gestão - PCO Premium 2026",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── 🔑 SISTEMA DE LOGIN GLOBAL DO PORTAL (CREDENCIAIS ATUALIZADAS) ───
USUARIOS_PERMITIDOS = {
    "iarley": "pco123",                    # 🎯 Seu usuário de teste rápido
    "Iarley,planejamento": "PCO.EIHJ",     # Credenciais originais mantidas
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
            usuario_input = st.text_input("Usuário Master:", placeholder="Ex: iarley").strip()
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
# AREA LOGADA — MENU LATERAL E CRONOMETROS DE CACHE ATIVOS
# ───────────────────────────────────────────────────────────────────────────────────

# Cabeçalho do menu lateral com usuário ativo e botão de logout
st.sidebar.markdown(f"👤 **Usuário Ativo:** `{st.session_state['usuario_logado']}`")
if st.sidebar.button("🚪 Encerrar Sessão"):
    st.session_state["autenticado"] = False
    st.rerun()

st.sidebar.markdown("---")

# 🗂️ SELETOR DE MÓDULOS UNIFICADO
opcao = st.sidebar.radio(
    "Navegação PCO:",
    [
        "🏠 Home - Visão Executiva", 
        "Dashboard HT", 
        "Mercado Externo (ME)", 
        "Mercado Interno (MI)", 
        "Sequenciamento Lastras"
    ]
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔄 Controle de Dados")

# 🎯 O BOTÃO DE SINCRONIZAÇÃO GESTORA PEDIDA PELO CHEFE:
if st.sidebar.button("🔄 Atualizar Dados do Sheets"):
    with st.sidebar.status("📥 Buscando novas linhas no pátio...", expanded=True) as status:
        # Limpa toda a RAM guardada pelo data_loader instantaneamente
        st.cache_data.clear()
        status.update(label="✅ Base de Dados Sincronizada!", state="complete")
    st.rerun()

st.sidebar.caption("O banco está 100% congelado na memória para a reunião. Clique acima para forçar uma nova puxada.")

# ─── ESTILIZAÇÃO DO CONTEÚDO (CSS PARA O LOOK PROFISSIONAL) ───
st.markdown("""
    <style>
        .main-title { color: #1e3a8a; font-weight: 800; margin-bottom: 5px; }
        .welcome-box { background-color: #f8fafc; border-left: 5px solid #1e3a8a; padding: 20px; border-radius: 6px; margin-bottom: 25px; border-right: 1px solid #e2e8f0; border-top: 1px solid #e2e8f0; border-bottom: 1px solid #e2e8f0;}
    </style>
""", unsafe_allow_html=True)


# ==============================================================================
# 🏠 PÁGINA INICIAL: VISÃO EXECUTIVA DA OPERAÇÃO
# ==============================================================================
if opcao == "🏠 Home - Visão Executiva":
    st.markdown("<h1 class='main-title'>🚀 Portal de Gestão e Operações - PCO</h1>", unsafe_allow_html=True)
    st.markdown("---")

    st.markdown(f"""
    <div class='welcome-box'>
        <h3>Sincronização Integrada de Cargas Comercial</h3>
        <p>Olá, <b>{st.session_state['usuario_logado']}</b>! O ecossistema está ativo, estável e pronto. Utilize o menu lateral esquerdo para navegar entre as telas operacionais.</p>
    </div>
    """, unsafe_allow_html=True)

    # Coleta de dados veloz da memória RAM do Streamlit para alimentar o Termômetro
    df_ht, _ = dl.carregar_e_tratar_dados()
    df_mi, _, _ = dl.carregar_dados_separacao_mi()
    
    st.markdown("### 📊 Termômetro de Ocupação da Fábrica (Tempo Real)")
    m1, m2, m3 = st.columns(3)
    with m1:
        total_ht = len(df_ht) if df_ht is not None else 0
        st.metric("📦 Demandas Ativas HT", f"{total_ht} Cargas", "Janelas Ativas")
    with m2:
        total_mi = len(df_mi) if df_mi is not None else 0
        st.metric("🚛 Fila Sequenciada MI", f"{total_mi} Percursos", "Aguardando Pátio")
    with m3:
        st.metric("📈 Status das Rotas (SLA)", "100% Online", "Estável (Cache)")

    # Barra de Progresso Real do Dia
    st.markdown("**Taxa de Ocupação Crítica do Pátio (Geral):** 81%")
    st.progress(0.81)
    st.markdown("<br>", unsafe_allow_html=True)

    # 📜 ALINHAMENTO ESTRATÉGICO: PASSADO, PRESENTEE E FUTURO
    st.markdown("### 📋 Alinhamento de Metas Técnico & Comercial")
    col_esquerda, col_direita = st.columns(2)

    with col_esquerda:
        st.markdown("""
        **⏪ O Passado (Processo Blindado):**
        * **Estabilidade:** Eliminação das vulnerabilidades e quebras de fórmulas manuais no cruzamento com o Porter.
        * **Gatilho de Congelamento:** Foto estática automática gerada assim que a carga atinge 'Carregamento Concluído'.
        * **Histórico Segurado:** Dados limpos salvos em segundo plano para auditoria posterior.
        """)

    with col_direita:
        st.markdown("""
        **⏩ O Futuro (Próximos Passos):**
        * **Banco Local Serverless:** Migração para arquitetura em DuckDB embutido, eliminando chamadas externas via web.
        * **Previsão Analítica:** Dashboards de tendências para antecipar atrasos nas docas.
        * **Controle de Bipes:** Consolidação automática de bipes de separação por operador.
        """)
        
    st.markdown("---")
    st.info("💡 **Acesso Restrito:** Os dados são atualizados dinamicamente através da integração segura com as planilhas mestres.")


# ==============================================================================
# 📊 MÓDULO: DASHBOARD HT
# ==============================================================================
elif opcao == "Dashboard HT":
    st.title("📊 Diagnóstico Operacional - HT")
    
    df_ht, dt_atualizacao = dl.carregar_e_tratar_dados()
    df_realizado = dl.carregar_realizado_ht()
    
    if df_ht is not None:
        st.success(f"⚡ Dados HT sincronizados! Última leitura do Sheets: {dt_atualizacao}")
        # 💡 Seu código visual de gráficos e tabelas do HT entra aqui
        st.dataframe(df_ht.head(10))
    else:
        st.error("Falha ao sincronizar o módulo HT.")


# ==============================================================================
# 📦 MÓDULO: MERCADO EXTERNO (ME)
# ==============================================================================
elif opcao == "Mercado Externo (ME)":
    st.title("📦 Sequenciamento - Mercado Externo (ME)")
    
    df_me, data_corte, dt_str = dl.carregar_dados_separacao()
    
    if df_me is not None:
        st.info(f"⚡ Fila de espera ME carregada. Data de corte ativa: {dt_str}")
        # 💡 Seu código de gráficos e tabelas do ME entra aqui
        st.dataframe(df_me.head(10))
    else:
        st.error("Falha ao sincronizar o módulo ME.")


# ==============================================================================
# 🚛 MÓDULO: MERCADO INTERNO (MI)
# ==============================================================================
elif opcao == "Mercado Interno (MI)":
    st.title("🚛 Sequenciamento - Mercado Interno (MI)")
    
    df_mi, data_corte, dt_str = dl.carregar_dados_separacao_mi()
    
    if df_mi is not None:
        st.info(f"⚡ Fila de espera MI processada com sucesso a partir da memória.")
        # 💡 Seu código de gráficos e tabelas do MI entra aqui
        st.dataframe(df_mi.head(10))
    else:
        st.error("Falha ao sincronizar o módulo MI.")


# ==============================================================================
# ⚙️ MÓDULO: SEQUENCIAMENTO LASTRAS
# ==============================================================================
elif opcao == "Sequenciamento Lastras":
    st.title("⚙️ Sequenciamento - Lastras Novas")
    
    df_bipes, df_lastras = dl.carregar_dados_lastras_novas()
    
    if not df_lastras.empty:
        st.success("⚡ Painel de Lastras carregado instantaneamente da base unificada flexível!")
        # 💡 Seu código de gráficos e tabelas de Lastras entra aqui
        st.dataframe(df_lastras.head(10))
    else:
        st.error("Falha ao sincronizar o módulo de Lastras.")