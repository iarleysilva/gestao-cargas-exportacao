import streamlit as st
import os
import pandas as pd
from src.core.data_loader import carregar_e_tratar_dados

# 1. Configuração da página (Layout Wide para melhor aproveitamento de tabelas)
st.set_page_config(
    page_title="Gestão de Cargas - Exportação",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Carrega os dados direto da API do Google Sheets (aba 'base demandas atual' e 'atualização')
df, ultima_atualizacao = carregar_e_tratar_dados()

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
    
    # Criação das Abas do Sistema
    tab_consulta, tab_indicadores = st.tabs(["🔍 Consulta por Fatura/Percurso", "📈 Indicadores Gerais"])
    
    # Lista de colunas oficiais para exibição (coluna 'Tipo' removida conforme solicitado)
    colunas_exibicao = ['Status', 'Fatura', 'Percurso', 'Total_Plt_Percurso', 'Data_Carregamento', 'Modal']
    
    # ─────────────────────────────────────────────────────────────────
    # ABA 1: CONSULTA POR FATURA / PERCURSO
    # ─────────────────────────────────────────────────────────────────
    with tab_consulta:
        st.subheader("Filtros de Pesquisa")
        
        # Seletor de Modal para a busca
        modal_disponiveis = ["Todos"] + list(df['Modal'].unique())
        modal_selecionado = st.selectbox("Selecione o Modal:", modal_disponiveis, key="modal_consulta")
        
        # Inputs de texto lado a lado
        col1, col2 = st.columns(2)
        with col1:
            busca_fatura = st.text_input("Digite o número da Fatura (ou parte dele):", key="fatura_cons").strip()
        with col2:
            busca_percurso = st.text_input("Digite o Percurso (ou parte dele):", key="perc_cons").strip()
            
        # Aplicação dinâmica dos filtros
        df_filtrado = df.copy()
        
        if modal_selecionado != "Todos":
            df_filtrado = df_filtrado[df_filtrado['Modal'] == modal_selecionado]
            
        if busca_fatura:
            df_filtrado = df_filtrado[df_filtrado['Fatura'].str.contains(busca_fatura, case=False, na=False)]
            
        if busca_percurso:
            df_filtrado = df_filtrado[df_filtrado['Percurso'].str.contains(busca_percurso, case=False, na=False)]
        
        # REGRA DO ZERO NA CONSULTA:
        # Se o usuário NÃO pesquisar nada por texto, esconde as linhas com 0 paletes.
        # Se ele digitar uma fatura ou percurso, mostra inclusive se estiver zerado.
        if not busca_fatura and not busca_percurso:
            df_filtrado = df_filtrado[df_filtrado['Total_Plt_Percurso'] > 0]
            st.caption("💡 Exibindo apenas cargas com paletes maiores que zero. Use os campos de busca acima para rastrear cargas zeradas.")
            
        st.write(f"**Registros encontrados:** {len(df_filtrado)}")
        
        # Formata a data para o padrão brasileiro (dd/mm/aaaa) antes de renderizar a tabela
        df_visualizacao = df_filtrado[colunas_exibicao].copy()
        df_visualizacao['Data_Carregamento'] = df_visualizacao['Data_Carregamento'].dt.strftime('%d/%m/%Y')
        
        # Exibe a tabela sem a coluna de índice do Pandas
        st.dataframe(df_visualizacao, use_container_width=True, hide_index=True)
        
    # ─────────────────────────────────────────────────────────────────
    # ABA 2: INDICADORES GERAIS (Visão de Capacidade)
    # ─────────────────────────────────────────────────────────────────
    with tab_indicadores:
        st.markdown("### 📈 Painel de Capacidade e Volumetria")
        st.write("Acompanhamento fixo dos principais períodos e consulta personalizada por data.")
        st.markdown("---")
        
        # Definição automática das datas de Hoje e Amanhã
        hoje = pd.Timestamp.now().normalize()
        amanha = hoje + pd.Timedelta(days=1)
        
        # Filtra a base base de cálculos removendo sempre o que for zero
        df_validos = df[df['Total_Plt_Percurso'] > 0]
        
        # Cálculo 1: Total Geral (Independente de data)
        total_plts_geral = int(df_validos['Total_Plt_Percurso'].sum())
        cargas_geral = len(df_validos)
        
        # Cálculo 2: Volume focado em Hoje
        df_hoje = df_validos[df_validos['Data_Carregamento'].dt.date == hoje.date()]
        total_plts_hoje = int(df_hoje['Total_Plt_Percurso'].sum())
        
        # Cálculo 3: Volume focado em Amanhã
        df_amanha = df_validos[df_validos['Data_Carregamento'].dt.date == amanha.date()]
        total_plts_amanha = int(df_amanha['Total_Plt_Percurso'].sum())
        
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
        
        # Renderização dos Cards lado a lado (Fixo no topo da aba)
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(estilo_card_topo.format(cor="#6c757d", titulo="📊 Total Geral em Aberto", valor=f"{total_plts_geral} Plts", subtitulo=f"{cargas_geral} cargas programadas no total"), unsafe_allow_html=True)
        with c2:
            st.markdown(estilo_card_topo.format(cor="#dc3545", titulo="🚨 Programado para Hoje", valor=f"{total_plts_hoje} Plts", subtitulo=f"{len(df_hoje)} cargas para {hoje.strftime('%d/%m')}"), unsafe_allow_html=True)
        with c3:
            st.markdown(estilo_card_topo.format(cor="#ffc107", titulo="📅 Programado para Amanhã", valor=f"{total_plts_amanha} Plts", subtitulo=f"{len(df_amanha)} cargas para {amanha.strftime('%d/%m')}"), unsafe_allow_html=True)
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("---")
        
        # Seção de seleção livre por calendário
        st.markdown("#### 🔍 Consultar Outra Data Específica")
        
        data_minima = df['Data_Carregamento'].min().date()
        data_maxima = df['Data_Carregamento'].max().date()
        
        # Criação do calendário dinâmico
        data_selecionada = st.date_input(
            "Selecione uma data no calendário para detalhar os modais abaixo:",
            value=hoje.date() if data_minima <= hoje.date() <= data_maxima else data_minima,
            min_value=data_minima,
            max_value=data_maxima
        )
        
        # Filtra as tabelas inferiores apenas para o dia selecionado (ocultando zeros)
        df_dia = df_validos[df_validos['Data_Carregamento'].dt.date == data_selecionada]
        
        st.markdown(f"##### Resumo detalhado para o dia: **{data_selecionada.strftime('%d/%m/%Y')}**")
        
        # Quebra dos dados por Modal (Rodoviário vs Marítimo) para a data escolhida
        df_rodo_dia = df_dia[df_dia['Modal'].str.contains('Rodoviário', case=False, na=False)]
        df_mari_dia = df_dia[df_dia['Modal'].str.contains('Marítimo', case=False, na=False)]
        
        total_plt_rodo = int(df_rodo_dia['Total_Plt_Percurso'].sum())
        total_plt_mari = int(df_mari_dia['Total_Plt_Percurso'].sum())
        
        # Prepara a visualização das tabelas inferiores (formatando a data)
        df_rodo_view = df_rodo_dia.copy()
        df_mari_view = df_mari_dia.copy()
        if not df_rodo_view.empty:
            df_rodo_view['Data_Carregamento'] = df_rodo_view['Data_Carregamento'].dt.strftime('%d/%m/%Y')
        if not df_mari_view.empty:
            df_mari_view['Data_Carregamento'] = df_mari_view['Data_Carregamento'].dt.strftime('%d/%m/%Y')
            
        colunas_indicadores = ['Fatura', 'Percurso', 'Status', 'Total_Plt_Percurso', 'Data_Carregamento']
        
        # Divide a parte inferior em duas colunas para os Modais
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
            with st.expander("📄 Listagem Rodoviário", expanded=True):
                if not df_rodo_dia.empty:
                    st.dataframe(df_rodo_view[colunas_indicadores], use_container_width=True, hide_index=True)
                else:
                    st.info("Nenhuma carga rodoviária ativa para esta data.")
                
        with col_direita:
            st.markdown(estilo_card_modal.format(cor="#28a745", titulo="🚢 Ocupação Marítima (Data Selecionada)", valor=f"{total_plt_mari} Plts ({len(df_mari_dia)} cargas)"), unsafe_allow_html=True)
            with st.expander("📄 Listagem Marítimo", expanded=True):
                if not df_mari_dia.empty:
                    st.dataframe(df_mari_view[colunas_indicadores], use_container_width=True, hide_index=True)
                else:
                    st.info("Nenhuma carga marítima ativa para esta data.")