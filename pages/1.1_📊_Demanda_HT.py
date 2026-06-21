import streamlit as st
import os
import pandas as pd
from datetime import datetime, time
import zoneinfo
from src.core.data_loader import carregar_e_tratar_dados, carregar_realizado_ht, carregar_matriz_capacidade

# 1. Configuração da página (Layout Wide para melhor aproveitamento de tabelas)
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

if df is not None:
    st.sidebar.info(f"**Última Atualização da Base:**\n{ultima_atualizacao}")
else:
    st.sidebar.error("⚠️ Não foi possível carregar a base de dados do Google Sheets.")

# 4. Título Principal do Aplicativo
st.title("📊 Acompanhamento de Cargas de Exportação")

if df is not None:
    # Garante que a coluna de paletes é numérica para as validações de maior que zero
    df['Total_Plt_Percurso'] = pd.to_numeric(df['Total_Plt_Percurso'], errors='coerce').fillna(0).astype(int)
    
    # ─────────────────────────────────────────────────────────────────
    # CRIAÇÃO DAS ABAS
    # ─────────────────────────────────────────────────────────────────
    tab_indicadores, tab_consulta = st.tabs(["📈 Indicadores Gerais", "🔍 Consulta por Fatura/Percurso"])
    
    # Lista de colunas oficiais para exibição
    colunas_exibicao = ['Status', 'Fatura', 'Percurso', 'Total_Plt_Percurso', 'Data_Carregamento', 'Modal']
    
    # ─────────────────────────────────────────────────────────────────
    # ABA 1: INDICADORES GERAIS (A Demanda governa o Cálculo de Capacidade)
    # ─────────────────────────────────────────────────────────────────
    with tab_indicadores:
        st.markdown("### 📈 Painel de Capacidade e Volumetria")
        st.write("Acompanhamento fixo dos principais períodos e consulta personalizada por data.")
        st.markdown("---")
        
        # Definição automática das datas de Hoje e Amanhã
        hoje = pd.Timestamp(hoje_br)
        amanha = hoje + pd.Timedelta(days=1)
        
        # Filtra a base base de cálculos removendo sempre o que for zero
        df_validos = df[df['Total_Plt_Percurso'] > 0]
        
        # Cálculo 1: Volume focado em Hoje
        df_hoje = df_validos[df_validos['Data_Carregamento'].dt.date == hoje_br]
        total_plts_hoje = int(df_hoje['Total_Plt_Percurso'].sum())
        
        # Cálculo 2: Volume focado em Amanhã
        df_amanha = df_validos[df_validos['Data_Carregamento'].dt.date == amanha.date()]
        total_plts_amanha = int(df_amanha['Total_Plt_Percurso'].sum())

        # Cálculo 3: Total Geral
        total_plts_geral = int(df_validos['Total_Plt_Percurso'].sum())
        cargas_geral = len(df_validos)
        
        # Estilização CSS dos 3 grandes cards do topo
        estilo_card_topo = """
        <div style="
            background-color: #f1f3f5; 
            padding: 15px; 
            border-radius: 8px; 
            border-top: 4px solid {cor}; 
            box-shadow: 1px 1px 3px rgba(0,0,0,0.05);
            text-align: center;">
            <span style="font-size: 13px; color: #495057; font-weight: bold; text-transform: uppercase;">{titulo}</span>
            <h2 style="margin: 5px 0 0 0; color: #212529; font-size: 26px;">{valor}</h2>
            <span style="font-size: 11px; color: #6c757d;">{subtitulo}</span>
        </div>
        """
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(estilo_card_topo.format(cor="#dc3545", titulo="🚨 Programado para Hoje", valor=f"{total_plts_hoje} Plts", subtitulo=f"{len(df_hoje)} cargas para {hoje.strftime('%d/%m')}"), unsafe_allow_html=True)
        with c2:
            st.markdown(estilo_card_topo.format(cor="#ffc107", titulo="📅 Programado para Amanhã", valor=f"{total_plts_amanha} Plts", subtitulo=f"{len(df_amanha)} cargas para {amanha.strftime('%d/%m')}"), unsafe_allow_html=True)
        with c3:
            st.markdown(estilo_card_topo.format(cor="#6c757d", titulo="📊 Total Geral em Aberto", valor=f"{total_plts_geral} Plts", subtitulo=f"{cargas_geral} cargas programadas no total"), unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # ─── ⚖️ VALIDAÇÃO DE TURNOS E TRAVA DE LIMBO ───
        st.markdown("### ⏱️ Governança de Pátio e Validação de Turnos (Hoje)")
        
        # Captura os parâmetros vivos da planilha mestre (Com tratamento de string/float para chaves)
        ciclos_t1 = tracking_pco.get(('HT', '1', 'CICLOS', 'POR_TURNO'), tracking_pco.get(('HT', '1.0', 'CICLOS', 'POR_TURNO'), 4))
        rend_t1 = tracking_pco.get(('HT', '1', 'RENDIMENTO', 'PLTS_POR_CICLO'), tracking_pco.get(('HT', '1.0', 'RENDIMENTO', 'PLTS_POR_CICLO'), 27))
        estimativa_t1 = ciclos_t1 * rend_t1 

        ciclos_t2 = tracking_pco.get(('HT', '2', 'CICLOS', 'POR_TURNO'), tracking_pco.get(('HT', '2.0', 'CICLOS', 'POR_TURNO'), 4))
        rend_t2 = tracking_pco.get(('HT', '2', 'RENDIMENTO', 'PLTS_POR_CICLO'), tracking_pco.get(('HT', '2.0', 'RENDIMENTO', 'PLTS_POR_CICLO'), 25))
        estimativa_t2 = ciclos_t2 * rend_t2 

        # 🔌 INCLUSÃO CIRÚRGICA DO TURNO 3
        ciclos_t3 = tracking_pco.get(('HT', '3', 'CICLOS', 'POR_TURNO'), tracking_pco.get(('HT', '3.0', 'CICLOS', 'POR_TURNO'), 4))
        rend_t3 = tracking_pco.get(('HT', '3', 'RENDIMENTO', 'PLTS_POR_CICLO'), tracking_pco.get(('HT', '3.0', 'RENDIMENTO', 'PLTS_POR_CICLO'), 25))
        estimativa_t3 = ciclos_t3 * rend_t3
        
        df_real_hoje = df_realizado_ht[df_realizado_ht['DATA_PROD'].dt.date == hoje_br] if df_realizado_ht is not None else pd.DataFrame()
        t1_confirmado = df_real_hoje[df_real_hoje['TURNO'].astype(str).str.contains('I$|1', na=False)]['PALLETS'].sum() if not df_real_hoje.empty else 0
        t2_confirmado = df_real_hoje[df_real_hoje['TURNO'].astype(str).str.contains('II$|2', na=False)]['PALLETS'].sum() if not df_real_hoje.empty else 0
        t3_confirmado = df_real_hoje[df_real_hoje['TURNO'].astype(str).str.contains('III$|3', na=False)]['PALLETS'].sum() if not df_real_hoje.empty else 0
        
        # Identifica o dia da semana atual (0=Segunda, 5=Sábado, 6=Domingo)
        dia_semana_hoje = hoje_br.weekday()

        # 🛑 REGRAS DE STATUS DOS TURNOS TRATANDO O DOMINGO E O PLANTÃO OFICIAL
        if dia_semana_hoje == 6:
            # Se for Domingo: Turno 1 e Turno 2 estão fechados de verdade
            status_t1_txt = "🛑 Fábrica Fechada (Plantão inicia às 22h)"
            cor_t1 = "#64748b" # Cinza tático de inatividade
            carga_real_t1 = 0
            
            status_t2_txt = "🛑 Fábrica Fechada (Plantão inicia às 22h)"
            cor_t2 = "#64748b"
            carga_real_t2 = 0
        else:
            # Dias de Semana Normais para Turno 1 e Turno 2
            if hora_atual < time(13, 30):
                status_t1_txt = "⚙️ Em Andamento / Previsto"
                cor_t1 = "#007ebd"
                carga_real_t1 = os.environ.get('ESTIMATIVA_T1', estimativa_t1)
            elif hora_atual >= time(13, 30) and t1_confirmado == 0:
                status_t1_txt = "⏳ Turno Passou - Retido Aguardando Atualização Técnica"
                cor_t1 = "#d97706"
                carga_real_t1 = estimativa_t1 
            else:
                status_t1_txt = "✅ Concluído e Consolidado no Sheets"
                cor_t1 = "#25a244"
                carga_real_t1 = t1_confirmado 

            if hora_atual < time(22, 0):
                status_t2_txt = "⚙️ Em Andamento / Previsto"
                cor_t2 = "#007ebd"
                carga_real_t2 = estimativa_t2
            elif hora_atual >= time(22, 0) and t2_confirmado == 0:
                status_t2_txt = "⏳ Turno Passou - Retido Aguardando Atualização Técnica"
                cor_t2 = "#d97706"
                carga_real_t2 = estimativa_t2
            else:
                status_t2_txt = "✅ Concluído e Consolidado no Sheets"
                cor_t2 = "#25a244"
                carga_real_t2 = t2_confirmado

        # ─── REGRA DO TURNO 3 (Roda de Domingo a Sexta à noite - Jornada de Segunda) ───
        if dia_semana_hoje == 5 and hora_atual >= time(22, 0):
            # Sábado após as 22h: Plantão encerrado
            status_t3_txt = "🛑 Fim de Plantão (Retorno Domingo 22h)"
            cor_t3 = "#64748b"
            carga_real_t3 = 0
        elif dia_semana_hoje == 6 and hora_atual < time(22, 0):
            # Domingo antes das 22h: Fábrica paralisada aguardando o início
            status_t3_txt = "⏳ Aguardando Início do Plantão Noturno"
            cor_t3 = "#64748b"
            carga_real_t3 = 0
        else:
            # Turno 3 em Execução Real (Entre 22:00 e 05:00)
            if hora_atual >= time(22, 0) or hora_atual < time(5, 0):
                if dia_semana_hoje == 6:
                    status_t3_txt = "⚙️ Noturno Em Andamento ➔ (Jornada de Segunda)"
                else:
                    status_t3_txt = "⚙️ Noturno Em Andamento"
                cor_t3 = "#007ebd"
                carga_real_t3 = estimativa_t3
            elif hora_atual >= time(5, 0) and t3_confirmado == 0:
                status_t3_txt = "⏳ Turno Passou - Retido Aguardando Atualização Técnica"
                cor_t3 = "#d97706"
                carga_real_t3 = estimativa_t3
            else:
                status_t3_txt = "✅ Concluído e Consolidado no Sheets"
                cor_t3 = "#25a244"
                carga_real_t3 = t3_confirmado

        # Transforma os blocos visuais de 2 colunas para 3 colunas para acolher o Turno 3
        ct1, ct2, ct3 = st.columns(3)
        with ct1:
            st.markdown(f"""
            <div style="background-color: #f8f9fa; border-radius: 8px; padding: 15px; border-left: 5px solid {cor_t1}; height: 140px;">
                <span style="font-size: 14px; font-weight: bold; color: #475569;">TURNO 1 (05h00 - 13h30)</span>
                <h4 style="margin: 5px 0; color: {cor_t1};">{status_t1_txt}</h4>
                <p style="margin: 0; font-size: 14px;"><b>Impacto Demanda:</b> {carga_real_t1} PLT (Plan: {estimativa_t1} / Real: {t1_confirmado})</p>
            </div>
            """, unsafe_allow_html=True)
            
        with ct2:
            st.markdown(f"""
            <div style="background-color: #f8f9fa; border-radius: 8px; padding: 15px; border-left: 5px solid {cor_t2}; height: 140px;">
                <span style="font-size: 14px; font-weight: bold; color: #475569;">TURNO 2 (13h30 - 22h00)</span>
                <h4 style="margin: 5px 0; color: {cor_t2};">{status_t2_txt}</h4>
                <p style="margin: 0; font-size: 14px;"><b>Impacto Demanda:</b> {carga_real_t2} PLT (Plan: {estimativa_t2} / Real: {t2_confirmado})</p>
            </div>
            """, unsafe_allow_html=True)

        with ct3:
            st.markdown(f"""
            <div style="background-color: #f8f9fa; border-radius: 8px; padding: 15px; border-left: 5px solid {cor_t3}; height: 140px;">
                <span style="font-size: 14px; font-weight: bold; color: #475569;">TURNO 3 (22h00 - 05h00)</span>
                <h4 style="margin: 5px 0; color: {cor_t3};">{status_t3_txt}</h4>
                <p style="margin: 0; font-size: 14px;"><b>Impacto Demanda:</b> {carga_real_t3} PLT (Plan: {estimativa_t3} / Real: {t3_confirmado})</p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        
        # ─── 🔍 SEÇÃO: CONSULTA POR CALENDÁRIO DIZENDO A CAPACIDADE ───
        st.markdown("#### 🔍 Consultar Horizonte de Carga e Estufagem Necessária")
        
        data_minima = df['Data_Carregamento'].min().date()
        data_maxima = df['Data_Carregamento'].max().date()
        
        data_selecionada = st.date_input(
            "Selecione uma data no calendário para calcular a pressão logística nas estufas:",
            value=hoje.date() if data_minima <= hoje.date() <= data_maxima else data_minima,
            min_value=data_minima,
            max_value=data_maxima
        )
        
        df_dia = df_validos[df_validos['Data_Carregamento'].dt.date == data_selecionada]
        st.markdown(f"##### Resumo Analítico de Estufagem para o dia: **{data_selecionada.strftime('%d/%m/%Y')}**")
        
        # Volume Total do Dia Selecionado (Ex: Dia 22)
        total_plts_dia_selecionado = int(df_dia['Total_Plt_Percurso'].sum()) if not df_dia.empty else 0
        
        # 🧮 O MOTOR REVERSO ATUALIZADO: SOMA OS 3 TURNOS NO CALENDÁRIO
        rendimento_medio_estufa = (rend_t1 + rend_t2 + rend_t3) / 3
        
        if total_plts_dia_selecionado > 0:
            ciclos_necessarios = -(-total_plts_dia_selecionado // rendimento_medio_estufa)
        else:
            ciclos_necessarios = 0
            
        teto_maximo_dia = (ciclos_t1 + ciclos_t2 + ciclos_t3) # Agora soma os 3 turnos vivos da planilha!
        saldo_ciclos_patio = teto_maximo_dia - ciclos_necessarios
        
        if saldo_ciclos_patio < 0:
            cor_alerta_pco = "rgba(239, 68, 68, 0.1)"
            borda_alerta_pco = "#ef4444"
            texto_alerta_pco = f"🚨 **Gargalo Detectado:** A demanda programada exige {int(ciclos_necessarios)} ciclos de aquecimento, mas os 3 turnos do plantão disponibilizam apenas {int(teto_maximo_dia)} ciclos hoje. Estouro de {int(abs(saldo_ciclos_patio))} fornadas!"
        elif total_plts_dia_selecionado == 0:
            cor_alerta_pco = "rgba(37, 162, 68, 0.1)"
            borda_alerta_pco = "#25a244"
            texto_alerta_pco = "✨ **Janela Totalmente Livre:** Zero paletes programados. Ótimo momento para antecipações operacionais."
        else:
            cor_alerta_pco = "rgba(245, 158, 11, 0.1)"
            borda_alerta_pco = "#f59e0b"
            texto_alerta_pco = f"🔋 **Operação Equilibrada:** A demanda exige {int(ciclos_necessarios)} estufas. O plantão de 3 turnos ainda suporta a entrada de mais {int(saldo_ciclos_patio)} ciclos de tratamento."

        st.markdown(f"""
        <div style="background-color: {cor_alerta_pco}; border-left: 6px solid {borda_alerta_pco}; padding: 18px; border-radius: 6px; margin-bottom: 20px;">
            <h4 style="margin: 0 0 5px 0; color: #1e293b;">Diagnóstico de Capacidade do HT</h4>
            <p style="margin: 0; font-size: 15px; color: #334155;">{texto_alerta_pco}</p>
        </div>
        """, unsafe_allow_html=True)

        # Divisão por modais técnicos
        df_rodo_dia = df_dia[df_dia['Modal'].str.contains('Rodoviário', case=False, na=False)]
        df_mari_dia = df_dia[df_dia['Modal'].str.contains('Marítimo', case=False, na=False)]
        
        total_plt_rodo = int(df_rodo_dia['Total_Plt_Percurso'].sum())
        total_plt_mari = int(df_mari_dia['Total_Plt_Percurso'].sum())
        
        df_rodo_view = df_rodo_dia.copy()
        df_mari_view = df_mari_dia.copy()
        if not df_rodo_view.empty:
            df_rodo_view['Data_Carregamento'] = df_rodo_view['Data_Carregamento'].dt.strftime('%d/%m/%Y')
        if not df_mari_view.empty:
            df_mari_view['Data_Carregamento'] = df_mari_view['Data_Carregamento'].dt.strftime('%d/%m/%Y')
            
        colunas_indicadores = ['Fatura', 'Percurso', 'Status', 'Total_Plt_Percurso', 'Data_Carregamento']
        
        col_esquerda, col_direita = st.columns(2)
        
        estilo_card_modal = """
        <div style="
            background-color: #f8f9fa; 
            padding: 15px; 
            border-radius: 8px; 
            border-left: 5px solid {cor}; 
            box-shadow: 2px 2px 4px rgba(0,0,0,0.02);
            margin-bottom: 15px;">
            <span style="font-size: 13px; color: #6c757d; font-weight: bold;">{titulo}</span>
            <h3 style="margin: 5px 0 0 0; color: #212529; font-size: 22px;">{valor}</h3>
        </div>
        """
        
        with col_esquerda:
            st.markdown(estilo_card_modal.format(cor="#007bff", titulo="🚚 Ocupação Rodoviária (Data Selecionada)", valor=f"{total_plt_rodo} Plts ({len(df_rodo_dia)} cargas)"), unsafe_allow_html=True)
            with st.expander("📄 Abrir Listagem Rodoviário", expanded=False):
                if not df_rodo_dia.empty:
                    st.dataframe(df_rodo_view[colunas_indicadores], use_container_width=True, hide_index=True)
                else:
                    st.info("Nenhuma carga rodoviária ativa para esta data.")
                
        with col_direita:
            st.markdown(estilo_card_modal.format(cor="#28a745", titulo="🚢 Ocupação Marítima (Data Selecionada)", valor=f"{total_plt_mari} Plts ({len(df_mari_dia)} cargas)"), unsafe_allow_html=True)
            with st.expander("📄 Abrir Listagem Marítimo", expanded=False):
                if not df_mari_dia.empty:
                    st.dataframe(df_mari_view[colunas_indicadores], use_container_width=True, hide_index=True)
                else:
                    st.info("Nenhuma carga marítima ativa para esta data.")

    # ─────────────────────────────────────────────────────────────────
    # ABA 2: CONSULTA POR FATURA / PERCURSO
    # ─────────────────────────────────────────────────────────────────
    with tab_consulta:
        st.subheader("Filtros de Pesquisa")
        
        modal_disponiveis = ["Todos"] + list(df['Modal'].unique())
        modal_selecionado = st.selectbox("Selecione o Modal:", modal_disponiveis, key="modal_consulta")
        
        col1, col2 = st.columns(2)
        with col1:
            busca_fatura = st.text_input("Digite o número da Fatura (ou parte dele):", key="fatura_cons").strip()
        with col2:
            busca_percurso = st.text_input("Digite o Percurso (ou parte dele):", key="perc_cons").strip()
            
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