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
# 🖨️ INTELIGÊNCIA DEDICADA DE IMPRESSÃO (ESTRUTURA COMPACTA PARA CÓDIGO LIMPO)
# ───────────────────────────────────────────────────────────────────────────────────
class PDFGeradorLote(FPDF):
    def header(self):
        # Top Banner Corporativo do Laudo Executivo
        self.set_fill_color(30, 58, 138)
        self.rect(0, 0, 210, 30, 'F')
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", 'B', 12)
        self.set_y(8)
        self.cell(0, 5, "PORTOBELLO S.A. | CONTROLADORIA OPERACIONAL PCO", ln=1, align="L")
        self.set_font("Helvetica", '', 9)
        self.cell(0, 4, "Laudo Técnico de Auditoria E2E e Lead Times por Evento (Mercado Externo)", ln=1, align="L")
        self.set_y(35)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", 'I', 8)
        self.set_text_color(148, 163, 184)
        self.cell(0, 10, f"Página {self.page_no()} | Homologação Flows ME 4.1", align="C")

# ───────────────────────────────────────────────────────────────────────────────────
# 🎨 INTERFACE DE AUDITORIA OPERACIONAL DO FLOWS ME 4.1
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

df_wk['dt_plan_parsed'] = pd.to_datetime(df_wk['dt_carregamento_plan'], errors='coerce')
df_wk['ano_processo'] = df_wk['dt_plan_parsed'].dt.year.fillna(0).astype(int)
anos_disponiveis = sorted([int(a) for a in df_wk['ano_processo'].unique() if a > 0])

col_ano, col_bkg, col_fat = st.columns([1, 2, 2])

with col_ano:
    ano_selecionado = st.selectbox("1. Escolha o Ano de Pesquisa:", anos_disponiveis, index=len(anos_disponiveis)-1)

# Trava de segurança para buscar registros APENAS do ano corrente
df_wk_ano = df_wk[df_wk['ano_processo'] == ano_selecionado]

with col_bkg:
    lista_bookings = ["-- Selecione um Booking --"] + sorted([str(b) for b in df_wk_ano['booking'].dropna().unique() if str(b) != 'nan'])
    booking_selecionado = st.selectbox("2. Filtrar por Booking:", lista_bookings)

with col_fat:
    fatura_digitada = st.text_input("3. Ou digite a Fatura Comercial (Ex: 1457 ou 2192):", placeholder="Ex: 1457").strip()

# Execução do Filtro Lógico Amarrado ao Ano Corrente
df_filtrado = pd.DataFrame()
if fatura_digitada:
    fatura_busca_pura = fatura_digitada.split('/')[0].strip()
    df_filtrado = df_wk_ano[df_wk_ano['fatura_pura'] == fatura_busca_pura]
elif booking_selecionado != "-- Selecione um Booking --":
    df_filtrado = df_wk_ano[df_wk_ano['booking'].astype(str) == booking_selecionado]

