import streamlit as st
from src.core import data_loader as dl  # 🔌 Caminho unificado do motor de dados
import pandas as pd
from datetime import datetime, time
import zoneinfo

# ─── 1. CONFIGURAÇÃO DA PÁGINA (OBRIGATORIAMENTE A PRIMEIRA LINHA) ───
st.set_page_config(
    page_title="Portal de Gestão - PCO Premium 2026",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Relógio Operacional Oficial de Brasília
fuso_br = zoneinfo.ZoneInfo("America/Sao_Paulo")
agora_br = datetime.now(fuso_br)
hoje_br = agora_br.date()
hora_atual = agora_br.time()

# ─── 🔑 SISTEMA DE LOGIN GLOBAL DO PORTAL ───
USUARIOS_PERMITIDOS = {
    "iarley": "pco123",                    # 🎯 Usuário master de teste rápido
    "Iarley,planejamento": "PCO.EIHJ",     # Credenciais originais mantidas
    "pco_operador": "logistica2026"
}

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    # Esconde o menu lateral inteiramente até que o login seja feito com sucesso
    st.markdown("<style>[data-testid='stSidebar'] {display: none;}</style>", unsafe_allow_html=True)
    
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
    st.stop()

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

if st.sidebar.button("🔄 Atualizar Dados do Sheets"):
    with st.sidebar.status("📥 Buscando novas linhas no pátio...", expanded=True) as status:
        st.cache_data.clear()
        status.update(label="✅ Base de Dados Sincronizada!", state="complete")
    st.rerun()

st.sidebar.caption("O banco está 100% congelado na memória para a reunião. Clique acima para forçar uma nova puxada.")

# ─── ESTILIZAÇÃO DO CONTEÚDO (CSS PADRONIZADO DO PORTAL) ───
st.markdown("""
    <style>
        .main-title { color: #1e3a8a; font-weight: 800; margin-bottom: 5px; }
        .welcome-box { background-color: #f8fafc; border-left: 5px solid #1e3a8a; padding: 18px; border-radius: 6px; margin-bottom: 25px; border-right: 1px solid #e2e8f0; border-top: 1px solid #e2e8f0; border-bottom: 1px solid #e2e8f0;}
        .section-header { color: #334155; font-weight: 700; margin-top: 25px; margin-bottom: 15px; border-bottom: 2px solid #e2e8f0; padding-bottom: 5px; }
    </style>
""", unsafe_allow_html=True)

# Puxada global de dados na memória RAM para alimentar as inteligências cruzadas
df_ht, _ = dl.carregar_e_tratar_dados()
df_realizado_ht = dl.carregar_realizado_ht(ano_selecionado=str(agora_br.year))
df_me, _, _ = dl.carregar_dados_separacao()
df_mi, _, _ = dl.carregar_dados_separacao_mi()
df_bipes, df_lastras = dl.carregar_dados_lastras_novas()
df_execucao = dl.carregar_execucao_turnos()

if isinstance(df_execucao, tuple):
    df_execucao = df_execucao[0]

# ==============================================================================
# 🏠 PÁGINA INICIAL: COCKPIT EXECUTIVO DA OPERAÇÃO
# ==============================================================================
if opcao == "🏠 Home - Visão Executiva":
    st.markdown("<h1 class='main-title'>🚀 Portal de Gestão e Operações - PCO</h1>", unsafe_allow_html=True)
    st.markdown("---")

    st.markdown(f"""
    <div class='welcome-box'>
        <h3>Painel de Controle Central Integrado</h3>
        <p>Olá, <b>{st.session_state['usuario_logado']}</b>! Abaixo está o diagnóstico em tempo real das frentes de trabalho. O monitoramento de SLA e volumetria está unificado e calibrado para 2026.</p>
    </div>
    """, unsafe_allow_html=True)

    # ─────────────────────────────────────────────────────────────────
    # BLOCO 1: MONITOR DE SLA OPERACIONAL (VISÃO DE TURNOS CORRIGIDA)
    # ─────────────────────────────────────────────────────────────────
    st.markdown("<div class='section-header'>⏱️ Monitor de SLA Operacional (Visão de Turnos)</div>", unsafe_allow_html=True)
    
    # 🪵 1. CAPTURA SEPARADA E ISOLADA DO REALIZADO HT (CICLOS DO DIA)
    df_real_hoje_ht = df_realizado_ht[df_realizado_ht['DATA_PROD'].dt.date == hoje_br].copy() if df_realizado_ht is not None else pd.DataFrame()
    if not df_real_hoje_ht.empty:
        df_real_hoje_ht['TURNO_LIMPO'] = df_real_hoje_ht['TURNO'].astype(str).str.replace(" ", "", regex=False).str.upper()
        ht_t1_bipes = df_real_hoje_ht[df_real_hoje_ht['TURNO_LIMPO'] == "TURNOI"]['PALLETS'].sum()
        ht_t2_bipes = df_real_hoje_ht[df_real_hoje_ht['TURNO_LIMPO'] == "TURNOII"]['PALLETS'].sum()
        ht_t3_bipes = df_real_hoje_ht[df_real_hoje_ht['TURNO_LIMPO'] == "TURNOIII"]['PALLETS'].sum()
    else:
        ht_t1_bipes, ht_t2_bipes, ht_t3_bipes = 0, 0, 0

    # 📥 2. CAPTURA SEPARADA E ISOLADA DO REALIZADO MERCADO INTERNO (MI)
    if df_mi is not None and df_execucao is not None:
        df_mi['PERCURSO'] = df_mi['PERCURSO'].astype(str).str.strip().str.replace('.0', '', regex=False)
        df_execucao['PERCURSO'] = df_execucao['PERCURSO'].astype(str).str.strip().str.replace('.0', '', regex=False)
        df_mi_hoje_bipado = pd.merge(df_mi[df_mi['DT_SEQUENCIADO'].dt.date == hoje_br], df_execucao, on='PERCURSO', how='inner')
        
        df_mi_hoje_bipado['TOTAL_CALCULADO'] = pd.to_numeric(df_mi_hoje_bipado['CXS'], errors='coerce').fillna(0) + pd.to_numeric(df_mi_hoje_bipado['PLS'], errors='coerce').fillna(0)
        mi_t1_bipes = df_mi_hoje_bipado[df_mi_hoje_bipado['TURNO_ALOCADO'].astype(str).str.contains('1', na=False)]['TOTAL_CALCULADO'].sum()
        mi_t2_bipes = df_mi_hoje_bipado[df_mi_hoje_bipado['TURNO_ALOCADO'].astype(str).str.contains('2', na=False)]['TOTAL_CALCULADO'].sum()
        mi_t3_bipes = df_mi_hoje_bipado[df_mi_hoje_bipado['TURNO_ALOCADO'].astype(str).str.contains('3', na=False)]['TOTAL_CALCULADO'].sum()
    else:
        mi_t1_bipes, mi_t2_bipes, mi_t3_bipes = 0, 0, 0

    # 🚢 3. CAPTURA SEPARADA E ISOLADA DO REALIZADO MERCADO EXTERNO (ME)
    if df_me is not None and df_execucao is not None:
        df_me['PERCURSO'] = df_me['PERCURSO'].astype(str).str.strip().str.replace('.0', '', regex=False)
        df_me_hoje_bipado = pd.merge(df_me[df_me['DT_SEQUENCIADO'].dt.date == hoje_br], df_execucao, on='PERCURSO', how='inner')
        me_t1_bipes = df_me_hoje_bipado[df_me_hoje_bipado['TURNO_ALOCADO'].astype(str).str.contains('1', na=False)]['VOLUME_TOTAL'].sum()
        me_t2_bipes = df_me_hoje_bipado[df_me_hoje_bipado['TURNO_ALOCADO'].astype(str).str.contains('2', na=False)]['VOLUME_TOTAL'].sum()
        me_t3_bipes = df_me_hoje_bipado[df_me_hoje_bipado['TURNO_ALOCADO'].astype(str).str.contains('3', na=False)]['VOLUME_TOTAL'].sum()
    else:
        me_t1_bipes, me_t2_bipes, me_t3_bipes = 0, 0, 0

    dia_semana_hoje = hoje_br.weekday()

    # --- FUNÇÃO DE STATUS DO SLA BASEADA NO RELÓGIO (INDIVIDUAL POR ÁREA) ---
    def gerar_status_SLA_individual(bipes, t_inicio, t_fim, unidade, turno_codigo):
        if dia_semana_hoje == 6 and turno_codigo in [1, 2]:
            return "🛑 Fábrica Fechada", "color:#64748b;"
        
        if turno_codigo == 3:
            if time(5, 0) <= hora_atual < time(22, 0):
                return (f"✅ Concluído ({int(bipes)} {unidade})" if bipes > 0 else "✅ Turno Concluído"), "color:#16a34a; font-weight:bold;" if bipes > 0 else "color:#64748b;"
            else:
                return ("⚙️ Em Andamento" if bipes > 0 else "⚙️ Noturno Ativo"), "color:#ea580c; font-weight:bold;"

        if hora_atual < t_inicio:
            return "⏳ Aguardando", "color:#64748b;"
        elif t_inicio <= hora_atual < t_fim:
            return ("⚙️ Em Andamento" if bipes > 0 else "⚙️ Ativo (Sem bipes)"), "color:#ea580c; font-weight:bold;"
        else:
            if bipes > 0:
                return f"✅ Finalizado ({int(bipes)} {unidade})", "color:#16a34a; font-weight:bold;"
            else:
                return "❌ Encerrado Sem Registro", "color:#dc2626;"

    # Aplicação dos estados individuais (Independentes e sem espelhamento)
    st_ht_t1, col_ht_t1 = gerar_status_SLA_individual(ht_t1_bipes, time(5,0), time(13,30), "PLT", 1)
    st_ht_t2, col_ht_t2 = gerar_status_SLA_individual(ht_t2_bipes, time(13,30), time(22,0), "PLT", 2)
    st_ht_t3, col_ht_t3 = gerar_status_SLA_individual(ht_t3_bipes, None, None, "PLT", 3)

    st_mi_t1, col_mi_t1 = gerar_status_SLA_individual(mi_t1_bipes, time(5,0), time(13,45), "un", 1)
    st_mi_t2, col_mi_t2 = gerar_status_SLA_individual(mi_t2_bipes, time(13,30), time(22,15), "un", 2)
    st_mi_t3, col_mi_t3 = gerar_status_SLA_individual(mi_t3_bipes, None, None, "un", 3)

    st_me_t1, col_me_t1 = gerar_status_SLA_individual(me_t1_bipes, time(5,0), time(13,30), "Ac", 1)
    st_me_t2, col_me_t2 = gerar_status_SLA_individual(me_t2_bipes, time(13,30), time(22,0), "Ac", 2)
    st_me_t3, col_me_t3 = gerar_status_SLA_individual(me_t3_bipes, None, None, "Ac", 3)

    # Renderização da Tabela de Controle de SLA
    matriz_sla_html = f"""
    <table style="width:100%; border-collapse: collapse; font-size:14px; text-align:left; background-color: white; border: 1px solid #cbd5e1; border-radius: 6px;">
        <tr style="background-color: #f1f5f9; border-bottom: 2px solid #cbd5e1;">
            <th style="padding: 12px; color:#475569;">MÓDULO OPERACIONAL</th>
            <th style="padding: 12px; color:#475569;">TURNO 1 (05h00 - 13h30)</th>
            <th style="padding: 12px; color:#475569;">TURNO 2 (13h30 - 22h00)</th>
            <th style="padding: 12px; color:#475569;">TURNO 3 (22h00 - 05h00)</th>
        </tr>
        <tr style="border-bottom: 1px solid #e2e8f0;">
            <td style="padding: 12px; font-weight:bold; color:#1e3a8a;">🪵 ESTUFAS HT</td>
            <td style="padding: 12px; {col_ht_t1}">{st_ht_t1}</td>
            <td style="padding: 12px; {col_ht_t2}">{st_ht_t2}</td>
            <td style="padding: 12px; {col_ht_t3}">{st_ht_t3}</td>
        </tr>
        <tr style="border-bottom: 1px solid #e2e8f0;">
            <td style="padding: 12px; font-weight:bold; color:#0f766e;">📐 LASTRAS NOVAS</td>
            <td style="padding: 12px; color:#ef4444; font-weight:bold; background-color:#fef2f2;" colspan="3">🛠️ MÓDULO EM MANUTENÇÃO TÉCNICA</td>
        </tr>
        <tr style="border-bottom: 1px solid #e2e8f0;">
            <td style="padding: 12px; font-weight:bold; color:#2563eb;">📥 MERCADO INTERNO (MI)</td>
            <td style="padding: 12px; {col_mi_t1}">{st_mi_t1}</td>
            <td style="padding: 12px; {col_mi_t2}">{st_mi_t2}</td>
            <td style="padding: 12px; {col_mi_t3}">{st_mi_t3}</td>
        </tr>
        <tr>
            <td style="padding: 12px; font-weight:bold; color:#7c3aed;">🚢 MERCADO EXTERNO (ME)</td>
            <td style="padding: 12px; {col_me_t1}">{st_me_t1}</td>
            <td style="padding: 12px; {col_me_t2}">{st_me_t2}</td>
            <td style="padding: 12px; {col_me_t3}">{st_me_t3}</td>
        </tr>
    </table>
    """
    st.markdown(matriz_sla_html, unsafe_allow_html=True)

    # ─────────────────────────────────────────────────────────────────
    # BLOCO 2: CARTEIRA DE DEMANDAS CONSOLIDADAS
    # ─────────────────────────────────────────────────────────────────
    st.markdown("<div class='section-header'>📊 Carteira de Demandas Consolidadas (Fluxos Operacionais)</div>", unsafe_allow_html=True)
    
    df_ht_validos = df_ht[df_ht['Total_Plt_Percurso'] > 0].copy() if df_ht is not None else pd.DataFrame()
    ht_total_aberto = int(df_ht_validos['Total_Plt_Percurso'].sum())
    ht_cargas = len(df_ht_validos)
    ht_mari = len(df_ht_validos[df_ht_validos['Modal'].str.contains('Marítimo', case=False, na=False)])
    ht_rodo = len(df_ht_validos[df_ht_validos['Modal'].str.contains('Rodoviário', case=False, na=False)])

    df_me_sobras = df_me[df_me['STATUS'] == "NÃO SEQUENCIADO"] if df_me is not None else pd.DataFrame()
    me_sobras_volume = int(df_me_sobras['VOLUME_TOTAL'].sum())

    df_mi_sobras = df_mi[df_mi['STATUS'] == "NÃO SEQUENCIADO"] if df_mi is not None else pd.DataFrame()
    mi_cxs = int(pd.to_numeric(df_mi_sobras['CXS'], errors='coerce').sum()) if not df_mi_sobras.empty else 0
    mi_pls = int(pd.to_numeric(df_mi_sobras['PLS'], errors='coerce').sum()) if not df_mi_sobras.empty else 0
    mi_total_sobras = mi_cxs + mi_pls

    col_a, col_b, col_c, col_d = st.columns(4)
    
    with col_a:
        st.markdown(f"""
        <div style="background-color: #ffffff; padding: 15px; border-radius: 8px; border-top: 4px solid #1e3a8a; box-shadow: 0 1px 3px rgba(0,0,0,0.1); text-align: center; height:150px;">
            <span style="font-size: 12px; color: #4b5563; font-weight: bold; text-transform: uppercase;">🪵 Total Geral em Aberto HT</span>
            <h2 style="margin: 5px 0; color: #1e3a8a; font-size: 28px;">{ht_total_aberto} Plts</h2>
            <span style="font-size: 11px; color: #64748b; font-weight: 600;">🚢 Marítimo: {ht_mari} | 🚚 Rodo: {ht_rodo} ({ht_cargas} cargas)</span>
        </div>
        """, unsafe_allow_html=True)

    with col_b:
        st.markdown(f"""
        <div style="background-color: #ffffff; padding: 15px; border-radius: 8px; border-top: 4px solid #7c3aed; box-shadow: 0 1px 3px rgba(0,0,0,0.1); text-align: center; height:150px;">
            <span style="font-size: 12px; color: #4b5563; font-weight: bold; text-transform: uppercase;">🔴 Sobras Geral ME</span>
            <h2 style="margin: 5px 0; color: #7c3aed; font-size: 28px;">{me_sobras_volume} <span style="font-size:16px;">Acessos</span></h2>
            <span style="font-size: 11px; color: #64748b; font-weight: 600;">Aguardando alocação tática de turnos</span>
        </div>
        """, unsafe_allow_html=True)

    with col_c:
        st.markdown(f"""
        <div style="background-color: #ffffff; padding: 15px; border-radius: 8px; border-top: 4px solid #0f766e; box-shadow: 0 1px 3px rgba(0,0,0,0.1); text-align: center; height:150px;">
            <span style="font-size: 12px; color: #4b5563; font-weight: bold; text-transform: uppercase;">🔎 Sobras da Carteira MI</span>
            <h2 style="margin: 5px 0; color: #0f766e; font-size: 28px;">{mi_total_sobras} <span style="font-size:16px;">un</span></h2>
            <span style="font-size: 11px; color: #64748b; font-weight: 600;">📦 {mi_cxs} Cxs não seq. | 🪵 {mi_pls} Pls não seq.</span>
        </div>
        """, unsafe_allow_html=True)

    with col_d:
        st.markdown(f"""
        <div style="background-color: #f1f5f9; padding: 15px; border-radius: 8px; border-top: 4px solid #94a3b8; box-shadow: 0 1px 3px rgba(0,0,0,0.05); text-align: center; height:150px; opacity: 0.75;">
            <span style="font-size: 12px; color: #64748b; font-weight: bold; text-transform: uppercase;">📐 Demanda Lastras</span>
            <h2 style="margin: 15px 0; color: #64748b; font-size: 22px;">🛠️ Em Manutenção</h2>
            <span style="font-size: 11px; color: #94a3b8;">Aguardando liberação engenharia</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.info("💡 **Acesso Restrito:** Os dados analíticos acima estão sincronizados de forma segura a partir das bases mestres da memória de cache.")

# ==============================================================================
# 📊 MÓDULO: DASHBOARD HT
# ==============================================================================
elif opcao == "Dashboard HT":
    st.title("📊 Diagnóstico Operacional - HT")
    if df_ht is not None:
        st.success("⚡ Dados HT carregados instantaneamente da memória de alta velocidade!")
        st.dataframe(df_ht.head(10))
    else:
        st.error("Falha ao sincronizar o módulo HT.")

# ==============================================================================
# 📦 MÓDULO: MERCADO EXTERNO (ME)
# ==============================================================================
elif opcao == "Mercado Externo (ME)":
    st.title("📦 Sequenciamento - Mercado Externo (ME)")
    if df_me is not None:
        st.info("⚡ Fila de espera ME carregada com sucesso.")
        st.dataframe(df_me.head(10))
    else:
        st.error("Falha ao sincronizar o módulo ME.")

# ==============================================================================
# 👑 MÓDULO: MERCADO INTERNO (MI)
# ==============================================================================
elif opcao == "Mercado Interno (MI)":
    st.title("👑 Sequenciamento - Mercado Interno (MI)")
    if df_mi is not None:
        st.info("⚡ Fila de espera MI processada com sucesso a partir da memória.")
        st.dataframe(df_mi.head(10))
    else:
        st.error("Falha ao sincronizar o módulo MI.")

# ==============================================================================
# ⚙️ MÓDULO: SEQUENCIAMENTO LASTRAS
# ==============================================================================
elif opcao == "Sequenciamento Lastras":
    st.title("⚙️ Sequenciamento - Lastras Novas")
    if not df_lastras.empty:
        st.success("⚡ Painel de Lastras carregado de forma unificada!")
        st.dataframe(df_lastras.head(10))
    else:
        st.error("Falha ao sincronizar o módulo de Lastras.")