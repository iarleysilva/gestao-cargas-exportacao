import streamlit as st
import pandas as pd
from datetime import datetime
import zoneinfo
import unicodedata
import os
from pathlib import Path
from fpdf import FPDF

# ─── BLOCO DE SEGURANÇA DE CAMINHOS ROBUSTO ───
import sys
raiz = Path(__file__).resolve().parents[1]
if str(raiz) not in sys.path:
    sys.path.append(str(raiz))
# ───────────────────────────────────────────────────────────────────────────────────

# Configuração Única da Página
st.set_page_config(
    page_title="Workflow Flows ME 4.1",
    page_icon="🔍",
    layout="wide"
)

# 🔒 CONTROLADOR DE ACESSO: CAMADA DE SEGURANÇA OPERACIONAL COM SENHA
SENHA_CORRETA = "PcoMe2026"

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    st.markdown("""
        <div style="text-align: center; margin-top: 50px;">
            <h2 style="color: #1e3a8a; font-weight: 800;">🔒 Sistema de Segurança Integrado PCO</h2>
            <p style="color: #64748b;">Este ambiente contém dados de faturamento estratégico e histórico de Lead Times (2024 - 2026 YTD). Insira a senha corporativa.</p>
        </div>
    """, unsafe_allow_html=True)
    
    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_b:
        senha_digitada = st.text_input("Senha de Acesso:", type="password", placeholder="Digite a chave corporativa...")
        botao_entrar = st.button("🔑 Liberar Acesso ao Cockpit", use_container_width=True)
        
        if botao_entrar:
            if senha_digitada == SENHA_CORRETA:
                st.session_state["autenticado"] = True
                st.rerun()
            else:
                st.error("❌ Credencial inválida. Acesso negado aos relatórios contábeis e operacionais.")
    st.stop()

# ───────────────────────────────────────────────────────────────────────────────────
# 🎨 SE PASSOU DA SENHA: INTERFACE DE AUDITORIA OPERACIONAL DO FLOWS ME 4.1
# ───────────────────────────────────────────────────────────────────────────────────

# Estilização CSS Premium para a Linha do Tempo e Tabelas de Processo
st.markdown("""
    <style>
        .main-title { color: #1e3a8a; font-weight: 800; margin-bottom: 5px; }
        .card-container { background-color: #ffffff; padding: 22px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border: 1px solid #e2e8f0; margin-bottom: 20px; }
        .metric-box { background-color: #f8fafc; border-radius: 8px; padding: 12px; text-align: center; border: 1px solid #e2e8f0; }
        .metric-title { font-size: 11px; color: #64748b; font-weight: 700; text-transform: uppercase; }
        .metric-value { font-size: 16px; color: #0f172a; font-weight: 700; margin-top: 4px; }
        .wf-table { width: 100%; border-collapse: collapse; margin-top: 15px; background-color: white; }
        .wf-table th { background-color: #f8fafc; color: #475569; padding: 10px 15px; text-align: left; font-size: 13px; font-weight: 700; border-bottom: 2px solid #e2e8f0; text-transform: uppercase; }
        .wf-table td { padding: 12px 15px; font-size: 14px; border-bottom: 1px solid #f1f5f9; color: #1e293b; }
        .status-ok { color: #16a34a; font-weight: 700; text-align: center; font-size: 16px; }
        .status-wait { color: #ea580c; font-weight: 700; text-align: center; font-size: 16px; }
        .date-text { color: #334155; font-weight: 500; }
        .pending-text { color: #94a3b8; font-weight: 500; font-style: italic; }
        .badge-modal { padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: bold; text-transform: uppercase; }
    </style>
""", unsafe_allow_html=True)

col_titulo, col_logout = st.columns([6, 1])
with col_titulo:
    st.markdown("<h1 class='main-title'>🔍 Painel de Visão de Processos (Flows ME 4.1)</h1>", unsafe_allow_html=True)
    st.write("Auditoria Avançada: Cruzamento histórico de processos logísticos de comércio exterior.")
with col_logout:
    if st.button("🔒 Encerrar Sessão", use_container_width=True):
        st.session_state["autenticado"] = False
        st.rerun()

st.markdown("---")

