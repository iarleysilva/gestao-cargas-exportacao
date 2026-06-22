import streamlit as st
import pandas as pd
from datetime import timedelta, datetime, time
import zoneinfo

# ─── BLOCO DE SEGURANÇA DE CAMINHOS ROBUSTO ───
import sys
from pathlib import Path
raiz = Path(__file__).resolve().parents[2]
if str(raiz) not in sys.path:
    sys.path.append(str(raiz))
# ──────────────────────────────────────────────

from src.core.data_loader import carregar_dados_separacao, carregar_execucao_turnos

st.set_page_config(page_title="Desempenho ME", layout="wide")

# ─── ESTILIZAÇÃO CSS COMPACTA (LADO A LADO) ───
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
        color: #1e3a8a;
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
        background-color: #eff6ff;
        color: #1d4ed8;
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
        line-height: 1.2;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>📈 Desempenho & Complexidade Operacional ME</h1>", unsafe_allow_html=True)
st.markdown("---")

df_demanda, data_corte_a3, txt_completo_a3 = carregar_dados_separacao()
df_execucao = carregar_execucao_turnos()

mapa_pesos = {
    'EXPORTAÇÃO - RODOVIÁRIO TRATAMENTO HT': 2.5,
    'EXPORTAÇÃO - PORTO': 1.0,
    'EXPORTAÇÃO - PORTO CQPA': 5.0,
    'EXPORTAÇÃO - INVERSIONES': 3.0,
    'EXPORTAÇÃO PORTO - FLOOR DECOR': 1.5
}

