import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, time
import zoneinfo

# ─── BLOCO DE SEGURANÇA DE CAMINHOS ROBUSTO ───
import sys
from pathlib import Path
raiz = Path(__file__).resolve().parents[2]
if str(raiz) not in sys.path:
    sys.path.append(str(raiz))
# ──────────────────────────────────────────────

from src.core.data_loader import carregar_dados_separacao_mi, carregar_execucao_turnos

st.set_page_config(page_title="Desempenho MI", layout="wide")

# ─── ESTILIZAÇÃO CSS COMPACTA PARA A CHEFIA ───
st.markdown("""
<style>
    .perf-turno-box {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 18px;
        margin-bottom: 15px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.02);
    }
    .perf-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid #f1f5f9;
        padding-bottom: 8px;
        margin-bottom: 12px;
    }
    .perf-turno-title {
        font-size: 1.15rem;
        font-weight: 800;
        color: #0f766e;
    }
    .badge-merito {
        background-color: #dcfce7;
        color: #15803d;
        padding: 4px 10px;
        border-radius: 12px;
        font-weight: 700;
        font-size: 0.75rem;
    }
    .badge-atencao {
        background-color: #fee2e2;
        color: #b91c1c;
        padding: 4px 10px;
        border-radius: 12px;
        font-weight: 700;
        font-size: 0.75rem;
    }
    .badge-superacao {
        background-color: #f0fdfa;
        color: #0d9488;
        padding: 4px 10px;
        border-radius: 12px;
        font-weight: 700;
        font-size: 0.75rem;
    }
    .badge-andamento {
        background-color: #fef3c7;
        color: #d97706;
        padding: 4px 10px;
        border-radius: 12px;
        font-weight: 700;
        font-size: 0.75rem;
    }
    .metric-num {
        font-size: 1.6rem;
        font-weight: 800;
        color: #1e293b;
        line-height: 1;
    }
    .metric-sub {
        font-size: 0.75rem;
        color: #64748b;
        font-weight: 700;
        text-transform: uppercase;
        margin-top: 3px;
        margin-bottom: 8px;
    }
    .mix-text {
        font-size: 0.8rem;
        color: #475569;
        line-height: 1.3;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center; color: #0F766E;'>🎯 Monitor de SLA & Complexidade de Fracionamento MI</h1>", unsafe_allow_html=True)
st.markdown("---")

# 🛡️ CORREÇÃO DA LINHA 99: Aponta para o motor unificado estável de MI
df_demanda, data_corte_a3, txt_completo_a3 = carregar_dados_separacao_mi()
df_execucao = carregar_execucao_turnos()

if df_demanda is not None and df_execucao is not None:
    df_demanda.columns = df_demanda.columns.str.strip()
    df_execucao.columns = df_execucao.columns.str.strip()
    
    st.markdown(f"📊 **Última Atualização (Célula A3):** `{txt_completo_a3}`")
    
    # Cruzamento dinâmico: cruza a demanda planejada de MI com a base geral de bipes
    df_modelo = pd.merge(df_demanda, df_execucao, on='PERCURSO', how='left')
    
    # Identifica se a rota geral de bipes deu match com a nossa carteira de MI
    col_match = 'TURNO_REALIZOU' if 'TURNO_REALIZOU' in df_modelo.columns else ('TURNO_REAL' if 'TURNO_REAL' in df_modelo.columns else None)
    df_modelo['DEU_MATCH'] = df_modelo[col_match].notna() if col_match else False
    
    # 🛡️ LOCALIZADOR AUTOMÁTICO DE COLUNAS PARA A ABA MI (EVITA QUALQUER KEYERROR)
    c_cx, c_pl, c_ac = None, None, None
    for col in df_modelo.columns:
        c_upper = str(col).upper().strip()
        if c_upper in ["CXS", "CXS_X", "CXS_Y"] or "CAIXA" in c_upper: c_cx = col
        if c_upper in ["PLS", "PLS_X", "PLS_Y"] or "PALETE" in c_upper: c_pl = col
        if c_upper in ["ACESSOS", "ACESSOS_X", "ACESSOS_Y"] or "TOTAL ACESSOS MI" in c_upper: c_ac = col

    # Isolamento absoluto das variáveis numéricas de MI
    df_modelo["CX_REAL"] = pd.to_numeric(df_modelo[c_cx], errors="coerce").fillna(0).astype(int) if c_cx else 0
    df_modelo["PL_REAL"] = pd.to_numeric(df_modelo[c_pl], errors="coerce").fillna(0).astype(int) if c_pl else 0
    df_modelo["VOLUME_TOTAL"] = pd.to_numeric(df_modelo[c_ac], errors="coerce").fillna(0).astype(int) if c_ac else (df_modelo["CX_REAL"] + df_modelo["PL_REAL"])

    # Relógio de controle de encerramento do PCO
    fuso_br = zoneinfo.ZoneInfo("America/Sao_Paulo")
    agora_br = datetime.now(fuso_br)
    hoje_br = agora_br.date()
    hora_atual = agora_br.time()
    corte_t1, corte_t2 = time(13, 30), time(22, 0)

    # Trava do match real pós-estouro de horário da janela de SLA
    def validar_SLA_isolado(row):
        if not row['DEU_MATCH']: return False
        
        dt_col = None
        for c in row.index:
            if "SEQUENCIADO" in str(c).upper():
                dt_col = c
                break
        if not dt_col: return row['DEU_MATCH']
        
        dt_sequenciado = pd.to_datetime(row[dt_col], errors='coerce').date()
        
        if dt_sequenciado == hoje_br:
            turno_col = 'TURNO' if 'TURNO' in row.index else ('TURNO_ALOCADO' if 'TURNO_ALOCADO' in row.index else None)
            if turno_col:
                turno_alocado = str(row[turno_col]).strip()
                if "1" in turno_alocado and hora_atual < corte_t1: return False
                if "2" in turno_alocado and hora_atual < corte_t2: return False
        return row['DEU_MATCH']

    df_modelo['DEU_MATCH_REAL'] = df_modelo.apply(validar_SLA_isolado, axis=1)

    base_date = data_corte_a3.date() if isinstance(data_corte_a3, pd.Timestamp) else pd.to_datetime(data_corte_a3).date()
    datas_tacticas = [base_date - timedelta(days=1), base_date, base_date + timedelta(days=1)]

    # Identifica colunas de filtros temporais
    col_dt_seq = 'DATA SEQUENCIADO' if 'DATA SEQUENCIADO' in df_modelo.columns else 'DT_SEQUENCIADO'
    col_dt_per = 'DT PERCURSO' if 'DT PERCURSO' in df_modelo.columns else 'DT_PERCURSO'

    for dt_date in datas_tacticas:
        dt_formatada = dt_date.strftime('%d/%m/%Y (%a)')
        
        if not df_modelo.empty:
            condicao_seq = (pd.to_datetime(df_modelo[col_dt_seq], errors='coerce').dt.date == dt_date) & (df_modelo['STATUS'] == "SEQUENCIADO")
            condicao_nao_seq = (pd.to_datetime(df_modelo[col_dt_per], errors='coerce').dt.date == dt_date) & (df_modelo['STATUS'] == "NÃO SEQUENCIADO")
            df_dia = df_modelo[condicao_seq | condicao_nao_seq]
        else:
            df_dia = pd.DataFrame()
        
        if df_dia.empty:
            st.markdown(f"⚪ **Horizonte: {dt_formatada}** | Sem atividade de MI registrada")
            st.markdown("---")
            continue

        # Grau de dificuldade diário atrelado à quantidade de caixas fracionadas programadas
        cxs_dia_recebidas = df_dia['CX_REAL'].sum()
        nota_dia = min(10.0, max(1.0, (cxs_dia_recebidas / 230) * 7.5))
        
        cor_header = "🔴" if nota_dia >= 7.5 else ("🟡" if nota_dia >= 5.0 else "🟢")
        header_linha = f"{cor_header} Horizonte: {dt_formatada} | Grau de Dificuldade da Carteira: {round(nota_dia, 1)} / 10"

        with st.expander(header_linha, expanded=(dt_date == base_date)):
            col_t1, col_t2 = st.columns(2)
            
            col_turno_nome = 'TURNO' if 'TURNO' in df_dia.columns else 'TURNO_ALOCADO'

            for turno_num, col_layout in [("1", col_t1), ("2", col_t2)]:
                with col_layout:
                    df_turno = df_dia[df_dia[col_turno_nome].astype(str).str.contains(turno_num, na=False)] if col_turno_nome in df_dia.columns else pd.DataFrame()
                    
                    if df_turno.empty:
                        st.markdown(f"""
                        <div class="perf-turno-box" style="opacity: 0.5;">
                            <div class="perf-header"><div class="perf-turno-title">Turno {turno_num}</div></div>
                            <p style="font-size:0.85rem; color:#64748b; margin:0;">Sem ordens de MI alocadas.</p>
                        </div>
                        """, unsafe_allow_html=True)
                        continue
                    
                    turno_encerrado = True
                    if dt_date == hoje_br:
                        if turno_num == "1" and hora_atual < corte_t1: turno_encerrado = False
                        if turno_num == "2" and hora_atual < corte_t2: turno_encerrado = False
                    elif dt_date > hoje_br:
                        turno_encerrado = False

                    # Separação isolada dos planejados
                    cxs_planejadas = df_turno['CX_REAL'].sum()
                    pls_planejados = df_turno['PL_REAL'].sum()
                    acessos_planejados = df_turno['VOLUME_TOTAL'].sum()
                    
                    # Separação isolada dos executados reais coletados da base geral
                    df_faits_turno = df_turno[df_turno['DEU_MATCH_REAL'] == True]
                    cxs_feitas = df_faits_turno['CX_REAL'].sum()
                    pls_feitas = df_faits_turno['PL_REAL'].sum()
                    acessos_feitos = df_faits_turno['VOLUME_TOTAL'].sum()
                    
                    qtd_percursos_total = df_turno['PERCURSO'].nunique()
                    
                    # Julgamento calibrado: teto de caixas é 230 por turno
                    nota_turno_dificuldade = min(10.0, max(1.0, (cxs_planejadas / 230) * 8.5))
                    eficiencia_SLA = (acessos_feitos / max(1, acessos_planejados) * 100)
                    
                    if not turno_encerrado:
                        badge_html = f'<span class="badge-andamento">⏳ MI EM ANDAMENTO</span>'
                        txt_nota_sub = "Aguardando fim do turno"
                    else:
                        txt_nota_sub = "Veredito de Esforço MI"
                        if nota_turno_dificuldade >= 7.5 and eficiencia_SLA >= 95:
                            badge_html = f'<span class="badge-superacao">🚀 ALTA SATURAÇÃO FRAÇÃO ({round(nota_turno_dificuldade, 1)})</span>'
                        elif eficiencia_SLA >= 100:
                            badge_html = f'<span class="badge-merito">✅ SLA ATENDIDO COM SUCESSO</span>'
                        else:
                            badge_html = f'<span class="badge-atencao">⚠️ QUEBRA DE SLA DIÁRIO ({int(eficiencia_SLA)}%)</span>'

                    # Painel visual com tratamento isolado para a chefia
                    st.markdown(f"""
                    <div class="perf-turno-box">
                        <div class="perf-header">
                            <div class="perf-turno-title">Turno {turno_num}</div>
                            {badge_html}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    sm1, sm2, sm3 = st.columns(3)
                    with sm1:
                        st.markdown(f'<div class="metric-num">{int(cxs_feitas)}</div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="metric-sub">📦 Caixas Concretizadas</div>', unsafe_allow_html=True)
                        st.caption(f"Planejado: {int(cxs_planejadas)} CXS")
                    with sm2:
                        st.markdown(f'<div class="metric-num" style="color:#0f766e;">{int(pls_feitas)}</div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="metric-sub">🪵 Paletes Movimentados</div>', unsafe_allow_html=True)
                        st.caption(f"Planejado: {int(pls_planejados)} PLS")
                    with sm3:
                        st.markdown(f'<div class="metric-num" style="color:#e24a8d;">{round(nota_turno_dificuldade, 1)}</div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="metric-sub">Grau Dificuldade</div>', unsafe_allow_html=True)
                        st.caption(txt_nota_sub)
                    
                    pct_do_esforco_em_fracao = (cxs_planejadas / max(1, acessos_planejados)) * 100
                    st.markdown(f'<div style="border-top: 1px dashed #e2e8f0; padding-top: 8px; margin-top:5px;"></div>', unsafe_allow_html=True)
                    st.markdown(f"""
                    <div class="mix-text">
                        • Total de Rotas Ativas na Noite: <strong>{qtd_percursos_total} percursos</strong><br>
                        • Total Geral de Acessos Computados (SLA): <strong>{int(acessos_feitos)} feitos</strong> de {int(acessos_planejados)} planeados<br>
                        • Concentração de Fracionamento: <strong>{int(pct_do_esforco_em_fracao)}% da carteira do turno é caixa solta</strong>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    with st.expander(f"📋 Roteiros Isolados MI T{turno_num}", expanded=False):
                        df_turno_view = df_turno.copy().drop_duplicates(subset=['PERCURSO'])
                        df_turno_view['Status_SLA'] = df_turno_view['DEU_MATCH_REAL'].map({True: "✅ Concretizado dentro da Janela", False: "⏳ Pendente de Execução"})
                        
                        colunas_exibir = ['PERCURSO']
                        col_canal_check = None
                        for col_v in df_turno_view.columns:
                            if str(col_v).upper().strip() in ['CANAL', 'OPERAÇÃO', 'TRANSPORTADORA']:
                                col_canal_check = col_v
                                break
                        if col_canal_check: colunas_exibir.append(col_canal_check)
                            
                        colunas_exibir.extend(['CX_REAL', 'PL_REAL', 'Status_SLA'])
                        st.dataframe(df_turno_view[colunas_exibir], use_container_width=True, hide_index=True)
        st.markdown("---")
else:
    st.error("Erro ao estruturar base de Desempenho MI.")