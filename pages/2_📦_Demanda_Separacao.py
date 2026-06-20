import streamlit as st
import pandas as pd
from src.core.data_loader import carregar_dados_separacao, carregar_execucao_turnos

st.set_page_config(page_title="Demanda Separação", layout="wide")

st.title("📦 Módulo: Demanda & Fluxo de Separação")
st.write("Visualização da Linha de Tempo das Cargas e Validação de Match com a Fábrica.")
st.markdown("---")

df_demanda = carregar_dados_separacao()
df_execucao = carregar_execucao_turnos()

if df_demanda is not None and df_execucao is not None:
    
    # Executa o cruzamento de Match por Percurso
    df_consolidado = pd.merge(df_demanda, df_execucao, on='PERCURSO', how='left')
    df_consolidado['DEU_MATCH'] = df_consolidado['TURNO_REALIZOU'].notna().map({True: 'SIM 🟢', False: 'NÃO 🔴'})
    df_consolidado['TURNO_REALIZOU'] = df_consolidado['TURNO_REALIZOU'].fillna('Aguardando')

    # SEPARAÇÃO COM VARIÁVEIS NORMALIZADAS EM MAIÚSCULO
    df_sobras_geral = df_consolidado[df_consolidado['STATUS'] == "NÃO SEQUENCIADO"]
    df_seq_geral = df_consolidado[df_consolidado['STATUS'] == "SEQUENCIADO"]
    
    # Filtro lateral
    st.sidebar.header("🗓️ Filtro de Operação")
    datas_planejadas = sorted(df_seq_geral['DT_SEQUENCIADO'].dropna().unique())
    
    if datas_planejadas:
        data_selecionada = st.sidebar.selectbox(
            "Selecione o Dia para Analisar a Demanda dos Turnos:",
            options=datas_planejadas,
            format_func=lambda x: pd.to_datetime(x).strftime('%d/%m/%Y')
        )
        df_seq_filtrado = df_seq_geral[df_seq_geral['DT_SEQUENCIADO'] == data_selecionada]
    else:
        st.sidebar.info("Nenhuma carga sequenciada com data encontrada.")
        df_seq_filtrado = df_seq_geral

    # KPIs do Topo
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric(label="🔴 Carteira de Sobras Geral", value=f"{df_sobras_geral['VOLUME_TOTAL'].sum()} Acessos", delta=f"{len(df_sobras_geral)} percursos parados")
    with c2:
        st.metric(label="🟢 Programado para o Dia Selecionado", value=f"{df_seq_filtrado['VOLUME_TOTAL'].sum()} Acessos", delta=f"{len(df_seq_filtrado)} percursos enviados")
    with c3:
        total_match = len(df_seq_filtrado[df_seq_filtrado['DEU_MATCH'] == 'SIM 🟢'])
        st.metric(label="📊 Percursos com MATCH no Dia", value=f"{total_match} Bipados", delta="Sincronizado")

    st.markdown("---")
    
    tab_seq, tab_sobras = st.tabs(["✅ Demandas Sequenciadas (Enviadas ao Turno)", "⚠️ Carteira Geral de Sobras (Não Sequenciadas)"])
    
    with tab_seq:
        if not df_seq_filtrado.empty:
            df_seq_view = df_seq_filtrado.copy()
            df_seq_view['1º Firme'] = df_seq_view['DT_1_FIRME'].dt.strftime('%d/%m/%Y')
            df_seq_view['Data Fís. Percurso'] = df_seq_view['DT_PERCURSO'].dt.strftime('%d/%m/%Y')
            
            cols_seq = ['PERCURSO', 'VOLUME_TOTAL', '1º Firme', 'Data Fís. Percurso', 'TURNO_ALOCADO', 'DEU_MATCH', 'TURNO_REALIZOU']
            st.dataframe(
                df_seq_view[cols_seq].rename(columns={
                    'VOLUME_TOTAL': 'Acessos (CXS+PLS)',
                    'TURNO_ALOCADO': 'Turno Planejado',
                    'DEU_MATCH': 'Deu Match?',
                    'TURNO_REALIZOU': 'Onde Bipou'
                }),
                use_container_width=True, hide_index=True
            )
        else:
            st.info("Nenhum percurso sequenciado para este dia.")
            
    with tab_sobras:
        st.write("Abaixo estão todas as cargas marcadas como 'NÃO SEQUENCIADO' na planilha com a linha de tempo original:")
        if not df_sobras_geral.empty:
            df_sobras_view = df_sobras_geral.copy()
            
            # Formatação da timeline para as sobras
            df_sobras_view['1º Firme'] = df_sobras_view['DT_1_FIRME'].dt.strftime('%d/%m/%Y')
            df_sobras_view['Data Fís. Percurso'] = df_sobras_view['DT_PERCURSO'].dt.strftime('%d/%m/%Y')
            
            # Exibindo a timeline completa nas sobras junto com o Status solicitado
            cols_sobras = ['PERCURSO', 'VOLUME_TOTAL', '1º Firme', 'Data Fís. Percurso', 'STATUS']
            st.dataframe(
                df_sobras_view[cols_sobras].rename(columns={
                    'VOLUME_TOTAL': 'Acessos',
                    'STATUS': 'Status'
                }), 
                use_container_width=True, 
                hide_index=True
            )
        else:
            st.info("Parabéns! Nenhuma sobra na carteira.")
else:
    st.error("Erro na estruturação dos dados.")