if df_demanda is not None and df_execucao is not None:
    
    st.markdown(f"📊 **Última Atualização (Célula A3):** `{txt_completo_a3}`")
    
    df_modelo = pd.merge(df_demanda, df_execucao, on='PERCURSO', how='left')
    df_modelo['DEU_MATCH'] = df_modelo['TURNO_REALIZOU'].notna()
    
    col_prioridade = 'PRIORIDADE PERCURSO'
    if col_prioridade not in df_modelo.columns:
        for col in df_modelo.columns:
            if "PRIORIDADE" in col.upper():
                col_prioridade = col
                break
        else:
            df_modelo['PRIORIDADE PERCURSO'] = 'EXPORTAÇÃO - PORTO'
            col_prioridade = 'PRIORIDADE PERCURSO'

    df_modelo[col_prioridade] = df_modelo[col_prioridade].astype(str).str.strip()
    df_modelo['PESO_DIFICULDADE'] = df_modelo[col_prioridade].map(mapa_pesos).fillna(1.0)

    # Relógio do PCO para travar a verdade até o fim real do turno
    fuso_br = zoneinfo.ZoneInfo("America/Sao_Paulo")
    agora_br = datetime.now(fuso_br)
    hoje_br = agora_br.date()
    hora_atual = agora_br.time()
    corte_t1, corte_t2 = time(13, 30), time(22, 0)

    # 🔒 O veredito do MATCH só se consolida após o horário de encerramento do turno
    def validar_match_por_horario(row):
        if not row['DEU_MATCH']: return False
        dt_sequenciado = pd.to_datetime(row['DT_SEQUENCIADO']).date()
        if dt_sequenciado == hoje_br:
            turno = str(row['TURNO_ALOCADO']).strip()
            if "1" in turno and hora_atual < corte_t1: return False
            if "2" in turno and hora_atual < corte_t2: return False
        return row['DEU_MATCH']

    df_modelo['DEU_MATCH_REAL'] = df_modelo.apply(validar_match_por_horario, axis=1)

    if isinstance(data_corte_a3, pd.Timestamp):
        base_date = data_corte_a3.date()
    else:
        base_date = pd.to_datetime(data_corte_a3).date()
        
    datas_tacticas = [base_date - timedelta(days=1), base_date, base_date + timedelta(days=1)]

    for dt_date in datas_tacticas:
        dt_formatada = dt_date.strftime('%d/%m/%Y (%a)')
        
        # Filtro integrado abrangendo sequenciados e não sequenciados da data
        condicao_seq = (pd.to_datetime(df_modelo['DT_SEQUENCIADO']).dt.date == dt_date) & (df_modelo['STATUS'] == "SEQUENCIADO")
        condicao_nao_seq = (pd.to_datetime(df_modelo['DT_PERCURSO']).dt.date == dt_date) & (df_modelo['STATUS'] == "NÃO SEQUENCIADO")
        df_dia = df_modelo[condicao_seq | condicao_nao_seq] if not df_modelo.empty else pd.DataFrame()
        
        if df_dia.empty:
            st.markdown(f"⚪ **Horizonte: {dt_formatada}** | Sem movimentação registrada")
            st.markdown("---")
            continue

        # Nota geral preditiva do dia (Calculada com o match blindado pelo relógio)
        df_dia_feitos = df_dia[df_dia['DEU_MATCH_REAL'] == True]
        vol_dia_feito = df_dia_feitos['VOLUME_TOTAL'].sum() if not df_dia_feitos.empty else 0
        vol_dia_recebido = df_dia['VOLUME_TOTAL'].sum() if not df_dia.empty else 0
        prio_media_dia = df_dia['PESO_DIFICULDADE'].mean() if not df_dia.empty else 1.0
        
        nota_dia = min(10.0, max(1.0, ((vol_dia_feito * prio_media_dia) / max(1, vol_dia_recebido)) * 5))
        cor_header = "🔴" if nota_dia >= 7.5 and vol_dia_feito > 0 else ("🟡" if vol_dia_feito > 0 else "🟢")
        
        header_linha = f"{cor_header} Horizonte: {dt_formatada} | Dificuldade Consolidada: {round(nota_dia, 1)} / 10"

        with st.expander(header_linha, expanded=(dt_date == base_date)):
            col_t1, col_t2 = st.columns(2)
            
            for turno_num, col_layout in [("1", col_t1), ("2", col_t2)]:
                with col_layout:
                    df_turno = df_dia[df_dia['TURNO_ALOCADO'].str.contains(turno_num, na=False)] if 'TURNO_ALOCADO' in df_dia.columns else pd.DataFrame()
                    
                    if df_turno.empty:
                        st.markdown(f"""
                        <div class="perf-turno-box" style="opacity: 0.5;">
                            <div class="perf-header"><div class="perf-turno-title">Turno {turno_num}</div></div>
                            <p style="font-size:0.85rem; color:#64748b; margin:0;">Sem programação para este turno.</p>
                        </div>
                        """, unsafe_allow_html=True)
                        continue
                        
                    is_sabado = dt_date.weekday() == 5
                    meta_turno = 130 if is_sabado else 260
                    
                    # Decide se o turno já encerrou ou está ativo
                    turno_encerrado = True
                    if dt_date == hoje_br:
                        if turno_num == "1" and hora_atual < corte_t1: turno_encerrado = False
                        if turno_num == "2" and hora_atual < corte_t2: turno_encerrado = False
                    elif dt_date > hoje_br:
                        turno_encerrado = False

                    volume_recebido = df_turno['VOLUME_TOTAL'].sum()
                    
                    # ─── 🔒 APLICAÇÃO DA TRAVA OPERACIONAL NO PROCESSO ───
                    # O volume feito oficial só pontua com base no DEU_MATCH_REAL (Pós-corte)
                    df_faits_turno = df_turno[df_turno['DEU_MATCH_REAL'] == True]
                    volume_feito = df_faits_turno['VOLUME_TOTAL'].sum()
                    
                    qtd_percursos_total = df_turno['PERCURSO'].nunique()
                    peso_medio_mix = df_turno['PESO_DIFICULDADE'].mean() if qtd_percursos_total > 0 else 1.0
                    
                    fator_esforco_real = volume_feito * peso_medio_mix
                    nota_dificuldade = min(10.0, max(1.0, (fator_esforco_real / meta_turno) * 5))
                    eficiencia_porcentagem = (volume_feito / volume_recebido * 100) if volume_recebido > 0 else 0.0
                    
                    # Gerenciamento de crachás respeitando o relógio do pátio
                    if not turno_encerrado:
                        badge_html = f'<span class="badge-andamento">⏳ TURNO EM ANDAMENTO</span>'
                        # Para fins visuais enquanto roda, mostra o que está acumulando temporariamente sem fechar a nota final
                        vol_acumulado_temp = df_turno[df_turno['DEU_MATCH'] == True]['VOLUME_TOTAL'].sum()
                        txt_nota_sub = f"Acumulado Temp: {int(vol_acumulado_temp)} un"
                    else:
                        txt_nota_sub = "Veredito Consolidado"
                        if nota_dificuldade >= 8.5 and eficiencia_porcentagem >= 95:
                            badge_html = f'<span class="badge-superacao">🚀 SUPERAÇÃO EXTREMA ({round(nota_dificuldade, 1)})</span>'
                        elif eficiencia_porcentagem >= 100:
                            badge_html = f'<span class="badge-merito">✅ META ATENDIDA ({int(eficiencia_porcentagem)}%)</span>'
                        else:
                            badge_html = f'<span class="badge-atencao">⚠️ ATENÇÃO OPERACIONAL ({int(eficiencia_porcentagem)}%)</span>'

                    # Card do Turno
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
                        st.markdown(f'<div class="metric-num">{int(volume_feito)}</div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="metric-sub">Entregue (un)</div>', unsafe_allow_html=True)
                        st.caption(f"Recebido: {int(volume_recebido)}")
                    with sm2:
                        st.markdown(f'<div class="metric-num" style="color:#11caa0;">{qtd_percursos_total}</div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="metric-sub">Rotas Ativas</div>', unsafe_allow_html=True)
                        st.caption(f"Peso Médio: {round(peso_medio_mix, 2)}")
                    with sm3:
                        # Se não encerrou a nota fica neutra (1.0) ou exibe a parcial real pós-corte
                        exibir_nota = 1.0 if not turno_encerrado else nota_dificuldade
                        cor_nota = "#ef4444" if exibir_nota >= 7.5 else ("#f59e0b" if exibir_nota >= 5.0 else "#11caa0")
                        st.markdown(f'<div class="metric-num" style="color:{cor_nota};">{round(exibir_nota, 1)}</div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="metric-sub">Nota Dif.</div>', unsafe_allow_html=True)
                        st.caption(txt_nota_sub)
                    
                    df_contagem_prioridade = df_turno.groupby(col_prioridade)['PERCURSO'].nunique().reset_index()
                    resumo_prioridades = ""
                    for _, row_prio in df_contagem_prioridade.iterrows():
                        resumo_prioridades += f"• {row_prio[col_prioridade]}: **{row_prio['PERCURSO']}** rotas<br>"
                    
                    st.markdown(f'<div style="border-top: 1px dashed #e2e8f0; padding-top: 8px; margin-top:5px;"></div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="mix-text">{resumo_prioridades}</div>', unsafe_allow_html=True)
                    
                    with st.expander(f"📋 Roteiros T{turno_num}", expanded=False):
                        df_turno_view = df_turno.copy().drop_duplicates(subset=['PERCURSO'])
                        df_turno_view['Status'] = df_turno_view['DEU_MATCH_REAL'].map({True: "✅ Bipado (Consolidado)", False: "⏳ Na esteira / Sem corte"})
                        st.dataframe(df_turno_view[['PERCURSO', 'VOLUME_TOTAL', 'Status']], width="stretch", hide_index=True)
        st.markdown("---")
else:
    st.error("Erro ao estruturar base de Desempenho.")