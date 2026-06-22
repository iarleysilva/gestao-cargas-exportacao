import streamlit as st
import pandas as pd
from datetime import timedelta, datetime, time  # <--- CORRIGIDO: Inclusão do 'time' nativo
import zoneinfo

# ─── BLOCO DE SEGURANÇA DE CAMINHOS ROBUSTO (AJUSTADO PARA ARQUIVO SOLTO EM PAGES) ───
import sys
from pathlib import Path
raiz = Path(__file__).resolve().parents[1]  # Sobe 1 nível (pages/ -> raiz do projeto)
if str(raiz) not in sys.path:
    sys.path.append(str(raiz))
# ───────────────────────────────────────────────────────────────────────────────────

# CORRIGIDO: Removido a importação fantasma de 'carregar_faturamento_ht'
from src.core.data_loader import carregar_e_tratar_dados, carregar_realizado_ht, carregar_matriz_capacidade

st.set_page_config(page_title="Capacidade HT", layout="wide")

# Título Principal com Design Moderno
st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🚛 Gestão de Capacidade & Estufas HT</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 1.2rem; color: #4B5563;'>Sincronização em tempo real entre Linha de Tempo Operacional e Impactos de Chão de Fábrica.</p>", unsafe_allow_html=True)
st.markdown("---")

# ─── 1. RELÓGIO OPERACIONAL DE BRASÍLIA ───
fuso_br = zoneinfo.ZoneInfo("America/Sao_Paulo")
agora_br = datetime.now(fuso_br)
hoje_br = agora_br.date()
hora_atual = agora_br.time()

# ─── 2. CARREGAMENTO DAS BASES ───
df_ht, txt_completo_a2 = carregar_e_tratar_dados()
df_realizado_ht = carregar_realizado_ht(ano_selecionado=str(hoje_br.year))

# 🔌 INTEGRAÇÃO DO NOVO MOTOR DE CAPACIDADE DO PCO
_, tracking_pco = carregar_matriz_capacidade()

