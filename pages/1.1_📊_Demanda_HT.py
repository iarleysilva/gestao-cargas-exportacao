import streamlit as st
import os
import pandas as pd
from datetime import datetime, time
import zoneinfo  # <--- CORRIGIDO: Injeção explícita da biblioteca de fuso horário

# ─── BLOCO DE SEGURANÇA DE CAMINHOS ROBUSTO (AJUSTADO PARA ARQUIVO SOLTO EM PAGES) ───
import sys
from pathlib import Path
raiz = Path(__file__).resolve().parents[1]  # Sobe 1 nível (pages/ -> raiz do projeto)
if str(raiz) not in sys.path:
    sys.path.append(str(raiz))
# ───────────────────────────────────────────────────────────────────────────────────

from src.core.data_loader import carregar_e_tratar_dados, carregar_realizado_ht, carregar_matriz_capacidade

# 1. Configuração Única da Página (CORRIGIDO: Removida a duplicidade que travava o sistema)
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
    # CRIAÇÃO DAS ABAS (Estrutura com as 3 abas solicitadas)
    # ─────────────────────────────────────────────────────────────────
    tab_indicadores, tab_sobras, tab_consulta = st.tabs([
        "📈 Indicadores Gerais", 
        "⚠️ Carteira Geral de Sobras (Não Sequenciadas)", 
        "🔍 Consulta por Fatura/Percurso"
    ])
    
    # Lista de colunas oficiais para exibição da aba corrente e consulta
    colunas_exibicao = ['Status', 'Fatura', 'Percurso', 'Total_Plt_Percurso', 'Data_Carregamento', 'Modal']
    
    # Filtra a base base de cálculos removendo sempre o que for zero
    df_validos = df[df['Total_Plt_Percurso'] > 0].copy()
    
    # Estilização CSS dos grandes cards do topo
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
    # ABA 1: INDICADORES GERAIS (A Demanda governa o Cálculo de Capacidade)
    # ─────────────────────────────────────────────────────────────────
    with tab_indicadores:
        st.markdown("### 📈 Painel de Capacidade e Volumetria")
        st.write("Acompanhamento fixo dos principais períodos e consulta personalizada por data.")
        st.markdown("---")
        
        # Definição automática das datas de Hoje e Amanhã
        hoje = pd.Timestamp(hoje_br)
        amanha = hoje + pd.Timedelta(days=1)
        
        # Cálculo 1: Volume focado em Hoje
        df_hoje = df_validos[df_validos['Data_Carregamento'].dt.date == hoje_br]
        total_plts_hoje = int(df_hoje['Total_Plt_Percurso'].sum())
        
        # Cálculo 2: Volume focado em Amanhã
        df_amanha = df_validos[df_validos['Data_Carregamento'].dt.date == amanha.date()]
        total_plts_amanha = int(df_amanha['Total_Plt_Percurso'].sum())

        # Cálculo 3: Total Geral
        total_plts_geral = int(df_validos['Total_Plt_Percurso'].sum())
        cargas_geral = len(df_validos)
        
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
        
        ciclos_t1 = tracking_pco.get(('HT', '1', 'CICLOS', 'POR_TURNO'), tracking_pco.get(('HT', '1.0', 'CICLOS', 'POR_TURNO'), 4))
        rend_t1 = tracking_pco.get(('HT', '1', 'RENDIMENTO', 'PLTS_POR_CICLO'), tracking_pco.get(('HT', '1.0', 'RENDIMENTO', 'PLTS_POR_CICLO'), 27))
        estimativa_t1 = ciclos_t1 * rend_t1 

        ciclos_t2 = tracking_pco.get(('HT', '2', 'CICLOS', 'POR_TURNO'), tracking_pco.get(('HT', '2.0', 'CICLOS', 'POR_TURNO'), 4))
        rend_t2 = tracking_pco.get(('HT', '2', 'RENDIMENTO', 'PLTS_POR_CICLO'), tracking_pco.get(('HT', '2.0', 'RENDIMENTO', 'PLTS_POR_CICLO'), 25))
        estimativa_t2 = ciclos_t2 * rend_t2 

        ciclos_t3 = tracking_pco.get(('HT', '3', 'CICLOS', 'POR_TURNO'), tracking_pco.get(('HT', '3.0', 'CICLOS', 'POR_TURNO'), 4))
        rend_t3 = tracking_pco.get(('HT', '3', 'RENDIMENTO', 'PLTS_POR_CICLO'), tracking_pco.get(('HT', '3.0', 'RENDIMENTO', 'PLTS_POR_CICLO'), 25))
        estimativa_t3 = ciclos_t3 * rend_t3
        
        df_real_hoje = df_realizado_ht[df_realizado_ht['DATA_PROD'].dt.date == hoje_br] if df_realizado_ht is not None else pd.DataFrame()
        t1_confirmado = df_real_hoje[df_real_hoje['TURNO'].astype(str).str.contains('I$|1', na=False)]['PALLETS'].sum() if not df_real_hoje.empty else 0
        t2_confirmado = df_real_hoje[df_real_hoje['TURNO'].astype(str).str.contains('II$|2', na=False)]['PALLETS'].sum() if not df_real_hoje.empty else 0
        t3_confirmado = df_real_hoje[df_real_hoje['TURNO'].astype(str).str.contains('III$|3', na=False)]['PALLETS'].sum() if not df_real_hoje.empty else 0
        
        dia_semana_hoje = hoje_br.weekday()

        if dia_semana_hoje == 6:
            status_t1_txt = "🛑 Fábrica Fechada (Plantão inicia às 22h)"
            cor_t1 = "#64748b"
            carga_real_t1 = 0
            status_t2_txt = "🛑 Fábrica Fechada (Plantão inicia às 22h)"
            cor_t2 = "#64748b"
            carga_real_t2 = 0
        else:
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

        if dia_semana_hoje == 5 and hora_atual >= time(22, 0):
            status_t3_txt = "🛑 Fim de Plantão (Retorno Domingo 22h)"
            cor_t3 = "#64748b"
            carga_real_t3 = 0
        elif dia_semana_hoje == 6 and hora_atual < time(22, 0):
            status_t3_txt = "⏳ Aguardando Início do Plantão Noturno"
            cor_t3 = "#64748b"
            carga_real_t3 = 0
        else:
            if hora_atual >= time(22, 0) or hora_atual < time(5, 0):
                status_t3_txt = "⚙️ Noturno Em Andamento ➔ (Jornada de Segunda)" if dia_semana_hoje == 6 else "⚙️ Noturno Em Andamento"
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

        ct1, ct2, ct3 = st.columns(3)
        with ct1:
            st.markdown(f'<div style="background-color: #f8f9fa; border-radius: 8px; padding: 15px; border-left: 5px solid {cor_t1}; height: 140px;"><span style="font-size: 14px; font-weight: bold; color: #475569;">TURNO 1 (05h00 - 13h30)</span><h4 style="margin: 5px 0; color: {cor_t1};">{status_t1_txt}</h4><p style="margin: 0; font-size: 14px;"><b>Impacto Demanda:</b> {carga_real_t1} PLT (Plan: {estimativa_t1} / Real: {t1_confirmado})</p></div>', unsafe_allow_html=True)
        with ct2:
            st.markdown(f'<div style="background-color: #f8f9fa; border-radius: 8px; padding: 15px; border-left: 5px solid {cor_t2}; height: 140px;"><span style="font-size: 14px; font-weight: bold; color: #475569;">TURNO 2 (13h30 - 22h00)</span><h4 style="margin: 5px 0; color: {cor_t2};">{status_t2_txt}</h4><p style="margin: 0; font-size: 14px;"><b>Impacto Demanda:</b> {carga_real_t2} PLT (Plan: {estimativa_t2} / Real: {t2_confirmado})</p></div>', unsafe_allow_html=True)
        with ct3:
            st.markdown(f'<div style="background-color: #f8f9fa; border-radius: 8px; padding: 15px; border-left: 5px solid {cor_t3}; height: 140px;"><span style="font-size: 14px; font-weight: bold; color: #475569;">TURNO 3 (22h00 - 05h00)</span><h4 style="margin: 5px 0; color: {cor_t3};">{status_t3_txt}</h4><p style="margin: 0; font-size: 14px;"><b>Impacto Demanda:</b> {carga_real_t3} PLT (Plan: {estimativa_t3} / Real: {t3_confirmado})</p></div>', unsafe_allow_html=True)

        st.markdown("---")
        
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
                
                data_formatada_card = row['Data_Ajustada_Sobras'].strftime('%d/%m/%Y')
                with colunas_cards[col_idx]:
                    st.markdown(estilo_card_topo.format(
                        cor="#f59e0b", 
                        titulo=f"Dia {data_formatada_card}", 
                        valor=f"{int(row['total_pallets'])} PLT", 
                        subtitulo=f"{int(row['total_cargas'])} percursos soltos"
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