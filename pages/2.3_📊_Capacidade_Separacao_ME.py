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

st.set_page_config(page_title="Capacidade ME", layout="wide")

# ─── ESTILIZAÇÃO CSS PREMIUM PARA OS CARDS DO PCO ───
st.markdown("""
<style>
    .pco-card {
        background-color: #f8fafc;
        border-left: 5px solid #1E3A8A;
        border-right: 1px solid #e2e8f0;
        border-top: 1px solid #e2e8f0;
        border-bottom: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 20px;
        height: 100%;
    }
    .pco-card-yellow { border-left-color: #f59e0b; }
    .pco-card-red { border-left-color: #ef4444; }
    
    .pco-title {
        color: #64748b;
        font-size: 0.85rem;
        font-weight: 700;
        text-transform: uppercase;
        margin-bottom: 10px;
        letter-spacing: 0.5px;
    }
    .pco-main-value {
        color: #1e293b;
        font-size: 2.2rem;
        font-weight: 800;
        line-height: 1.1;
    }
    .pco-divider {
        height: 1px;
        background-color: #e2e8f0;
        margin: 12px 0;
    }
    .pco-sub-value {
        color: #475569;
        font-size: 1.1rem;
        font-weight: 600;
    }
    .pco-label {
        color: #94a3b8;
        font-size: 0.8rem;
    }
    .guia-pcp {
        background-color: #f0fdf4;
        border: 1px solid #bbf7d0;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 20px;
    }
    .guia-header {
        color: #166534;
        font-weight: bold;
        font-size: 1.1rem;
        margin-bottom: 8px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>📊 Capacidade & Aderência Tática ME</h1>", unsafe_allow_html=True)
st.markdown("---")

# ─── 📝 CRONOGRAMA DIRETOR DO PCP ───
with st.container():
    st.markdown("""
    <div class="guia-pcp">
        <div class="guia-header">⚡ Cronograma de Sequenciamento Operacional ME</div>
        <div style="font-size: 0.95rem; color: #1e293b; line-height: 1.5;">
            • <b>Turno 2 (Janela Atual):</b> Encerramento de novos sequenciamentos às <b>10h30</b>.<br>
            • <b>Turno 3 e Turno 1 (Próxima Jornada):</b> Sequenciamento fechado e salvo na base às <b>16h30</b>.<br>
            • <b>⚠️ REGRA DE FECHAMENTO:</b> Assim que o turno recebe registro de sequenciamento, a capacidade dele trava no volume alocado. O saldo não utilizado é descartado como perda operacional e não acumula.
        </div>
    </div>
    """, unsafe_allow_html=True)

df_demanda, data_corte_a3, txt_completo_a3 = carregar_dados_separacao()
df_execucao = carregar_execucao_turnos()

if df_demanda is not None and df_execucao is not None:
    
    st.markdown(f"📊 **Status do Sistema:** Última atualização (Célula A3) em `{txt_completo_a3}`")
    
    if isinstance(data_corte_a3, pd.Timestamp):
        data_corte_a3_date = data_corte_a3.date()
    else:
        data_corte_a3_date = pd.to_datetime(data_corte_a3).date()

    df_demanda['PERCURSO'] = df_demanda['PERCURSO'].astype(str).str.strip().str.replace('.0', '', regex=False)
    if 'STATUS' in df_demanda.columns:
        df_demanda['STATUS'] = df_demanda['STATUS'].astype(str).str.upper().str.strip()

    df_modelo = pd.merge(df_demanda, df_execucao, on='PERCURSO', how='left')
    df_modelo['DEU_MATCH'] = df_modelo['TURNO_REALIZOU'].notna()
    
    fuso_br = zoneinfo.ZoneInfo("America/Sao_Paulo")
    agora_br = datetime.now(fuso_br)
    hoje_br = agora_br.date()
    hora_atual = agora_br.time()
    corte_t1, corte_t2 = time(13, 30), time(22, 0)

    def validar_match_por_horario(row):
        if not row['DEU_MATCH']: return False
        dt_sequenciado = pd.to_datetime(row['DT_SEQUENCIADO']).date()
        if dt_sequenciado == hoje_br:
            turno = str(row['TURNO_ALOCADO']).strip()
            if "1" in turno and hora_atual < corte_t1: return False
            if "2" in turno and hora_atual < corte_t2: return False
        return row['DEU_MATCH']

    df_modelo['DEU_MATCH_REAL'] = df_modelo.apply(validar_match_por_horario, axis=1)
    
    datas_planilha = {pd.to_datetime(d) for d in (set(df_modelo['DT_SEQUENCIADO'].dropna().unique()) | set(df_modelo['DT_PERCURSO'].dropna().unique()))}
    dia_anterior = data_corte_a3_date - timedelta(days=1)
    datas_futuras = {pd.to_datetime(data_corte_a3_date + timedelta(days=i)) for i in range(6)} | {pd.to_datetime(dia_anterior)}
    datas_ordenadas = sorted(list(datas_planilha | datas_futuras))
    
    for dt in datas_ordenadas:
        dt_date = dt.date()
        
        condicao_seq = (pd.to_datetime(df_modelo['DT_SEQUENCIADO']).dt.date == dt_date) & (df_modelo['STATUS'] == "SEQUENCIADO")
        condicao_nao_seq = (pd.to_datetime(df_modelo['DT_PERCURSO']).dt.date == dt_date) & (df_modelo['STATUS'] == "NÃO SEQUENCIADO")
        df_dia = df_modelo[condicao_seq | condicao_nao_seq] if not df_modelo.empty else pd.DataFrame()
        
        dt_formatada = dt.strftime('%d/%m/%Y (%a)')
        
        is_sabado = dt.weekday() == 5
        is_domingo = dt.weekday() == 6
        
        # Volumetrias brutas alocadas por turno
        df_seq = df_dia[df_dia['STATUS'] == "SEQUENCIADO"] if not df_dia.empty else pd.DataFrame()
        vol_t1_alocado = df_seq[df_seq['TURNO_ALOCADO'].astype(str).str.contains("1", na=False)]['VOLUME_TOTAL'].sum() if not df_seq.empty else 0
        vol_t2_alocado = df_seq[df_seq['TURNO_ALOCADO'].astype(str).str.contains("2", na=False)]['VOLUME_TOTAL'].sum() if not df_seq.empty else 0
        
        # Capacidades Nominais Padrão
        cap_t1 = 0 if is_domingo else (130 if is_sabado else 260)
        cap_t2 = 0 if is_domingo else (130 if is_sabado else 260)
        
        # ⚡ TRAVA DINÂMICA DE TURNO SEQUENCIADO/ENCERRADO
        if vol_t1_alocado > 0:
            cap_t1 = vol_t1_alocado  # Trava a capacidade exatamente no que foi rodado
        elif dt_date == hoje_br and hora_atual >= corte_t1:
            cap_t1 = 0               # Se passou do horário e está zerado, a capacidade morre
            
        if vol_t2_alocado > 0:
            cap_t2 = vol_t2_alocado  # Trava a capacidade do Turno 2 no volume real existente
        elif dt_date == hoje_br and hora_atual >= corte_t2:
            cap_t2 = 0

        capacidade_total_dia = cap_t1 + cap_t2
        
        vol_seq_total = df_seq['VOLUME_TOTAL'].sum() if not df_seq.empty else 0
        df_nao_seq = df_dia[df_dia['STATUS'] == "NÃO SEQUENCIADO"] if not df_dia.empty else pd.DataFrame()
        vol_nao_seq = df_nao_seq['VOLUME_TOTAL'].sum() if not df_nao_seq.empty else 0
        
        volume_pressionando = (vol_seq_total + vol_nao_seq)
        saldo_vagas = capacidade_total_dia - volume_pressionando

        vol_t1_feito = df_seq[(df_seq['TURNO_ALOCADO'].astype(str).str.contains("1", na=False)) & (df_seq['DEU_MATCH_REAL'] == True)]['VOLUME_TOTAL'].sum() if not df_seq.empty else 0
        vol_t2_feito = df_seq[(df_seq['TURNO_ALOCADO'].astype(str).str.contains("2", na=False)) & (df_seq['DEU_MATCH_REAL'] == True)]['VOLUME_TOTAL'].sum() if not df_seq.empty else 0
        vol_realizado_total = vol_t1_feito + vol_t2_feito

        t1_aguardando = vol_t1_alocado if (dt_date == hoje_br and hora_atual < corte_t1) or dt_date > hoje_br else 0
        t1_retornado = vol_t1_alocado - vol_t1_feito if (dt_date == hoje_br and hora_atual >= corte_t1) or dt_date < hoje_br else 0
        
        t2_aguardando = vol_t2_alocado if (dt_date == hoje_br and hora_atual < corte_t2) or dt_date > hoje_br else 0
        t2_retornado = vol_t2_alocado - vol_t2_feito if (dt_date == hoje_br and hora_atual >= corte_t2) or dt_date < hoje_br else 0
        
        total_aguardando = t1_aguardando + t2_aguardando
        total_retornado = max(0, t1_retornado + t2_retornado)
        
        if dt_date < data_corte_a3_date:
            cor_status = "⚪"
            if vol_realizado_total >= (vol_seq_total + vol_nao_seq) and (vol_seq_total + vol_nao_seq) > 0:
                txt_saldo = "Meta Cumprida: Operação Absorveu e Atendeu 100% da Carga ✅"
            elif total_retornado > 0:
                txt_saldo = f"Dia Concluído com Restrições: {int(total_retornado)} Acessos Não Aderidos ⚠️"
            else:
                txt_saldo = "Data Histórica Finalizada sem Pendências Operacionais ✨"
            expandir_padrao = False  
        elif is_domingo:
            cor_status = "⚪"
            txt_saldo = "Domingo: Fábrica Fechada (Sem Operação Diurna)"
            expandir_padrao = False  
        else:
            if saldo_vagas < 0:
                cor_status = "🔴"
                txt_saldo = f"🚨 RESTRITO: Estouro de Capacidade por {int(abs(saldo_vagas))} Acessos!"
            elif volume_pressionando > 0:
                cor_status = "🟡"
                txt_saldo = f"👍 Disponível para PCP: Suporta mais {int(saldo_vagas)} Acessos"
            else:
                cor_status = "🟢"
                txt_saldo = f"🟢 Liberado para PCP: Janela Totalmente Livre ({int(saldo_vagas)} Vagas)"
            
            expandir_padrao = (dt_date == data_corte_a3_date or saldo_vagas < 0)

        header_card = f"{cor_status} Horizonte: {dt_formatada} ➔ {txt_saldo}"

        with st.expander(header_card, expanded=expandir_padrao):
            m1, m2, m3 = st.columns(3)
            with m1:
                st.markdown(f"""
                <div class="pco-card">
                    <div class="pco-title">Capacidade vs Carga</div>
                    <div class="pco-label">Capacidade Disponível Atualizada</div>
                    <div class="pco-main-value">{capacidade_total_dia} <span style="font-size:1rem; font-weight:400; color:#64748b;">Acessos</span></div>
                    <div class="pco-divider"></div>
                    <div class="pco-label">Total Alocado Pressionando Dia</div>
                    <div class="pco-sub-value" style="color: #1E3A8A;">{int(volume_pressionando)} un</div>
                </div>
                """, unsafe_allow_html=True)
                
                with st.expander("🔎 Detalhe de Recebimento", expanded=False):
                    st.write(f"**Sequenciado Turno 1:** {int(vol_t1_alocado)} un")
                    st.write(f"**Sequenciado Turno 2:** {int(vol_t2_alocado)} un")
                    st.write(f"**Carteira Não Sequenciada:** {int(vol_nao_seq)} un")
            
            with m2:
                st.markdown(f"""
                <div class="pco-card pco-card-yellow">
                    <div class="pco-title">Status do Acompanhamento</div>
                    <div class="pco-label">Volume Realizado Concluído</div>
                    <div class="pco-main-value" style="color: #11caa0;">{int(vol_realizado_total)} <span style="font-size:1rem; font-weight:400; color:#64748b;">Acessos</span></div>
                    <div class="pco-divider"></div>
                    <div class="pco-label">Aguardando Execução da Janela</div>
                    <div class="pco-sub-value" style="color: #f59e0b;">{int(total_aguardando)} un</div>
                </div>
                """, unsafe_allow_html=True)
                
                with st.expander("🔎 Detalhe de Execução", expanded=False):
                    st.write(f"**T1 Concluído:** Fez {int(vol_t1_feito)} un")
                    st.write(f"**T2 Concluído:** Fez {int(vol_t2_feito)} un")
            
            with m3:
                classe_card = "pco-card-red" if total_retornado > 0 else "pco-card"
                st.markdown(f"""
                <div class="pco-card {classe_card}">
                    <div class="pco-title">Alerta de Quebra de Janela (Sobras)</div>
                    <div class="pco-label">Estourou Turno e Virou Sobra Real</div>
                    <div class="pco-main-value" style="color: {'#ef4444' if total_retornado > 0 else '#1e293b'};">{int(total_retornado)} <span style="font-size:1rem; font-weight:400; color:#64748b;">un</span></div>
                    <div class="pco-divider"></div>
                    <div class="pco-label">Carteira Geral Sem Sequência</div>
                    <div class="pco-sub-value">{int(vol_nao_seq)} un</div>
                </div>
                """, unsafe_allow_html=True)
                
                with st.expander("🔎 Detalhe de Impacto de Saldos", expanded=False):
                    st.write(f"**Margem de Vagas Restante para o PCP:** {int(saldo_vagas)} un")

            if not df_dia.empty:
                st.markdown("<br>", unsafe_allow_html=True)
                with st.expander("📋 Inspecionar Detalhamento Faturamento/Roteiros", expanded=False):
                    df_unido_view = df_dia.copy().drop_duplicates(subset=['PERCURSO'])
                    df_unido_view['Data_Origem_Percurso'] = df_unido_view['DT_PERCURSO'].dt.strftime('%d/%m/%Y')
                    df_unido_view['Status_Match'] = df_unido_view['DEU_MATCH_REAL'].map({True: "Bipado / Executado ✅", False: "Pendente / Em Linha ⏳"})
                    st.dataframe(
                        df_unido_view[['PERCURSO', 'VOLUME_TOTAL', 'STATUS', 'Data_Origem_Percurso', 'Status_Match']].rename(columns={
                            'VOLUME_TOTAL': 'Acessos', 'STATUS': 'Status Planilha', 'Data_Origem_Percurso': 'Data do Percurso'
                        }), use_container_width=True, hide_index=True
                    )
else:
    st.error("Erro ao cruzar as bases de dados.")