if df_ht is not None:
    
    try:
        dt_a2_str = txt_completo_a2.split()[0]
        data_corte_a2 = pd.to_datetime(dt_a2_str, dayfirst=True, errors='coerce')
        if pd.isna(data_corte_a2):
            data_corte_a2 = pd.to_datetime(pd.Timestamp.now().date())
    except Exception:
        data_corte_a2 = pd.to_datetime(pd.Timestamp.now().date())

    # Barra de Status Superior Clean
    st.markdown(f"📊 **Status do Sistema:** Última atualização da planilha (Célula A2) em `{txt_completo_a2}`")
    
    # ─── 3. PROCESSAMENTO DE ESTRADOS ───
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
                if qtd_estrados >= 100:
                    fornadas_full += 1
                elif qtd_estrados > 0:
                    fornadas_parciais += 1

    # Captura a meta padrão de estrados parametrizada na planilha
    meta_estrados_pco = tracking_pco.get(('HT', 'TOTAL', 'META', 'ESTRADOS_DIA'), 200)

    # ─── PANEL RESUMO DE IMPACTOS ───
    with st.expander("🔬 Resumo de Impactos e Justificativas de Fábrica (PCO)", expanded=True):
        m1, m2 = st.columns(2)
        m1.metric("🪵 Estrados Processados Hoje", f"{estrados_tratados_hoje} un", f"Meta Diária Planilha: {meta_estrados_pco} un", delta_color="off")
        
        perda_capacidade_por_estrado = (fornadas_full * 30) + (fornadas_parciais * 15)
        m2.metric("📉 Perda de Capacidade (Carga)", f"-{perda_capacidade_por_estrado} PLT", delta_color="inverse")

    st.markdown("### 🗓️ Linha do Tempo de Carregamento")

    df_ht['Data_Ajustada'] = pd.to_datetime(df_ht['Data_Carregamento']).dt.normalize()
    df_com_volume = df_ht[df_ht['Total_Plt_Percurso'] > 0]
    datas_reais = set(df_com_volume['Data_Ajustada'].dropna().unique())
    datas_reais = {pd.to_datetime(d) for d in datas_reais}
    
    if datas_reais:
        menor_data = min(datas_reais)
        inicio_timeline = min(menor_data, data_corte_a2)
        maior_data_real = max(datas_reais)
        fim_timeline = maior_data_real + timedelta(days=1)
        if fim_timeline.weekday() == 6:
            fim_timeline += timedelta(days=1)
            
        total_dias_intervalo = (fim_timeline - inicio_timeline).days + 1
        sequencia_continua = {inicio_timeline + timedelta(days=i) for i in range(total_dias_intervalo)}
        datas_para_renderizar = sorted(list(sequencia_continua))
    else:
        datas_para_renderizar = [data_corte_a2]

    # ─── 4. RENDERIZAÇÃO ESTÉTICA DA TIMELINE DINÂMICA COMPLETA ───
    for dt in datas_para_renderizar:
        dt_date = dt.date()
        dia_semana = dt.weekday()
        
        df_cargas_da_data = df_ht[df_ht['Data_Ajustada'] == dt] if not df_ht.empty else pd.DataFrame()
        total_plt_planejado = df_cargas_da_data['Total_Plt_Percurso'].sum() if not df_cargas_da_data.empty else 0
        dt_formatada = dt.strftime('%d/%m/%Y (%a)')
        
        # 📊 1. CAPTURA DOS 3 TURNOS DO PCO
        c_t1 = tracking_pco.get(('HT', '1', 'CICLOS', 'POR_TURNO'), tracking_pco.get(('HT', '1.0', 'CICLOS', 'POR_TURNO'), 4))
        r_t1 = tracking_pco.get(('HT', '1', 'RENDIMENTO', 'PLTS_POR_CICLO'), tracking_pco.get(('HT', '1.0', 'RENDIMENTO', 'PLTS_POR_CICLO'), 27))
        
        c_t2 = tracking_pco.get(('HT', '2', 'CICLOS', 'POR_TURNO'), tracking_pco.get(('HT', '2.0', 'CICLOS', 'POR_TURNO'), 4))
        r_t2 = tracking_pco.get(('HT', '2', 'RENDIMENTO', 'PLTS_POR_CICLO'), tracking_pco.get(('HT', '2.0', 'RENDIMENTO', 'PLTS_POR_CICLO'), 25))
        
        c_t3 = tracking_pco.get(('HT', '3', 'CICLOS', 'POR_TURNO'), tracking_pco.get(('HT', '3.0', 'CICLOS', 'POR_TURNO'), 4))
        r_t3 = tracking_pco.get(('HT', '3', 'RENDIMENTO', 'PLTS_POR_CICLO'), tracking_pco.get(('HT', '3.0', 'RENDIMENTO', 'PLTS_POR_CICLO'), 25))
        
        # 📊 2. CAPTURA DO TETO COMPLETO DO DIA (Soma de T1 + T2 + T3)
        teto_dia_completo = (c_t1 * r_t1) + (c_t2 * r_t2) + (c_t3 * r_t3)
        
        if dt_date == hoje_br:
            capacidade_base_dia = max(0, teto_dia_completo - perda_capacidade_por_estrado)
        else:
            capacidade_base_dia = teto_dia_completo

        # Regra de Jornada e Paradas de Fim de Semana
        is_parada_fim_de_semana = False
        if dt_date == hoje_br:
            if dia_semana == 5 and hora_atual >= time(22, 0):
                is_parada_fim_de_semana = True
            elif dia_semana == 6 and hora_atual < time(22, 0):
                is_parada_fim_de_semana = True
                
            capacidade_nominal_ht = 0 if is_parada_fim_de_semana else capacidade_base_dia
            
            # Descontos parciais baseados na capacidade dinâmica informada pelo PCO
            if not is_parada_fim_de_semana:
                if hora_atual >= time(13, 30):
                    capacidade_nominal_ht = max(0, capacidade_nominal_ht - (c_t1 * r_t1))
                if hora_atual >= time(22, 0):
                    capacidade_nominal_ht = max(0, capacidade_nominal_ht - (c_t2 * r_t2))
        else:
            capacidade_nominal_ht = 0 if dia_semana == 6 else capacidade_base_dia

        # Semáforos e Identificação de Títulos dos Cards
        if dt < data_corte_a2:
            if total_plt_planejado <= 0: continue
            cor_bolinha = "⚪"
            txt_saldo = f"Pendências Represadas: {total_plt_planejado} PLT"
        elif capacidade_nominal_ht == 0 and total_plt_planejado <= 0:
            continue
        elif capacidade_nominal_ht == 0 and total_plt_planejado > 0:
            cor_bolinha = "⚪"
            txt_saldo = f"Aviso: Parada de Fábrica com {total_plt_planejado} PLT Planejados"
        else:
            saldo_disponivel = capacidade_nominal_ht - total_plt_planejado
            if total_plt_planejado == 0:
                cor_bolinha = "🟢"
                txt_saldo = f"VAGA LIVRE: {saldo_disponivel} PLT Disponíveis"
            elif saldo_disponivel < 0:
                cor_bolinha = "🔴"
                txt_saldo = f"ESTOURO DE CAPACIDADE: {saldo_disponivel} PLT"
            else:
                cor_bolinha = "🟡"
                txt_saldo = f"Operação Estável: {saldo_disponivel} PLT de Saldo"
                
        header_card = f"{cor_bolinha} {dt_formatada} ➔ {txt_saldo}"
        expandir_padrao = (dt == data_corte_a2 or total_plt_planejado == 0 or (capacidade_nominal_ht - total_plt_planejado) < 0)
        
        with st.expander(header_card, expanded=expandir_padrao):
            c1, c2, c3 = st.columns(3)
            
            with c1:
                st.metric("🎯 Teto Disponível (Estimativa PCO)", f"{capacidade_nominal_ht} PLT", f"Turnos parametrizados ativos")
            with c2:
                st.metric("📦 Carga Planejada", f"{total_plt_planejado} PLT", f"{round(total_plt_planejado / 27, 1)} Estufas" if total_plt_planejado > 0 else "0 Estufas")
            with c3:
                saldo_atual_card = capacidade_nominal_ht - total_plt_planejado
                st.metric("⚖️ Saldo Real de Pátio", f"{saldo_atual_card} PLT", 
                          delta=saldo_atual_card if saldo_atual_card >= 0 else saldo_atual_card,
                          delta_color="normal" if saldo_atual_card >= 0 else "inverse")
            
            if capacidade_nominal_ht > 0:
                porcentagem_ocupacao = min(1.0, float(total_plt_planejado / capacidade_nominal_ht))
                st.markdown(f"**Ocupação Física do HT:** {int(porcentagem_ocupacao * 100)}%")
                st.progress(porcentagem_ocupacao)
            
            if dt < data_corte_a2:
                st.error("🛑 **Cargas Atrasadas Detectadas:** Estes paletes estão ocupando espaço físico precioso e travando as docas.")
            elif total_plt_planejado == 0:
                st.success("✨ **Janela Totalmente Livre:** Excelente momento para o PCO antecipar percursos e diluir o pátio.")
            elif (capacidade_nominal_ht - total_plt_planejado) < 0:
                st.warning(f"🚨 **Gargalo de Escoamento:** O volume alocado supera o limite físico disponível para a jornada atual.")
            else:
                st.info("🔋 **Fluxo Equilibrado:** O volume programado está perfeitamente alinhado com a capacidade operacional.")
                    
            if not df_cargas_da_data.empty:
                with st.expander("🔎 Clique para ver o detalhamento técnico das faturas", expanded=False):
                    st.dataframe(
                        df_cargas_da_data[['Fatura', 'Percurso', 'Total_Plt_Percurso', 'Status', 'Modal']].rename(columns={
                            'Total_Plt_Percurso': 'Paletes', 'Status': 'Status Atual'
                        }), use_container_width=True, hide_index=True
                    )