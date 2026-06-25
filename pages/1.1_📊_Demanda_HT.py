import streamlit as st
import os
import pandas as pd
from datetime import datetime, timedelta, time
import zoneinfo

# ─── BLOCO DE SEGURANÇA DE CAMINHOS ROBUSTO ───
import sys
from pathlib import Path
raiz = Path(__file__).resolve().parents[1]  # Sobe 1 nível (pages/ -> raiz)
if str(raiz) not in sys.path:
    sys.path.append(str(raiz))
# ───────────────────────────────────────────────────────────────────────────────────

from src.core.data_loader import carregar_e_tratar_dados, carregar_realizado_ht, carregar_matriz_capacidade

# 1. Configuração Única da Página
st.set_page_config(
    page_title="Gestão de Cargas - Exportação",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Relógio Operacional Oficial de Brasília
fuso_br = zoneinfo.ZoneInfo("America/Sao_Paulo")
agora_br = datetime.now(fuso_br)
hoje_br = agora_br.date()
hora_atual = agora_br.time()

# 2. Carrega as bases unificadas de dados e as metas dinâmicas do PCO
df, ultima_atualizacao = carregar_e_tratar_dados()
df_realizado_ht = carregar_realizado_ht(ano_selecionado=str(hoje_br.year))
_, tracking_pco = carregar_matriz_capacidade()

# 3. Barra Lateral (Sidebar) com o Card de Última Atualização real do Sheets
st.sidebar.title("🚢 Navegação & Status")
st.sidebar.write(f"⏰ **Relógio Sistema:** {agora_br.strftime('%H:%M')}")

if df is not None:
    st.sidebar.info(f"**Última Atualização da Base:**\n{ultima_atualizacao}")
else:
    st.sidebar.error("⚠️ Não foi possível carregar a base de dados do Google Sheets.")
    st.stop()

# 4. Título Principal do Aplicativo
st.title("📊 Acompanhamento de Cargas de Exportação")

if df is not None:
    # Garante que a coluna de paletes é numérica para as validações de maior que zero
    df['Total_Plt_Percurso'] = pd.to_numeric(df['Total_Plt_Percurso'], errors='coerce').fillna(0).astype(int)
    
    # ABAS PRINCIPAIS DO SISTEMA
    tab_indicadores, tab_sobras, tab_consulta = st.tabs([
        "📈 Indicadores Gerais", 
        "⚠️ Carteira Geral de Sobras (Não Sequenciadas)", 
        "🔍 Consulta por Fatura/Percurso"
    ])
    
    colunas_exibicao = ['Status', 'Fatura', 'Percurso', 'Total_Plt_Percurso', 'Data_Carregamento', 'Modal']
    df_validos = df[df['Total_Plt_Percurso'] > 0].copy()
    
    estilo_card_topo = """
    <div style="
        background-color: #f1f3f5; 
        padding: 15px; 
        border-radius: 8px; 
        border-top: 4px solid {cor}; 
        box-shadow: 1px 1px 3px rgba(0,0,0,0.05);
        text-align: center;
        margin-bottom: 15px;">
        <span style="font-size: 13px; color: #495057; font-weight: bold; text-transform: uppercase;">{titulo}</span>
        <h2 style="margin: 5px 0 0 0; color: #212529; font-size: 26px;">{valor}</h2>
        <span style="font-size: 11px; color: #6c757d;">{subtitulo}</span>
    </div>
    """

    # ─────────────────────────────────────────────────────────────────
    # ABA 1: INDICADORES GERAIS (Governança e Janelas de Auditoria)
    # ─────────────────────────────────────────────────────────────────
    with tab_indicadores:
        st.markdown("### 📈 Painel de Capacidade e Volumetria")
        st.write("Acompanhamento fixo dos principais períodos e consulta personalizada por data.")
        st.markdown("---")
        
        hoje = pd.Timestamp(hoje_br)
        amanha = hoje + pd.Timedelta(days=1)
        
        df_hoje = df_validos[df_validos['Data_Carregamento'].dt.date == hoje_br]
        total_plts_hoje = int(df_hoje['Total_Plt_Percurso'].sum())
        
        df_amanha = df_validos[df_validos['Data_Carregamento'].dt.date == amanha.date()]
        total_plts_amanha = int(df_amanha['Total_Plt_Percurso'].sum())

        total_plts_geral = int(df_validos['Total_Plt_Percurso'].sum())
        cargas_geral = len(df_validos)
        
        # 🚢 QUEBRA ANALÍTICA DE MODAIS POR PERÍODO
        m_hoje_mari = len(df_hoje[df_hoje['Modal'].str.contains('Marítimo', case=False, na=False)])
        m_hoje_rodo = len(df_hoje[df_hoje['Modal'].str.contains('Rodoviário', case=False, na=False)])

        m_amanha_mari = len(df_amanha[df_amanha['Modal'].str.contains('Marítimo', case=False, na=False)])
        m_amanha_rodo = len(df_amanha[df_amanha['Modal'].str.contains('Rodoviário', case=False, na=False)])

        m_geral_mari = len(df_validos[df_validos['Modal'].str.contains('Marítimo', case=False, na=False)])
        m_geral_rodo = len(df_validos[df_validos['Modal'].str.contains('Rodoviário', case=False, na=False)])
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(estilo_card_topo.format(cor="#dc3545", titulo="🚨 Programado para Hoje", valor=f"{total_plts_hoje} Plts", subtitulo=f"🚢 Marítimo: {m_hoje_mari} | 🚚 Rodo: {m_hoje_rodo} ({len(df_hoje)} cargas)"), unsafe_allow_html=True)
        with c2:
            st.markdown(estilo_card_topo.format(cor="#ffc107", titulo="📅 Programado para Amanhã", valor=f"{total_plts_amanha} Plts", subtitulo=f"🚢 Marítimo: {m_amanha_mari} | 🚚 Rodo: {m_amanha_rodo} ({len(df_amanha)} cargas)"), unsafe_allow_html=True)
        with c3:
            st.markdown(estilo_card_topo.format(cor="#6c757d", titulo="📊 Total Geral em Aberto", valor=f"{total_plts_geral} Plts", subtitulo=f"🚢 Marítimo: {m_geral_mari} | 🚚 Rodo: {m_geral_rodo} ({cargas_geral} cargas)"), unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # ─── ⚖️ MOTOR DE GOVERNANÇA DE PÁTIO DINÂMICO ───
        st.markdown("### ⏱ ...")
        st.markdown("### ⏱️ Governança de Pátio e Validação de Turnos (Hoje)")
        
        # Recuperação das capacidades padrão do PCO
        ciclos_t1 = tracking_pco.get(('HT', '1', 'CICLOS', 'POR_TURNO'), tracking_pco.get(('HT', '1.0', 'CICLOS', 'POR_TURNO'), 4))
        rend_t1 = tracking_pco.get(('HT', '1', 'RENDIMENTO', 'PLTS_POR_CICLO'), tracking_pco.get(('HT', '1.0', 'RENDIMENTO', 'PLTS_POR_CICLO'), 27))
        estimativa_t1 = ciclos_t1 * rend_t1 

        ciclos_t2 = tracking_pco.get(('HT', '2', 'CICLOS', 'POR_TURNO'), tracking_pco.get(('HT', '2.0', 'CICLOS', 'POR_TURNO'), 4))
        rend_t2 = tracking_pco.get(('HT', '2', 'RENDIMENTO', 'PLTS_POR_CICLO'), tracking_pco.get(('HT', '2.0', 'RENDIMENTO', 'PLTS_POR_CICLO'), 25))
        estimativa_t2 = ciclos_t2 * rend_t2 

        ciclos_t3 = tracking_pco.get(('HT', '3', 'CICLOS', 'POR_TURNO'), tracking_pco.get(('HT', '3.0', 'CICLOS', 'POR_TURNO'), 4))
        rend_t3 = tracking_pco.get(('HT', '3', 'RENDIMENTO', 'PLTS_POR_CICLO'), tracking_pco.get(('HT', '3.0', 'RENDIMENTO', 'PLTS_POR_CICLO'), 25))
        estimativa_t3 = ciclos_t3 * rend_t3
        
        # 🛡️ FIX DO RECONHECIMENTO DE TURNOS (DADO CONECTADO COM A PERFORMANCE 3.1)
        # Isola estritamente as strings de turnos com tratamento anti-espaço para não misturar os dados
        df_real_hoje = df_realizado_ht[df_realizado_ht['DATA_PROD'].dt.date == hoje_br].copy() if df_realizado_ht is not None else pd.DataFrame()
        if not df_real_hoje.empty:
            df_real_hoje['TURNO_LIMPO'] = df_real_hoje['TURNO'].astype(str).str.replace(" ", "", regex=False).str.upper()
            t1_confirmado = df_real_hoje[df_real_hoje['TURNO_LIMPO'] == "TURNOI"]['PALLETS'].sum()
            t2_confirmado = df_real_hoje[df_real_hoje['TURNO_LIMPO'] == "TURNOII"]['PALLETS'].sum()
            t3_confirmado = df_real_hoje[df_real_hoje['TURNO_LIMPO'] == "TURNOIII"]['PALLETS'].sum()
        else:
            t1_confirmado, t2_confirmado, t3_confirmado = 0, 0, 0
        
        dia_semana_hoje = hoje_br.weekday()

        # Inicialização das variáveis operacionais
        status_t1_txt, status_t2_txt, status_t3_txt = "Aguardando", "Aguardando", "Aguardando"
        cor_t1, cor_t2, cor_t3 = "#64748b", "#64748b", "#64748b"
        carga_real_t1, carga_real_t2, carga_real_t3 = 0, 0, 0

        # 🧠 FUNÇÃO OPERACIONAL INTERNA DE CÁLCULO E ANÁLISE DE RAIO-X DE METAS COM JUSTIFICATIVAS
        def analisar_SLA_e_mix_hoje(real, planejado, turno_tag):
            if planejado <= 0:
                return ""
            perf_pct = ((real / planejado) - 1) * 100
            
            df_bipes_turno = df_real_hoje[df_real_hoje['TURNO_LIMPO'] == turno_tag] if not df_real_hoje.empty else pd.DataFrame()
            v_carga = int(df_bipes_turno[df_bipes_turno['TIPO_FLUXO'] == 'CARGA']['PALLETS'].sum())
            v_estrado = int(df_bipes_turno[df_bipes_turno['TIPO_FLUXO'] == 'ESTRADO']['PALLETS'].sum())
            
            detalhe_volumes = f"<br><span style='font-size:11px; color:#475569;'>📦 Carga: {v_carga} PLT | 🪵 Estrado: {v_estrado} PLT</span>"
            
            if perf_pct >= 0:
                return f" <span style='color:#25a244; font-weight:bold;'> (+{perf_pct:.1f}% Superou Meta)</span>{detalhe_volumes}"
            else:
                justificativa = " (Onerado por Estrados 🪵)" if v_estrado > 0 else " (Abaixo da Meta)"
                return f" <span style='color:#dc3545; font-weight:bold;'> ({perf_pct:.1f}% Recuo)</span>{justificativa}{detalhe_volumes}"

        if dia_semana_hoje == 6:  # Domingo
            status_t1_txt = "🛑 Fábrica Fechada (Plantão inicia às 22h)"
            status_t2_txt = "🛑 Fábrica Fechada (Plantão inicia às 22h)"
            carga_real_t1, carga_real_t2, carga_real_t3 = 0, 0, 0
            perf_t1_html, perf_t2_html, perf_t3_html = "", "", ""
        else:
            # ─── LOGIC TRAP: TURNO 1 DYNAMIC SLA ───
            if hora_atual < time(5, 0):
                status_t1_txt = "⏳ Aguardando Início de Turno"
                cor_t1 = "#64748b"
                carga_real_t1 = 0
                perf_t1_html = ""
            elif time(5, 0) <= hora_atual < time(13, 30):
                status_t1_txt = "⚙️ Em Andamento / Previsto"
                cor_t1 = "#007ebd"
                carga_real_t1 = t1_confirmado  # Mostra o andamento real parcial da performance
                perf_t1_html = analisar_SLA_e_mix_hoje(carga_real_t1, estimativa_t1, 'TURNOI')
            elif time(13, 30) <= hora_atual < time(13, 45):
                status_t1_txt = "⏳ Fim de Turno - Aguardando Auditoria"
                cor_t1 = "#d97706"
                carga_real_t1 = t1_confirmado
                perf_t1_html = analisar_SLA_e_mix_hoje(carga_real_t1, estimativa_t1, 'TURNOI')
            else:
                status_t1_txt = "✅ Concluído e Consolidado" if t1_confirmado > 0 else "❌ Finalizado Sem Informação"
                cor_t1 = "#25a244" if t1_confirmado > 0 else "#475569"
                carga_real_t1 = t1_confirmado
                perf_t1_html = analisar_SLA_e_mix_hoje(carga_real_t1, estimativa_t1, 'TURNOI') if t1_confirmado > 0 else ""

            # ─── LOGIC TRAP: TURNO 2 DYNAMIC SLA ───
            if hora_atual < time(13, 30):
                status_t2_txt = "⏳ Aguardando Início de Turno"
                cor_t2 = "#64748b"
                carga_real_t2 = 0
                perf_t2_html = ""
            elif time(13, 30) <= hora_atual < time(22, 0):
                status_t2_txt = "⚙️ Em Andamento / Previsto"
                cor_t2 = "#007ebd"
                carga_real_t2 = t2_confirmado
                perf_t2_html = analisar_SLA_e_mix_hoje(carga_real_t2, estimativa_t2, 'TURNOII')
            elif time(22, 0) <= hora_atual < time(22, 15):
                status_t2_txt = "⏳ Fim de Turno - Aguardando Auditoria"
                cor_t2 = "#d97706"
                carga_real_t2 = t2_confirmado
                perf_t2_html = analisar_SLA_e_mix_hoje(carga_real_t2, estimativa_t2, 'TURNOII')
            else:
                status_t2_txt = "✅ Concluído e Consolidado" if t2_confirmado > 0 else "❌ Finalizado Sem Informação"
                cor_t2 = "#25a244" if t2_confirmado > 0 else "#475569"
                carga_real_t2 = t2_confirmado
                perf_t2_html = analisar_SLA_e_mix_hoje(carga_real_t2, estimativa_t2, 'TURNOII') if t2_confirmado > 0 else ""

        # ─── LOGIC TRAP: TURNO 3 DYNAMIC SLA ───
        if dia_semana_hoje == 5 and hora_atual >= time(22, 0):
            status_t3_txt = "🛑 Fim de Plantão (Retorno Domingo 22h)"
            carga_real_t3 = 0
            perf_t3_html = ""
        elif dia_semana_hoje == 6 and hora_atual < time(22, 0):
            status_t3_txt = "⏳ Aguardando Início do Plantão Noturno"
            carga_real_t3 = 0
            perf_t3_html = ""
        else:
            if hora_atual >= time(22, 0) or hora_atual < time(5, 0):
                status_t3_txt = "⚙️ Noturno Em Andamento ➔ (Jornada Segunda)" if dia_semana_hoje == 6 else "⚙️ Noturno Em Andamento"
                cor_t3 = "#007ebd"
                carga_real_t3 = t3_confirmado
                perf_t3_html = analisar_SLA_e_mix_hoje(carga_real_t3, estimativa_t3, 'TURNOIII')
                
                # Engenharia de degradação temporal das estufas
                if hora_atual >= time(2, 0) and hora_atual < time(5, 0) and t3_confirmado == 0:
                    horas_ociosas = (agora_br - agora_br.replace(hour=2, minute=0, second=0)).seconds // 3600
                    ciclos_perdidos = min(int(horas_ociosas // 2) + 1, ciclos_t3)
                    estimativa_t3 = max(0, (ciclos_t3 - ciclos_perdidos) * rend_t3)
                    status_t3_txt = f"⚙️ Noturno Ocioso (Perda de {ciclos_perdidos} Estufas)"
                    cor_t3 = "#ea580c"
                    perf_t3_html = analisar_SLA_e_mix_hoje(carga_real_t3, estimativa_t3, 'TURNOIII')
            elif time(5, 0) <= hora_atual < time(5, 15):
                status_t3_txt = "⏳ Fim de Turno - Aguardando Auditoria"
                cor_t3 = "#d97706"
                carga_real_t3 = t3_confirmado
                perf_t3_html = analisar_SLA_e_mix_hoje(carga_real_t3, estimativa_t3, 'TURNOIII')
            else:
                status_t3_txt = "✅ Concluído e Consolidado" if t3_confirmado > 0 else "❌ Finalizado Sem Informação"
                cor_t3 = "#25a244" if t3_confirmado > 0 else "#475569"
                carga_real_t3 = t3_confirmado
                perf_t3_html = analisar_SLA_e_mix_hoje(carga_real_t3, estimativa_t3, 'TURNOIII') if t3_confirmado > 0 else ""

        # Renderização dos Cards Visuais Atualizados com Alinhamento Estrito
        ct1, ct2, ct3 = st.columns(3)
        with ct1:
            st.markdown(f'<div style="background-color: #f8f9fa; border-radius: 8px; padding: 15px; border-left: 5px solid {cor_t1}; height: 160px;"><span style="font-size: 14px; font-weight: bold; color: #475569;">TURNO 1 (05h00 - 13h30)</span><h4 style="margin: 5px 0; color: {cor_t1};">{status_t1_txt}</h4><p style="margin: 0; font-size: 14px;"><b>Impacto Demanda:</b> {carga_real_t1} PLT (Plan: {ciclos_t1 * rend_t1} / Real: {t1_confirmado}){perf_t1_html}</p></div>', unsafe_allow_html=True)
        with ct2:
            st.markdown(f'<div style="background-color: #f8f9fa; border-radius: 8px; padding: 15px; border-left: 5px solid {cor_t2}; height: 160px;"><span style="font-size: 14px; font-weight: bold; color: #475569;">TURNO 2 (13h30 - 22h00)</span><h4 style="margin: 5px 0; color: {cor_t2};">{status_t2_txt}</h4><p style="margin: 0; font-size: 14px;"><b>Impacto Demanda:</b> {carga_real_t2} PLT (Plan: {ciclos_t2 * rend_t2} / Real: {t2_confirmado}){perf_t2_html}</p></div>', unsafe_allow_html=True)
        with ct3:
            st.markdown(f'<div style="background-color: #f8f9fa; border-radius: 8px; padding: 15px; border-left: 5px solid {cor_t3}; height: 160px;"><span style="font-size: 14px; font-weight: bold; color: #475569;">TURNO 3 (22h00 - 05h00)</span><h4 style="margin: 5px 0; color: {cor_t3};">{status_t3_txt}</h4><p style="margin: 0; font-size: 14px;"><b>Impacto Demanda:</b> {carga_real_t3} PLT (Plan: {ciclos_t3 * rend_t3} / Real: {t3_confirmado}){perf_t3_html}</p></div>', unsafe_allow_html=True)

        st.markdown("---")
        
        # ─── CALCULO DO DIAGNÓSTICO DO HT DINÂMICO ───
        st.markdown("#### 🔍 Consultar Horizonte de Carga e Estufagem Necessária")
        data_minima = df['Data_Carregamento'].min().date()
        data_maxima = df['Data_Carregamento'].max().date()
        
        data_selecionada = st.date_input("Selecione uma data no calendário para calcular a pressão logística nas estufas:", value=hoje.date(), min_value=data_minima, max_value=data_maxima, key="cal_ht")
        df_dia = df_validos[df_validos['Data_Carregamento'].dt.date == data_selecionada]
        
        total_plts_dia_selecionado = int(df_dia['Total_Plt_Percurso'].sum()) if not df_dia.empty else 0
        rendimento_medio_estufa = (rend_t1 + rend_t2 + rend_t3) / 3
        ciclos_necessarios = -(-total_plts_dia_selecionado // rendimento_medio_estufa) if total_plts_dia_selecionado > 0 else 0
        teto_maximo_dia = (ciclos_t1 + ciclos_t2 + ciclos_t3)
        saldo_ciclos_patio = teto_maximo_dia - ciclos_necessarios
        
        if saldo_ciclos_patio < 0:
            cor_alerta_pco, borda_alerta_pco, texto_alerta_pco = "rgba(239, 68, 68, 0.1)", "#ef4444", f"🚨 **Gargalo Detectado:** Exige {int(ciclos_necessarios)} ciclos, mas o PCO liberou {int(teto_maximo_dia)}. Estouro de {int(abs(saldo_ciclos_patio))} fornadas!"
        elif total_plts_dia_selecionado == 0:
            cor_alerta_pco, borda_alerta_pco, texto_alerta_pco = "rgba(37, 162, 68, 0.1)", "#25a244", "✨ **Janela Totalmente Livre:** Zero paletes programados."
        else:
            cor_alerta_pco, borda_alerta_pco, texto_alerta_pco = "rgba(245, 158, 11, 0.1)", "#f59e0b", f"🔋 **Operação Equilibrada:** Exige {int(ciclos_necessarios)} estufas. Suporta mais {int(saldo_ciclos_patio)} ciclos."

        st.markdown(f'<div style="background-color: {cor_alerta_pco}; border-left: 6px solid {borda_alerta_pco}; padding: 18px; border-radius: 6px; margin-bottom: 20px;"><h4 style="margin: 0 0 5px 0; color: #1e293b;">Diagnóstico de Capacidade do HT</h4><p style="margin: 0; font-size: 15px; color: #334155;">{texto_alerta_pco}</p></div>', unsafe_allow_html=True)

        df_rodo_dia = df_dia[df_dia['Modal'].str.contains('Rodoviário', case=False, na=False)]
        df_mari_dia = df_dia[df_dia['Modal'].str.contains('Marítimo', case=False, na=False)]
        col_esquerda, col_direita = st.columns(2)
        with col_esquerda:
            st.markdown(f'<div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 5px solid #007bff; margin-bottom: 15px;"><span style="font-size: 13px; color: #6c757d; font-weight: bold;">🚚 Ocupação Rodoviária</span><h3 style="margin: 5px 0 0 0; color: #212529; font-size: 22px;">{int(df_rodo_dia["Total_Plt_Percurso"].sum())} Plts</h3></div>', unsafe_allow_html=True)
            with st.expander("📄 Listagem Rodoviário", expanded=False):
                st.dataframe(df_rodo_dia[colunas_exibicao], use_container_width=True, hide_index=True) if not df_rodo_dia.empty else st.info("Sem cargas.")
        with col_direita:
            st.markdown(f'<div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 5px solid #28a745; margin-bottom: 15px;"><span style="font-size: 13px; color: #6c757d; font-weight: bold;">🚢 Ocupação Marítima</span><h3 style="margin: 5px 0 0 0; color: #212529; font-size: 22px;">{int(df_mari_dia["Total_Plt_Percurso"].sum())} Plts</h3></div>', unsafe_allow_html=True)
            with st.expander("📄 Listagem Marítimo", expanded=False):
                st.dataframe(df_mari_dia[colunas_exibicao], use_container_width=True, hide_index=True) if not df_mari_dia.empty else st.info("Sem cargas.")

    # ─────────────────────────────────────────────────────────────────
    # ABA 2: CARTEIRA GERAL DE SOBRAS (Não Sequenciadas)
    # ─────────────────────────────────────────────────────────────────
    with tab_sobras:
        st.markdown("### 🔎 Central Analítica da Carteira de Sobras Geral")
        st.write("Filtro de calendário ignorado. Exibindo todos os volumes ativos sem registro de sequenciamento no sistema.")
        st.markdown("---")
        
        df_sobras_geral = df_validos[
            (~df_validos['Status'].astype(str).str.contains('Sequenciado', case=False, na=False)) &
            (~df_validos['Status'].astype(str).str.contains('Bipado', case=False, na=False)) &
            (~df_validos['Status'].astype(str).str.contains('Concluido|Finalizado', case=False, na=False))
        ].copy()

        if not df_sobras_geral.empty:
            df_sobras_geral['Data_Ajustada_Sobras'] = df_sobras_geral['Data_Carregamento'].dt.date
            
            agrupado_sobras = df_sobras_geral.groupby('Data_Ajustada_Sobras').agg(
                total_pallets=('Total_Plt_Percurso', 'sum'),
                total_cargas=('Fatura', 'count')
            ).reset_index().sort_values('Data_Ajustada_Sobras')

            total_acessos_sobras = int(df_sobras_geral['Total_Plt_Percurso'].sum())
            st.metric("📊 Volume Total da Carteira Disponível", f"{total_acessos_sobras} Acessos / Plts", f"{len(df_sobras_geral)} faturas em aberto", delta_color="inverse")
            st.markdown("<br>", unsafe_allow_html=True)
            
            st.markdown("##### 📅 Distribuição Cronológica de Oportunidades (Cards por Data)")
            
            colunas_cards = st.columns(min(len(agrupado_sobras), 4))
            for idx, row in agrupado_sobras.reset_index().iterrows():
                col_idx = idx % 4
                if idx > 0 and col_idx == 0:
                    colunas_cards = st.columns(min(len(agrupado_sobras) - idx, 4))
                
                data_alvo_card = row['Data_Ajustada_Sobras']
                data_formatada_card = data_alvo_card.strftime('%d/%m/%Y')
                
                df_recorte_card = df_sobras_geral[df_sobras_geral['Data_Ajustada_Sobras'] == data_alvo_card]
                mod_mari_card = len(df_recorte_card[df_recorte_card['Modal'].str.contains('Marítimo', case=False, na=False)])
                mod_rodo_card = len(df_recorte_card[df_recorte_card['Modal'].str.contains('Rodoviário', case=False, na=False)])

                with colunas_cards[col_idx]:
                    st.markdown(estilo_card_topo.format(
                        cor="#f59e0b", 
                        titulo=f"Dia {data_formatada_card}", 
                        valor=f"{int(row['total_pallets'])} PLT", 
                        subtitulo=f"🚢 Marítimo: {mod_mari_card} | 🚚 Rodo: {mod_rodo_card}"
                    ), unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("##### 📋 Linha do Tempo e Detalhamento Técnico (Planilha de Controle)")
            
            df_sobras_tabela = df_sobras_geral.copy()
            df_sobras_tabela['Data_Programacao'] = df_sobras_tabela['Data_Carregamento'].dt.strftime('%d/%m/%Y')
            df_sobras_tabela['Data_Percurso'] = df_sobras_tabela['Data_Programacao']
            df_sobras_tabela['Data_Sequenciamento'] = "-"
            
            colunas_sobras_final = ['Percurso', 'Fatura', 'Total_Plt_Percurso', 'Data_Programacao', 'Data_Percurso', 'Data_Sequenciamento', 'Modal']
            df_sobras_render = df_sobras_tabela[colunas_sobras_final].rename(columns={
                'Total_Plt_Percurso': 'Acessos / Paletes'
            })
            
            st.dataframe(df_sobras_render, use_container_width=True, hide_index=True)
        else:
            st.success("✨ **Carteira Totalmente Sequenciada!** Não existem sobras pendentes na base de dados.")

    # ─────────────────────────────────────────────────────────────────
    # ABA 3: CONSULTA POR FATURA / PERCURSO
    # ─────────────────────────────────────────────────────────────────
    with tab_consulta:
        st.subheader("Filtros de Pesquisa")
        
        modal_disponiveis = ["Todos"] + list(df['Modal'].unique())
        modal_selecionado = st.selectbox("Selecione o Modal:", modal_disponiveis, key="modal_consulta")
        
        col1, col2 = st.columns(2)
        with col1:
            busca_fatura = st.text_input("Digite o número da Fatura (or parte dele):", key="fatura_cons").strip()
        with col2:
            busca_percurso = st.text_input("Digite o Percurso (or parte dele):", key="perc_cons").strip()
            
        df_filtrado = df.copy()
        
        if modal_selecionado != "Todos":
            df_filtrado = df_filtrado[df_filtrado['Modal'] == modal_selecionado]
            
        if busca_fatura:
            df_filtrado = df_filtrado[df_filtrado['Fatura'].str.contains(busca_fatura, case=False, na=False)]
            
        if busca_percurso:
            df_filtrado = df_filtrado[df_filtrado['Percurso'].str.contains(busca_percurso, case=False, na=False)]
        
        if not busca_fatura and not busca_percurso:
            df_filtrado = df_filtrado[df_filtrado['Total_Plt_Percurso'] > 0]
            st.caption("💡 Exibindo apenas cargas com paletes maiores que zero. Use os campos de busca acima para rastrear cargas zeradas.")
            
        st.write(f"**Registros encontrados:** {len(df_filtrado)}")
        
        df_visualizacao = df_filtrado[colunas_exibicao].copy()
        df_visualizacao['Data_Carregamento'] = df_visualizacao['Data_Carregamento'].dt.strftime('%d/%m/%Y')
        
        st.dataframe(df_visualizacao, use_container_width=True, hide_index=True)