import streamlit as st
import pandas as pd
from datetime import timedelta, datetime, time
import zoneinfo

# ─── BLOCO DE SEGURANÇA DE CAMINHOS ROBUSTO ───
import sys
from pathlib import Path
raiz = Path(__file__).resolve().parents[1]  # Sobe 1 nível (pages/ -> raiz do projeto)
if str(raiz) not in sys.path:
    sys.path.append(str(raiz))
# ───────────────────────────────────────────────────────────────────────────────────

from src.core.data_loader import carregar_e_tratar_dados, carregar_realizado_ht, carregar_matriz_capacidade

st.set_page_config(page_title="Capacidade HT", layout="wide")

# Título Principal com Design Moderno
st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🚛 Gestão de Capacidade & Estufas HT</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 1.2rem; color: #4B5563;'>Sincronização Avançada: SLA Vivo, Gestão Física de Atrasos e Limpeza de Cards Vazios.</p>", unsafe_allow_html=True)
st.markdown("---")

# ─── 1. RELÓGIO OPERACIONAL DE BRASÍLIA ───
fuso_br = zoneinfo.ZoneInfo("America/Sao_Paulo")
agora_br = datetime.now(fuso_br)
hoje_br = agora_br.date()
hora_atual = agora_br.time()

# ─── 2. CARREGAMENTO DAS BASES CONTÁBEIS E MATRIZES ───
df_ht, txt_completo_a2 = carregar_e_tratar_dados()
df_realizado_ht = carregar_realizado_ht(ano_selecionado=str(hoje_br.year))
_, tracking_pco = carregar_matriz_capacidade()