# --- RENDERIZAÇÃO DA ESTEIRA DO FLOWS ---
if df_filtrado.empty:
    st.markdown("""
        <div style="text-align: center; border: 2px dashed #cbd5e1; padding: 40px; border-radius: 8px; background-color: #f8fafc;">
            <p style="color: #64748b; font-weight: 500; font-size:15px; margin:0;">💡 Escolha o Ano e insira uma Fatura válida ou escolha um Booking para projetar o pacote de contêineres.</p>
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

    # ─── MOTOR SÊNIOR DE EMISSÃO PDF: DETALHADO POR CONTEINER + SOMA GLOBAL E LEAD TIMES ───
    def gerar_pdf_pacote_com_leadtimes(dados_df, fat_id, ano_ref):
        pdf = PDFGeradorLote()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # 📄 PÁGINA 1: CAPA COM A SOMA CONSOLIDADA DO PROCESSO COMO UM TODO
        pdf.add_page()
        pdf.set_text_color(15, 23, 42)
        pdf.set_font("Helvetica", 'B', 14)
        pdf.cell(0, 10, f"LAUDO AUDITOR COCKPIT - PACOTE DE EXPEDICAO", ln=1)
        pdf.set_font("Helvetica", '', 10)
        pdf.cell(0, 5, f"Fatura Analisada: {limpar_txt(fat_id)} | Ano Fiscal Mapeado: {ano_ref}", ln=1)
        pdf.ln(5)
        
        # Agregadores Totais
        total_cntrs = len(dados_df)
        soma_receita = pd.to_numeric(dados_df['receita_total_faturada_reais'], errors='coerce').fillna(0).sum()
        soma_pecas = pd.to_numeric(dados_df['total_pecas_faturadas'], errors='coerce').fillna(0).sum()
        
        pdf.set_fill_color(241, 245, 249)
        pdf.set_font("Helvetica", 'B', 11)
        pdf.cell(190, 8, " 1. RESUMO GERAL CONSOLIDADO DO EMBARQUE (SOMA DO PROCESSO)", ln=1, fill=True)
        pdf.set_font("Helvetica", '', 10)
        pdf.cell(190, 7, f" * Total de Ativos no Lote: {total_cntrs} Conteiner(es)", ln=1)
        pdf.cell(190, 7, f" * Faturamento Total Integrado: R$ {soma_receita:,.2f}", ln=1)
        pdf.cell(190, 7, f" * Volume de Pecas Faturadas no Lote: {soma_pecas:,.2f} un", ln=1)
        
        # Listagem resumida do pacote
        pdf.ln(5)
        pdf.set_font("Helvetica", 'B', 11)
        pdf.cell(190, 8, " 2. INDEXADOR DE DISPARO DE ATIVOS NO PACOTE", ln=1, fill=True)
        pdf.set_font("Helvetica", 'B', 9)
        pdf.cell(30, 7, "ID Percurso", border=1)
        pdf.cell(45, 7, "Sigla Conteiner", border=1)
        pdf.cell(40, 7, "Canal Patio", border=1)
        pdf.cell(75, 7, "Cliente", border=1, ln=1)
        
        pdf.set_font("Helvetica", '', 9)
        for _, r in dados_df.iterrows():
            pdf.cell(30, 7, str(r.get('percurso')), border=1)
            pdf.cell(45, 7, str(r.get('container_sigla', 'N/A')), border=1)
            pdf.cell(40, 7, str(r.get('canal_patio', 'N/A')), border=1)
            pdf.cell(75, 7, str(r.get('cliente', 'N/A'))[:35], border=1, ln=1)
            
        # 📄 PÁGINAS SEGUINTES: DETALHAMENTO DO LAUDO DE LEAD TIME POR EVENTO PONTA A PONTA
        for _, r in dados_df.iterrows():
            pdf.add_page()
            pid = str(r.get('percurso', 'N/A'))
            cntr = str(r.get('container_sigla', 'N/A'))
            
            pdf.set_font("Helvetica", 'B', 12)
            pdf.cell(190, 8, f"AUDITORIA INDIVIDUAL - CONTEINER: {cntr} / PERCURSO: {pid}", ln=1, fill=True)
            pdf.set_font("Helvetica", '', 10)
            pdf.cell(190, 6, f"Cliente Consignatario: {limpar_txt(r.get('cliente'))}", ln=1)
            pdf.cell(190, 6, f"Canal de Venda WMS: {limpar_txt(r.get('desc_canal_wms'))} | Prioridade: {limpar_txt(r.get('prioridade_wms'))}", ln=1)
            pdf.cell(190, 6, f"Tipologia da Carga: {limpar_txt(r.get('indic_lastras'))} | Nota Fiscal: {str(r.get('ultima_nf_emitida', 'N/A'))}", ln=1)
            pdf.ln(4)
            
            # --- SEÇÃO COMPACTA DE METRICAS DE LEAD TIMES POR EVENTO PONTA A PONTA ---
            pdf.set_font("Helvetica", 'B', 11)
            pdf.cell(190, 7, " TRACKING DE LEAD TIMES DE EXECUÇÃO ADUANEIRA E LOGÍSTICA:", ln=1, fill=True)
            pdf.set_font("Helvetica", '', 10)
            
            # 1. Lead Time de Separação Interna (WMS)
            t_nasc = fmt_dt(r.get('data_nascimento_percurso'))
            t_pront = fmt_dt(r.get('data_carga_pronta_wms'))
            lt_wms = f"{((t_pront - t_nasc).total_seconds() / 3600):.1f} horas" if t_nasc and t_pront else "N/A"
            pdf.cell(190, 6, f" * SLA de Separação (Nascimento ERP ate Carga Pronta WMS): {lt_wms}", ln=1)
            
            # 2. Lead Time de Espera do Caminhão (Janela Logística)
            t_cheg = fmt_dt(r.get('dt_chegada_fabrica'))
            lt_espera = f"{((t_cheg - t_pront).total_seconds() / 3600):.1f} horas" if t_cheg and t_pront else "N/A"
            pdf.cell(190, 6, f" * Tempo de Reação Logística (Carga Pronta ate Chegada do Veículo): {lt_espera}", ln=1)
            
            # 3. Lead Time de Giro de Doca (Estufagem Física)
            t_ent = fmt_dt(r.get('dt_entrada_fabrica'))
            t_carreg = fmt_dt(r.get('dt_carregamento_real'))
            lt_doca = f"{((t_carreg - t_ent).total_seconds() / 3600):.1f} horas" if t_ent and t_carreg else "N/A"
            pdf.cell(190, 6, f" * Giro de Doca / Carregamento (Entrada Portaria ate Fim Estufagem): {lt_doca}", ln=1)
            
            # 4. Lead Time de Permanência Total no Pátio
            t_sai = fmt_dt(r.get('dt_saida_fabrica'))
            lt_patio = f"{((t_sai - t_cheg).total_seconds() / 3600):.1f} horas" if t_cheg and t_sai else "N/A"
            pdf.cell(190, 6, f" * Ciclo de Vida em Pátio Fábrica (Permanência Chegada ate Saída): {lt_patio}", ln=1)
            
        return bytes(pdf.output(dest='S'))

    # Renderização Executiva do Botão Mestre de Laudo PDF
    fatura_mestre_id = str(df_filtrado.iloc[0].get('fatura_patio', fatura_digitada))
    st.markdown("### 📄 Emissão Documental Técnica e Auditoria")
    
    pdf_bytes_lote = gerar_pdf_pacote_completo(df_filtrado, fatura_mestre_id, ano_selecionado) if 'gerar_pdf_pacote_completo' in locals() else gerar_pdf_pacote_com_leadtimes(df_filtrado, fatura_mestre_id, ano_selecionado)
    
    st.download_button(
        label=f"📥 Baixar Laudo Técnico PDF Consolidado (Soma de {len(df_filtrado)} Cargas + Lead Times por Evento)",
        data=pdf_bytes_lote,
        file_name=f"Laudo_Executivo_ME_Fatura_{fatura_mestre_id.replace('/', '_')}.pdf",
        mime="application/pdf",
        use_container_width=True
    )
    st.markdown("---")

    # RENDERIZAÇÃO SECUNDÁRIA DO LOOP DOS CARDS OPERACIONAIS NA TELA
    for idx, row in df_filtrado.iterrows():
        fatura_id = str(row.get('fatura_patio', 'N/A'))
        container_sigla = str(row.get('container_sigla', 'N/A'))
        percurso_id = str(row.get('percurso', 'N/A'))
        booking_id = str(row.get('booking', 'N/A'))
        
        is_maritimo = pd.notna(row.get('booking')) and str(row.get('booking')).lower() != 'nan' and str(row.get('booking')).strip() != ""
        txt_modal_tela = "🚢 MARÍTIMO" if is_maritimo else "🚛 RODOVIÁRIO TERRESTRE (MERCOSUL)"
        cor_modal = "background-color: #e0f2fe; color: #0369a1;" if is_maritimo else "background-color: #fef3c7; color: #b45309;"

        cliente_id = str(row.get('cliente')) if pd.notna(row.get('cliente')) else "Cliente em Análise Aduaneira"
        destino_id = str(row.get('destino')) if pd.notna(row.get('destino')) else "Destino Registrado"
        incoterm = str(row.get('incoterm_codigo')) if pd.notna(row.get('incoterm_codigo')) else "FOB"
        status_fat = str(row.get('status_final_faturamento', 'Aguardando Emissão'))
        canal = str(row.get('canal_patio', 'N/A'))
        
        desc_canal_wms = str(row.get('desc_canal_wms', 'DIRECT SALE'))
        prioridade_wms = str(row.get('prioridade_wms', 'EXPORTAÇÃO - PORTO'))
        tipo_formato = str(row.get('indic_lastras', 'Outros formats'))
        cor_formato = "color: #e11d48; font-weight: bold;" if tipo_formato == "Lastras" else "color: #0f172a;"

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

        # Cockpit Visual na Tela
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
                <div class="metric-box"><div class="metric-title">⏱️ Lead Time CD (WMS)</div><div class="metric-value" style="color: #2563eb;">{lead_time_wms_cd}</div></div>
            </div>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 15px; font-size: 13px; color: #475569; background-color:#f8fafc; padding:12px; border-radius:6px; border: 1px solid #e2e8f0;">
                <div><b>🏢 Cliente Final:</b> {cliente_id}</div>
                <div><b>🌍 Destino Internacional:</b> {destino_id} | <b>Incoterm:</b> <code>{incoterm}</code></div>
                <div><b>🚚 Logística Física:</b> {str(row.get('motorista', 'N/I'))} (Placa: <code>{str(row.get('cavalo', 'N/A'))}</code>) | <b>Giro Pátio:</b> <code>{lead_time_patio}</code></div>
                <div><b>🚦 Canal WMS:</b> {desc_canal_wms} | <b>Prioridade:</b> {prioridade_wms}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # --- CONSTRUÇÃO DAS ABAS DE DETALHES ---
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