# 💾 FUNÇÃO DE CACHE ADAPTATIVA (ROBUSTA CONTRA DIRETÓRIOS DO TERMINAL)
@st.cache_data(ttl=300)
def carregar_base_flows_suprema_local():
    nome_arquivo = "Dados_para_teste_workflows_ME (17).csv"
    caminho_script = Path(__file__).resolve()
    raiz_projeto = caminho_script.parent.parent
    
    caminho_1 = raiz_projeto / "src" / "data" / nome_arquivo
    caminho_2 = Path("src/data") / nome_arquivo
    caminho_3 = Path(nome_arquivo).resolve()
    
    if caminho_1.exists():
        df = pd.read_csv(caminho_1)
    elif caminho_2.exists():
        df = pd.read_csv(caminho_2)
    elif caminho_3.exists():
        df = pd.read_csv(caminho_3)
    else:
        return None, None
        
    if 'fatura_patio' in df.columns:
        df['fatura_pura'] = df['fatura_patio'].astype(str).str.split('/').str[0].str.strip()
    return df, nome_arquivo

df_wk, nome_arquivo_carregado = carregar_base_flows_suprema_local()

# 🚦 ALERTAS VISUAIS FORA DO CACHE
if df_wk is not None and not df_wk.empty:
    st.toast(f"💻 Cockpit ativo! Base unificada: {nome_arquivo_carregado}", icon="💾")
else:
    caminho_script = Path(__file__).resolve()
    raiz_projeto = caminho_script.parent.parent
    pasta_esperada = raiz_projeto / "src" / "data"
    st.markdown(f"""
    <div style="background-color: #fde8e8; border-left: 5px solid #e11d48; padding: 20px; border-radius: 8px; color: #9f1239;">
        <h4 style="margin: 0 0 10px 0; font-weight: 800;">❌ Erro de Organização de Arquivos</h4>
        <p style="margin: 0 0 10px 0; font-size: 14px;">O arquivo unificado não foi localizado na pasta de dados.</p>
        <p style="margin: 0; font-size: 13px;">Garanta que o arquivo <b>Dados_para_teste_workflows_ME (17).csv</b> esteja em:<br>
        📂 <code>{pasta_esperada}</code></p>
    </div>
    <br>
    """, unsafe_allow_html=True)
    st.stop()

# --- ÁREA DE FILTROS INTELIGENTES ---
st.markdown("### 🎛️ Filtros de Pesquisa por Processo")
col1, col2 = st.columns(2)

with col1:
    lista_bookings = ["-- Selecione um Booking --"] + sorted([str(b) for b in df_wk['booking'].dropna().unique() if str(b) != 'nan'])
    booking_selecionado = st.selectbox("Filtrar por Reserva de Porto (Booking):", lista_bookings)

with col2:
    fatura_digitada = st.text_input("Ou digite o número da Fatura Comercial (Ex: 1457 ou 2192):", placeholder="Ex: 1457").strip()

# Execução do Filtro Lógico
df_filtrado = pd.DataFrame()
if fatura_digitada:
    fatura_busca_pura = fatura_digitada.split('/')[0].strip()
    df_filtrado = df_wk[df_wk['fatura_pura'] == fatura_busca_pura]
elif booking_selecionado != "-- Selecione um Booking --":
    df_filtrado = df_wk[df_wk['booking'].astype(str) == booking_selecionado]

# --- RENDERIZAÇÃO DA ESTEIRA DO FLOWS ---
if df_filtrado.empty:
    st.markdown("""
        <div style="text-align: center; border: 2px dashed #cbd5e1; padding: 40px; border-radius: 8px; background-color: #f8fafc;">
            <p style="color: #64748b; font-weight: 500; font-size:15px; margin:0;">💡 Insira uma Fatura válida ou escolha um Booking para projetar a análise e emitir o Laudo em PDF.</p>
        </div>
    """, unsafe_allow_html=True)