if df_ht is not None:
    
    # Normalização e preparação de dados
    df_ht['Data_Ajustada'] = pd.to_datetime(df_ht['Data_Carregamento']).dt.normalize()
    df_ht['Total_Plt_Percurso'] = pd.to_numeric(df_ht['Total_Plt_Percurso'], errors='coerce').fillna(0).astype(int)
    
    try:
        dt_a2_str = txt_completo_a2.split()[0]
        data_corte_a2 = pd.to_datetime(dt_a2_str, dayfirst=True, errors='coerce').date()
        if pd.isna(data_corte_a2):
            data_corte_a2 = hoje_br
    except Exception:
        data_corte_a2 = hoje_br

    st.markdown(f"📊 **Status do Sistema:** Última atualização da planilha em `{txt_completo_a2}`")
    
    # ─── 3. ENGENHARIA DE ATRASOS (O SALDO DO PASSADO QUE EMPURRA O PRESENTE) ───
    # Captura tudo o que ficou para trás da data de corte e acumula como Atraso Físico de Pátio
    df_atrasos_retroativos = df_ht[(df_ht['Data_Ajustada'].dt.date < hoje_br) & (df_ht['Total_Plt_Percurso'] > 0)]
    total_pallets_atrasados_geral = int(df_atrasos_retroativos['Total_Plt_Percurso'].sum())

    # ─── 4. PROCESSAMENTO DE ESTRADOS DO DIA ATUAL ───
    fornadas_full = 0
    fornadas_parciais = 0
    estrados_tratados_hoje = 0

    if df_realizado_ht is not None and not df_realizado_ht.empty:
        df_realizado_ht['DATA_PROD'] = pd.to_datetime(df_realizado_ht['DATA_PROD'], errors='coerce')
        df_hoje = df_realizado_ht[df_realizado_ht['DATA_PROD'].dt.date == hoje_br]
        df_estrados_hoje = df_hoje[df_hoje['TIPO_FLUXO'] == 'ESTRADO']
        
        if not df_estrados_hoje.empty:
            resumo_fornadas = df_estrados_hoje.groupby('CONCAT')['PALLETS'].sum().reset_index()
            for idx, row in resumo_fornadas.iterrows():
                qtd_estrados = row['PALLETS']
                estrados_tratados_hoje += qtd_estrados
                if qtd_estrados >= 100: fornadas_full += 1
                elif qtd_estrados > 0: fornadas_parciais += 1

    meta_estrados_pco = tracking_pco.get(('HT', 'TOTAL', 'META', 'ESTRADOS_DIA'), 200)
    perda_capacidade_por_estrado = (fornadas_full * 30) + (fornadas_parciais * 15)

    # ─── PANEL RESUMO PREMIUM DE IMPACTOS (AGORA COM ATRASOS AOS OLHOS DOS OPERADORES) ───
    with st.container():
        st.markdown("""<style>.box-metr { background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 15px; text-align: center; }</style>""", unsafe_allow_html=True)
        c_meta1, c_meta2, c_meta3 = st.columns(3)
        
        with c_meta1:
            st.metric("🪵 Estrados Processados Hoje", f"{estrados_tratados_hoje} un", f"Meta Diária: {meta_estrados_pco} un", delta_color="off")
        with c_meta2:
            # 🚨 ALERTA VERMELHO DE ATRASOS ACUMULADOS
            cor_atraso = "#ef4444" if total_pallets_atrasados_geral > 0 else "#10b981"
            st.markdown(f"""
            <div class="box-metr" style="border-top: 4px solid {cor_atraso};">
                <span style="font-size: 12px; font-weight: bold; color: #64748b; text-transform: uppercase;">🚨 Cargas Retidas / Atrasos Acumulados</span>
                <h2 style="margin: 5px 0 0 0; color: {cor_atraso}; font-size: 24px;">{total_pallets_atrasados_geral} PLT</h2>
                <span style="font-size: 11px; color: #94a3b8;">Impacta diretamente a capacidade física de hoje</span>
            </div>
            """, unsafe_allow_html=True)
        with c_meta3:
            st.metric("📉 Perda por Ocupação Secundária", f"-{perda_capacidade_por_estrado} PLT", "Capacidade subtraída das estufas", delta_color="inverse")

    st.markdown("<br>### 🗓️ Linha do Tempo Dinâmica do HT (SLA Operacional Ativo)", unsafe_allow_html=True)

    # Coleta horizonte futuro para renderizar os cards
    datas_reais_futuras = sorted([d for d in df_ht['Data_Ajustada'].dropna().unique() if pd.to_datetime(d).date() >= hoje_br])
    
    if not datas_reais_futuras:
        datas_reais_futuras = [pd.to_datetime(hoje_br)]

    # ─── 5. MOTOR DE CAPACIDADE DE DEPRECIAÇÃO PELO SLA HORÁRIO ───
    c_t1 = tracking_pco.get(('HT', '1', 'CICLOS', 'POR_TURNO'), 4)
    r_t1 = tracking_pco.get(('HT', '1', 'RENDIMENTO', 'PLTS_POR_CICLO'), 27)
    cap_total_t1 = c_t1 * r_t1

    c_t2 = tracking_pco.get(('HT', '2', 'CICLOS', 'POR_TURNO'), 4)
    r_t2 = tracking_pco.get(('HT', '2', 'RENDIMENTO', 'PLTS_POR_CICLO'), 25)
    cap_total_t2 = c_t2 * r_t2

    c_t3 = tracking_pco.get(('HT', '3', 'CICLOS', 'POR_TURNO'), 4)
    r_t3 = tracking_pco.get(('HT', '3', 'RENDIMENTO', 'PLTS_POR_CICLO'), 25)
    cap_total_t3 = c_t3 * r_t3

    teto_nominal_dia_completo = cap_total_t1 + cap_total_t2 + cap_total_t3

    for dt in datas_reais_futuras:
        dt_date = pd.to_datetime(dt).date()
        dia_semana = dt_date.weekday()
        
        df_cargas_da_data = df_ht[df_ht['Data_Ajustada'] == dt].copy() if not df_ht.empty else pd.DataFrame()
        total_plt_planejado_original = int(df_cargas_da_data['Total_Plt_Percurso'].sum()) if not df_cargas_da_data.empty else 0
        
        # 🌟 REGRA ANTI-POLUIÇÃO: Se o dia não tem nenhuma carga planejada, ignora e pula o card
        if total_plt_planejado_original == 0 and dt_date != hoje_br:
            continue

        dt_formatada = pd.to_datetime(dt).strftime('%d/%m/%Y (%a)')
        
        # ⚡ CALIBRAGEM DO SLA VIVO DA CAPACIDADE CONFORME O TEMPO PASSA
        if dt_date == hoje_br:
            capacidade_corrente = max(0, teto_nominal_dia_completo - perda_capacidade_por_estrado)
            
            # Se a hora passou do fim do Turno 1 (13h30), aquela capacidade morreu na operação física
            if hora_atual >= time(13, 30):
                capacidade_corrente = max(0, capacidade_corrente - cap_total_t1)
            # Se passou do Turno 2 (22h00), a capacidade dele também cai
            if hora_atual >= time(22, 0):
                capacidade_corrente = max(0, capacidade_corrente - cap_total_t2)
                
            # 🚨 REGRA MESTRE: O Dia de hoje recebe o peso das sobras/atrasos acumulados do passado
            carga_total_pressionando = total_plt_planejado_original + total_pallets_atrasados_geral
        else:
            # Dias futuros rodam com capacidade nominal cheia e sem peso de atrasos retroativos diretos
            capacidade_corrente = 0 if dia_semana == 6 else teto_nominal_dia_completo
            carga_total_pressionando = total_plt_planejado_original

        saldo_estufas = capacidade_corrente - carga_total_pressionando
        
        # Definição de Cores e Semáforos Reais
        if capacidade_corrente == 0:
            cor_bolinha = "⚪"
            txt_saldo = f"Janela Encerrada ou Sem Escala Operacional Activa"
        elif saldo_estufas < 0:
            cor_bolinha = "🔴"
            txt_saldo = f"🚨 GARGALO / CRÍTICO: Estouro de pátio por {int(abs(saldo_estufas))} PLT!"
        else:
            cor_bolinha = "🟢" if total_plt_planejado_original == 0 else "专业"
            cor_bolinha = "🟢" if total_plt_planejado_original == 0 else "🟡"
            txt_saldo = f"Fluxo Estável: {int(saldo_estufas)} PLT Livres na Calçada"

        header_card = f"{cor_bolinha} Horizonte: {dt_formatada} ➔ {txt_saldo}"
        expandir_padrao = (dt_date == hoje_br or saldo_estufas < 0)

        with st.expander(header_card, expanded=expandir_padrao):
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("🎯 Teto Disponível Vivo (SLA)", f"{int(capacidade_corrente)} PLT", "Diminui conforme o tempo do turno avança")
            with c2:
                texto_sub_carga = f"Planejado: {total_plt_planejado_original} | Atrasos: {total_pallets_atrasados_geral}" if dt_date == hoje_br else f"Planejado do Dia"
                st.metric("📦 Carga Pressionando Pátio", f"{int(carga_total_pressionando)} PLT", texto_sub_carga)
            with c3:
                st.metric("⚖️ Saldo Real de Alocação", f"{int(saldo_estufas)} PLT", 
                          delta=int(saldo_estufas),
                          delta_color="normal" if saldo_estufas >= 0 else "inverse")
            
            if capacidade_corrente > 0:
                porcentagem_ocupacao = min(1.0, float(carga_total_pressionando / capacidade_corrente))
                st.markdown(f"**Ocupação em Tempo Real:** {int(porcentagem_ocupacao * 100)}%")
                st.progress(porcentagem_ocupacao)

            # Divisão segregada por Modais Úteis (Filtro Interno Anti-Poluição de modais zerados)
            if not df_cargas_da_data.empty:
                df_rodo = df_cargas_da_data[df_cargas_da_data['Modal'].str.contains('Rodoviário', case=False, na=False)]
                df_mari = df_cargas_da_data[df_cargas_da_data['Modal'].str.contains('Marítimo', case=False, na=False)]
                
                col_esq, col_dir = st.columns(2)
                
                with col_esq:
                    # 🌟 SÓ MOSTRA SE TIVER DADO REAL DE RODOVIÁRIO
                    if not df_rodo.empty and df_rodo['Total_Plt_Percurso'].sum() > 0:
                        st.markdown(f'<div style="background-color: #f8fafc; padding: 12px; border-radius: 6px; border-left: 4px solid #007bff; margin-bottom: 10px;"><span style="font-size: 12px; color: #64748b; font-weight: bold;">🚚 Modal Rodoviário</span><h4 style="margin: 3px 0 0 0; color: #1e293b;">{int(df_rodo["Total_Plt_Percurso"].sum())} Plts</h4></div>', unsafe_allow_html=True)
                        with st.expander("Ver Faturas Rodoviário", expanded=False):
                            st.dataframe(df_rodo[['Fatura', 'Percurso', 'Total_Plt_Percurso', 'Status']], use_container_width=True, hide_index=True)
                
                with col_dir:
                    # 🌟 SÓ MOSTRA SE TIVER DADO REAL DE MARÍTIMO
                    if not df_mari.empty and df_mari['Total_Plt_Percurso'].sum() > 0:
                        st.markdown(f'<div style="background-color: #f8fafc; padding: 12px; border-radius: 6px; border-left: 4px solid #16a34a; margin-bottom: 10px;"><span style="font-size: 12px; color: #64748b; font-weight: bold;">🚢 Modal Marítimo</span><h4 style="margin: 3px 0 0 0; color: #1e293b;">{int(df_mari["Total_Plt_Percurso"].sum())} Plts</h4></div>', unsafe_allow_html=True)
                        with st.expander("Ver Faturas Marítimo", expanded=False):
                            st.dataframe(df_mari[['Fatura', 'Percurso', 'Total_Plt_Percurso', 'Status']], use_container_width=True, hide_index=True)
                            
            # Injeta as faturas em atraso real visíveis apenas dentro do card de Hoje para guiar o operador
            if dt_date == hoje_br and total_pallets_atrasados_geral > 0:
                st.error(f"🛑 **Atenção:** Há {total_pallets_atrasados_geral} paletes de dias anteriores retidos na calçada que precisam ser descarregados/estufados com prioridade máxima!")
                with st.expander("🔍 Inspecionar Lista de Faturas em Atraso (Pendências Históricas)", expanded=False):
                    st.dataframe(df_atrasos_retroativos[['Fatura', 'Percurso', 'Total_Plt_Percurso', 'Data_Ajustada', 'Modal']], use_container_width=True, hide_index=True)