else:
    def limpar_txt(txt):
        if pd.isna(txt) or txt is None: return "N/A"
        texto_limpo = "".join(c for c in unicodedata.normalize('NFD', str(txt)) if unicodedata.category(c) != 'Mn')
        return "".join(c for c in texto_limpo if ord(c) < 128)

    def fmt_dt(val):
        if pd.isna(val) or str(val).strip() == "" or str(val).lower() == "nan":
            return None
        try:
            limpo = str(val).split('.')[0].replace('T', ' ').replace('Z', '').strip()
            if len(limpo) == 16:
                return datetime.strptime(limpo, '%Y-%m-%d %H:%M')
            return datetime.strptime(limpo, '%Y-%m-%d %H:%M:%S')
        except:
            return None

    for idx, row in df_filtrado.iterrows():
        fatura_id = str(row.get('fatura_patio', 'N/A'))
        container_sigla = str(row.get('container_sigla', 'N/A'))
        percurso_id = str(row.get('percurso', 'N/A'))
        booking_id = str(row.get('booking', 'N/A'))
        
        is_maritimo = pd.notna(row.get('booking')) and str(row.get('booking')).lower() != 'nan' and str(row.get('booking')).strip() != ""
        txt_modal_tela = "🚢 MARÍTIMO" if is_maritimo else "🚛 RODOVIÁRIO TERRESTRE (MERCOSUL)"
        txt_modal_pdf = "MARITIMO" if is_maritimo else "RODOVIARIO TERRESTRE"
        cor_modal = "background-color: #e0f2fe; color: #0369a1;" if is_maritimo else "background-color: #fef3c7; color: #b45309;"

        cliente_id = str(row.get('cliente')) if pd.notna(row.get('cliente')) else "Cliente em Análise Aduaneira"
        destino_id = str(row.get('destino')) if pd.notna(row.get('destino')) else "Destino Registrado"
        incoterm = str(row.get('incoterm_codigo')) if pd.notna(row.get('incoterm_codigo')) else "FOB"
        status_fat = str(row.get('status_final_faturamento', 'Aguardando Emissão'))
        canal = str(row.get('canal_patio', 'N/A'))
        
        desc_canal_wms = str(row.get('desc_canal_wms', 'DIRECT SALE'))
        prioridade_wms = str(row.get('prioridade_wms', 'EXPORTAÇÃO - PORTO'))
        tipo_formato = str(row.get('indic_lastras', 'Outros formatos'))
        cor_formato = "color: #e11d48; font-weight: bold;" if tipo_formato == "Lastras" else "color: #0f172a;"

        receita_reais = pd.to_numeric(row.get('receita_total_faturada_reais'), errors='coerce')
        receita_reais = float(receita_reais) if pd.notna(receita_reais) else 0.0
        total_pecas = pd.to_numeric(row.get('total_pecas_faturadas'), errors='coerce')
        total_pecas = float(total_pecas) if pd.notna(total_pecas) else 0.0
        nf_emitida = pd.to_numeric(row.get('ultima_nf_emitida'), errors='coerce')
        nf_valida = int(nf_emitida) if pd.notna(nf_emitida) and nf_emitida > 0 else 0

        txt_faturamento = f'R$ {receita_reais:,.2f}' if receita_reais > 0 else 'Aguardando Gatilho Contábil'
        txt_nf = f'{nf_valida}' if nf_valida > 0 else 'N/A'
        txt_pecas = f'{total_pecas:,.2f} un' if total_pecas > 0 else 'Em Carregamento'

        # 📐 EXTRAÇÃO SECA DOS NOMES EXATOS DAS COLUNAS (17)
        dt_nascimento = fmt_dt(row.get('data_nascimento_percurso'))
        dt_pronta_wms = fmt_dt(row.get('data_carga_pronta_wms'))
        lead_time_wms_cd = "N/A"
        if dt_nascimento and dt_pronta_wms:
            diff_wms = (dt_pronta_wms - dt_nascimento).total_seconds() / 3600
            if diff_wms >= 0:
                lead_time_wms_cd = f"{diff_wms:.1f} horas"

        dt_chegada = fmt_dt(row.get('dt_chegada_fabrica'))
        dt_saida = fmt_dt(row.get('dt_saida_fabrica'))
        lead_time_patio = "N/A"
        if dt_chegada and dt_saida:
            diff_patio = (dt_saida - dt_chegada).total_seconds() / 3600
            if diff_patio >= 0:
                lead_time_patio = f"{diff_patio:.1f} horas"

        # Cockpit Executivo na Tela
        st.markdown(f"""
        <div class="card-container">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                <h3 style="color:#1e3a8a; font-size: 1.25rem; font-weight:700; margin:0;">📦 ID Percurso: {percurso_id} | Contêiner: {container_sigla}</h3>
                <span class="badge-modal" style="{cor_modal}">{txt_modal_tela}</span>
            </div>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 15px; margin-bottom: 15px;">
                <div class="metric-box"><div class="metric-title">📋 Fatura Ativa</div><div class="metric-value">{fatura_id}</div></div>
                <div class="metric-box"><div class="metric-title">🚦 Formato Carga</div><div class="metric-value" style="{cor_formato}">{tipo_formato}</div></div>
                <div class="metric-box"><div class="metric-title">🚦 Canal Pátio</div><div class="metric-value" style="color: {'#16a34a' if canal=='VERDE' else '#475569'}; font-weight:bold;">{canal}</div></div>
                <div class="metric-box"><div class="metric-title">⏱️ Lead Time Separacao (CD)</div><div class="metric-value" style="color: #2563eb;">{lead_time_wms_cd}</div></div>
            </div>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 15px; font-size: 13px; color: #475569; background-color:#f8fafc; padding:12px; border-radius:6px; border: 1px solid #e2e8f0;">
                <div><b>🏢 Cliente Final:</b> {cliente_id}</div>
                <div><b>🌍 Destino Internacional:</b> {destino_id} | <b>Incoterm:</b> <code>{incoterm}</code></div>
                <div><b>🚚 Logística Física:</b> {str(row.get('motorista', 'N/I'))} (Placa: <code>{str(row.get('cavalo', 'N/A'))}</code>) | <b>Giro Pátio:</b> <code>{lead_time_patio}</code></div>
                <div><b>🚦 Canal WMS:</b> {desc_canal_wms} | <b>Prioridade:</b> {prioridade_wms}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # --- ABAS DE PROCESSO RECONSTRUÍDAS SEM ESPAÇOS DE MARGEM (RESOLVE O BUG VISUAL) ---
        nome_aba_3 = "🚢 3. Escoamento Marítimo & Porto" if is_maritimo else "<b>🚛 3. Escoamento Terrestre (Fronteira)</b>"
        t1, t2, t3 = st.tabs(["🏭 1. Logística de Pátio & Fábrica (CD)", "📋 2. SLA & Documental PCO", nome_aba_3])
        
        with t1:
            st.markdown("##### ⏱️ Linha do Tempo Estendida do Ciclo de Vida do Percurso")
            
            marcos_patio = [
                {"fase": "🟢 ANTES", "etapa": "Nascimento / Criacao do Percurso no ERP", "valor": row.get('data_nascimento_percurso')},
                {"fase": "🟢 ANTES", "etapa": "Planejamento de Janela de Carregamento", "valor": row.get('dt_carregamento_plan')},
                {"fase": "🟢 ANTES", "etapa": "Planejamento de Unitização / Estufagem no CD", "valor": row.get('dt_unitizacao_plan')},
                {"fase": "🟢 ANTES", "etapa": "Conclusão do Picking / Carga Pronta na Calçada (WMS)", "valor": row.get('data_carga_pronta_wms')},
                {"fase": "🟡 DURANTE", "etapa": "Conclusão de Unitização Física Interna (CD)", "valor": row.get('dt_unitizacao_real')},
                {"fase": "🟡 DURANTE", "etapa": "Retirada / Coleta de Contêiner Vazio Realizada", "valor": row.get('dt_entrega_vazio_real')},
                {"fase": "🟡 DURANTE", "etapa": "Chegada do Veículo na Fila da Portaria Externa", "valor": row.get('dt_chegada_fabrica')},
                {"fase": "🟡 DURANTE", "etapa": "Entrada na Fábrica e Acoplamento na Doca", "valor": row.get('dt_entrada_fabrica')},
                {"fase": "🟡 DURANTE", "etapa": "Fim do Carregamento Físico e Estufagem do Veículo", "valor": row.get('dt_carregamento_real')},
                {"fase": "🔵 DEPOIS", "etapa": "Liberação e Faturamento Fiscal das Lojas/Clientes", "valor": row.get('data_faturamento_wms')},
                {"fase": "🔵 DEPOIS", "etapa": "Saída da Portaria Fábrica (Início Trânsito Fronteira/Porto)", "valor": row.get('dt_saida_fabrica')},
            ]
            
            h1 = ""
            for m in marcos_patio:
                d = fmt_dt(m["valor"])
                txt_d = d.strftime('%d/%m/%Y às %H:%M') if d else None
                icone = '✅' if txt_d else '⏳'
                classe_status = 'status-ok' if txt_d else 'status-wait'
                txt_data_exibida = f'<span class="date-text">{txt_d}</span>' if txt_d else '<span class="pending-text">Aguardando Processo</span>'
                # Construção em linha única contínua sem espaços na esquerda para travar o renderizador HTML
                h1 += f"<tr><td style='font-weight:bold; color:#1e3a8a;'>{m['fase']}</td><td class='{classe_status}'>{icone}</td><td style='font-weight:600;'>{m['etapa']}</td><td>{txt_data_exibida}</td></tr>"
                
            st.markdown(f'<table class="wf-table"><tr><th style="width:15%;">ESTÁGIO</th><th style="width:10%; text-align:center;">STATUS</th><th style="width:45%;">MARCO OPERACIONAL DO PERCURSO</th><th style="width:30%;">DATA / HORA REALIZADO</th></tr>{h1}</table>', unsafe_allow_html=True)

        with t2:
            marcos_pco = [
                {"etapa": "Gatilho de Emissão Fiscal (Data Faturamento Real)", "valor": row.get('data_real_faturamento')},
                {"etapa": "Data Limite Regulamentar para Envio do Draft (SLA)", "valor": row.get('dt_deadline_draft')},
            ]
            h2 = ""
            for m in marcos_pco:
                d = fmt_dt(m["valor"])
                txt_d = d.strftime('%d/%m/%Y às %H:%M') if d else None
                icone = '✅' if txt_d else '⏳'
                classe_status = 'status-ok' if txt_d else 'status-wait'
                txt_data_exibida = f'<span class="date-text">{txt_d}</span>' if txt_d else '<span class="pending-text">Pendente / Em Trâmite</span>'
                h2 += f"<tr><td class='{classe_status}'>{icone}</td><td style='font-weight:600;'>{m['etapa']}</td><td>{txt_data_exibida}</td></tr>"
                
            st.markdown(f'<table class="wf-table"><tr><th style="width:10%; text-align:center;">STATUS</th><th style="width:50%;">MARCO REGULAMENTAR & FISCAL</th><th style="width:40%;">DATA / HORA REALIZADO</th></tr>{h2}</table>', unsafe_allow_html=True)

        with t3:
            h3 = ""
            if is_maritimo:
                marcos_porto = [
                    {"etapa": "Saída da Portaria Fábrica (Trânsito Porto)", "valor": row.get('dt_saida_fabrica')},
                    {"etapa": "Liberação do Desembaraço Aduaneiro", "valor": row.get('dt_desembaraco')},
                    {"etapa": "Gate-in Confirmado Terminal (Carga Liberada)", "valor": row.get('dt_carga_liberada_porto')},
                    {"etapa": "Prazo Limite do Navio (Corte de Carga Porto)", "valor": row.get('dt_deadline_carga')},
                ]
                for m in marcos_porto:
                    d = fmt_dt(m["valor"])
                    txt_d = d.strftime('%d/%m/%Y às %H:%M') if d else None
                    icone = '✅' if txt_d else '⏳'
                    classe_status = 'status-ok' if txt_d else 'status-wait'
                    txt_data_exibida = f'<span class="date-text">{txt_d}</span>' if txt_d else '<span class="pending-text">Aguardando Chegada no Porto</span>'
                    h3 += f"<tr><td class='{classe_status}'>{icone}</td><td style='font-weight:600;'>{m['etapa']}</td><td>{txt_data_exibida}</td></tr>"
                st.markdown(f'<table class="wf-table"><tr><th style="width:10%; text-align:center;">STATUS</th><th style="width:50%;">MARCO PORTUÁRIO MARÍTIMO</th><th style="width:40%;">DATA / HORA REALIZADO</th></tr>{h3}</table>', unsafe_allow_html=True)
            else:
                marcos_terrestre = [
                    {"etapa": "Saída da Portaria Fábrica (Início Trânsito Fronteira)", "valor": row.get('dt_saida_fabrica')},
                ]
                for m in marcos_terrestre:
                    d = fmt_dt(m["valor"])
                    txt_d = d.strftime('%d/%m/%Y às %H:%M') if d else None
                    icone = '✅' if txt_d else '⏳'
                    classe_status = 'status-ok' if txt_d else 'status-wait'
                    txt_data_exibida = f'<span class="date-text">{txt_d}</span>' if txt_d else '<span class="pending-text">Aguardando Saída</span>'
                    h3 += f"<tr><td class='{classe_status}'>{icone}</td><td style='font-weight:600;'>{m['etapa']}</td><td>{txt_data_exibida}</td></tr>"
                
                h3 += f"<tr><td class='status-ok'>✅</td><td style='font-weight:600;'>Liberação de Trânsito Terrestre Internacional</td><td><span class='date-text'>Isento de Deadlines de Navio / Fluxo Direto Fronteira</span></td></tr>"
                st.markdown(f'<table class="wf-table"><tr><th style="width:10%; text-align:center;">STATUS</th><th style="width:50%;">MARCO LOGÍSTICO TERRESTRE</th><th style="width:40%;">STATUS / FLUXO EM FRONTEIRA</th></tr>{h3}</table>', unsafe_allow_html=True)

        st.markdown("<br><div style='border-top:1px dashed #cbd5e1; margin:10px 0;'></div>", unsafe_allow_html=True)