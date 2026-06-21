import streamlit as st
import pandas as pd
from datetime import datetime, time
import zoneinfo
from src.core.data_loader import carregar_dados_separacao_mi, carregar_execucao_turnos

st.set_page_config(page_title="Demanda Separação MI", layout="wide")

st.title("📦 Módulo: Demanda & Fluxo de Separação — MI")
st.write("SLA Logístico Advanced: Gestão de Carteira e Sobras por Canal de Venda (Mercado Interno).")
st.markdown("---")

# ─── 1. CARREGAMENTO DOS DADOS ORIGINAIS DA ABA MI ───
retorno_demanda = carregar_dados_separacao_mi()
df_execucao = carregar_execucao_turnos()

if isinstance(retorno_demanda, tuple):
    df_demanda = retorno_demanda[0]
else:
    df_demanda = retorno_demanda

if isinstance(df_execucao, tuple):
    df_execucao = df_execucao[0]

if df_demanda is None:
    st.error("⚠️ Erro ao conectar ou extrair os dados da planilha de demandas MI.")
    st.stop()

# ─── 2. PADRONIZAÇÃO DO PERCURSO E COALESCÊNCIA DE VOLUMES BRUTOS ───
df_demanda['PERCURSO'] = df_demanda['PERCURSO'].astype(str).str.strip().str.replace('.0', '', regex=False)
df_demanda['DT_SEQUENCIADO'] = pd.to_datetime(df_demanda['DT_SEQUENCIADO'], errors='coerce')

# Conjunto de busca cega para saber onde o percurso foi localizado na fábrica
percursos_bipados_fabrica = set(df_execucao['PERCURSO'].dropna().unique()) if df_execucao is not None else set()

# ─── 3. RELÓGIO OPERACIONAL DE BRASÍLIA ───
fuso_br = zoneinfo.ZoneInfo("America/Sao_Paulo")
agora_br = datetime.now(fuso_br)
hoje_br = agora_br.date()
hora_atual = agora_br.time()

# ─── 4. MOTOR DE SLA LOGÍSTICO PARA MI ───
def calcular_SLA_permanencia_mi(row):
    percurso_id = row['PERCURSO']
    turno_planejado = str(row['TURNO_ALOCADO']).strip().replace('.0', '')
    status_seq = str(row['STATUS']).upper().strip()
    data_carga = row['DT_SEQUENCIADO'].date() if pd.notna(row['DT_SEQUENCIADO']) else hoje_br

    existe_na_fabrica = percurso_id in percursos_bipados_fabrica

    if status_seq == "NÃO SEQUENCIADO":
        if existe_na_fabrica:
            return 'OPORTUNIDADE ⚡', 'Separado via Oportunidade Canal ⚡'
        return 'AGUARDANDO ⏳', 'Carteira de Sobras em Aberto'

    if data_carga < hoje_br:
        if existe_na_fabrica:
            return 'SIM 🟢', 'Confirmado e Retido no Prazo'
        return 'NÃO ADERIDO ❌', 'Turno Encerrado sem Bipe 🛑'
        
    elif data_carga > hoje_br:
        return 'AGUARDANDO INÍCIO SEP ⏳', 'Programado para Data Futura'

    if turno_planejado in ["1", "1.0"]:
        if hora_atual < time(5, 0):
            return 'AGUARDANDO INÍCIO SEP ⏳', 'Aguardando Início do Turno 1'
        elif time(5, 0) <= hora_atual < time(13, 30):
            if existe_na_fabrica:
                return 'EM ANDAMENTO ⚙️', 'Identificado na Aba (Aguardando Fim)'
            return 'AGUARDANDO ⏳', 'Aguardando Entrada no Turno 1'
        else:
            if existe_na_fabrica:
                return 'SIM 🟢', 'Confirmado (Permaneceu na Planilha)'
            return 'NÃO ADERIDO ❌', 'T1 Encerrado sem Aderência 🛑'

    elif turno_planejado in ["2", "2.0"]:
        if hora_atual < time(13, 30):
            return 'AGUARDANDO INÍCIO SEP ⏳', 'Aguardando Início do Turno 2'
        elif time(13, 30) <= hora_atual < time(22, 0):
            if existe_na_fabrica:
                return 'EM ANDAMENTO ⚙️', 'Identificado na Aba (Aguardando Fim)'
            return 'AGUARDANDO ⏳', 'Aguardando Entrada no Turno 2'
        else:
            if existe_na_fabrica:
                return 'SIM 🟢', 'Confirmado (Permaneceu na Planilha)'
            return 'NÃO ADERIDO ❌', 'T2 Encerrado sem Aderência 🛑'

    elif turno_planejado in ["3", "3.0"]:
        if hora_atual < time(22, 0) and hora_atual >= time(5, 0):
            return 'AGUARDANDO INÍCIO SEP ⏳', 'Aguardando Início do Turno 3'
        else:
            if existe_na_fabrica:
                return 'EM ANDAMENTO ⚙️', 'Identificado na Aba (Aguardando Fim)'
            return 'AGUARDANDO ⏳', 'Aguardando Entrada no Turno 3'

    return 'AGUARDANDO ⏳', 'Sem Definição de Turno'

res_SLA = df_demanda.apply(calcular_SLA_permanencia_mi, axis=1)
df_demanda['DEU_MATCH'] = [x[0] for x in res_SLA]
df_demanda['TURNO_REALIZOU_VIEW'] = [x[1] for x in res_SLA]

df_sobras_geral = df_demanda[df_demanda['STATUS'] == "NÃO SEQUENCIADO"]
df_seq_geral = df_demanda[df_demanda['STATUS'] == "SEQUENCIADO"]

# ─── 5. INDICADORES DO TOPO DO DASHBOARD ───
st.sidebar.header("🗓️ Filtro MI Operação")
st.sidebar.write(f"⏰ **Hora Atual:** {agora_br.strftime('%H:%M')}")

datas_planejadas = sorted(df_seq_geral['DT_SEQUENCIADO'].dropna().unique())
if datas_planejadas:
    hoje_timestamp = pd.Timestamp(hoje_br)
    indice_padrao = datas_planejadas.index(hoje_timestamp) if hoje_timestamp in datas_planejadas else len(datas_planejadas) - 1
    data_selecionada = st.sidebar.selectbox(
        "Selecione o Dia para o Sequenciado:", 
        options=datas_planejadas, 
        index=indice_padrao, 
        format_func=lambda x: pd.to_datetime(x).strftime('%d/%m/%Y')
    )
    df_seq_filtrado = df_seq_geral[df_seq_geral['DT_SEQUENCIADO'] == data_selecionada]
else:
    df_seq_filtrado = df_seq_geral

c1, c2, c3 = st.columns(3)
with c1:
    v_sobras = df_sobras_geral['VOLUME_TOTAL'].sum() if not df_sobras_geral.empty else 0
    st.metric("🔴 Sobras MI (Total Carteira)", f"{v_sobras} Acessos")
with c2:
    v_filtrado = df_seq_filtrado['VOLUME_TOTAL'].sum() if not df_seq_filtrado.empty else 0
    st.metric("🟢 Sequenciado no Dia", f"{v_filtrado} Acessos")
with c3:
    total_match = len(df_seq_filtrado[df_seq_filtrado['DEU_MATCH'].str.contains('SIM|EM ANDAMENTO', regex=True)])
    st.metric("📊 Cargas MI Ativas/Feitas", f"{total_match} Registros")

st.markdown("---")
tab_sobras, tab_seq = st.tabs(["⚠️ Carteira Geral de Sobras (Visão Gerencial)", "✅ Demandas Sequenciadas MI"])

# ─── 📂 ABA 1: CARTEIRA GERAL DE SOBRAS ───
with tab_sobras:
    if not df_sobras_geral.empty:
        df_sobras_processamento = df_sobras_geral.copy()
        df_sobras_processamento['DT_PERCURSO_NORMALIZADA'] = pd.to_datetime(df_sobras_processamento['DT_PERCURSO'], errors='coerce')
        
        st.markdown("### 🗓️ Saldo de Sobras Acumulado por Data do Percurso")
        
        resumo_datas_sobras = df_sobras_processamento.groupby('DT_PERCURSO_NORMALIZADA').agg(
            TOTAL_ACESSOS=('VOLUME_TOTAL', 'sum'),
            QTD_PERCURSOS=('PERCURSO', 'count')
        ).reset_index().sort_values('DT_PERCURSO_NORMALIZADA')
        
        colunas_cards = st.columns(min(len(resumo_datas_sobras), 4))
        for index, row_card in resumo_datas_sobras.reset_index().iterrows():
            idx_col = index % 4
            if index > 0 and idx_col == 0:
                colunas_cards = st.columns(min(len(resumo_datas_sobras) - index, 4))
                
            dt_card_formatada = row_card['DT_PERCURSO_NORMALIZADA'].strftime('%d/%m/%Y')
            volume_card_acessos = int(row_card['TOTAL_ACESSOS'])
            qtd_percursos = int(row_card['QTD_PERCURSOS'])
            
            with colunas_cards[idx_col]:
                st.markdown(f"""
                <div style="background-color: #f8fafc; border-left: 5px solid #ef4444; border-radius: 8px; padding: 15px; margin-bottom: 15px; border-right: 1px solid #e2e8f0; border-top: 1px solid #e2e8f0; border-bottom: 1px solid #e2e8f0;">
                    <div style="font-size: 0.8rem; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px;">📅 {dt_card_formatada}</div>
                    <div style="font-size: 1.8rem; font-weight: 800; color: #1e293b; line-height: 1.1; margin: 8px 0;">{volume_card_acessos} <span style="font-size: 0.9rem; font-weight: 400; color: #64748b;">Acessos</span></div>
                    <div style="font-size: 0.85rem; font-weight: 600; color: #b91c1c;">📦 {qtd_percursos} Percurso(s) Pendente(s)</div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("### 📊 Detalhamento de Canais por Janela de Sobra")
        df_dinamica_sobras = df_sobras_processamento.groupby([df_sobras_processamento['DT_PERCURSO_NORMALIZADA'].dt.strftime('%d/%m/%Y'), 'CANAL']).agg(
            Soma_CXS=('CXS', 'sum'),
            Soma_PLS=('PLS', 'sum'),
            Acessos_Totais=('VOLUME_TOTAL', 'sum'),
            Percursos=('PERCURSO', 'count')
        ).rename_axis(['Data Percurso', 'Canal Comercial'])
        
        # 🛡️ INJEÇÃO COMPATIBILIDADE: Linha de Total Geral para Sobras
        total_sobras_linha = pd.DataFrame([{
            'Soma_CXS': df_dinamica_sobras['Soma_CXS'].sum(),
            'Soma_PLS': df_dinamica_sobras['Soma_PLS'].sum(),
            'Acessos_Totais': df_dinamica_sobras['Acessos_Totais'].sum(),
            'Percursos': df_dinamica_sobras['Percursos'].sum()
        }], index=pd.MultiIndex.from_tuples([('TOTAL GERAL', '')], names=['Data Percurso', 'Canal Comercial']))
        df_dinamica_sobras = pd.concat([df_dinamica_sobras, total_sobras_linha])
        
        st.dataframe(df_dinamica_sobras.rename(columns={
            'Soma_CXS': 'Soma de CXS', 'Soma_PLS': 'Soma de PLS', 'Acessos_Totais': 'Acessos Totais'
        }), use_container_width=True)
        
        with st.expander("📋 Ver Detalhamento Técnico Aberto (Linha por Linha)", expanded=False):
            df_sobras_processamento['Data_Fis_Percurso'] = df_sobras_processamento['DT_PERCURSO_NORMALIZADA'].dt.strftime('%d/%m/%Y')
            st.dataframe(
                df_sobras_processamento[['PERCURSO', 'CANAL', 'CXS', 'PLS', 'VOLUME_TOTAL', 'STATUS', 'Data_Fis_Percurso']].rename(columns={
                    'VOLUME_TOTAL': 'Acessos', 'STATUS': 'Status Planilha', 'Data_Fis_Percurso': 'Data do Percurso'
                }), use_container_width=True, hide_index=True
            )
    else:
        st.success("✨ Excelente! Nenhuma sobra ou pendência de Mercado Interno na carteira.")

# ─── 📂 ABA 2: DEMANDAS SEQUENCIADAS MI ───
with tab_seq:
    if not df_seq_filtrado.empty:
        df_seq_view = df_seq_filtrado.copy()
        df_seq_view['1º Firme'] = pd.to_datetime(df_seq_view['DT_1_FIRME'], errors='coerce').dt.strftime('%d/%m/%Y')
        df_seq_view['Data Fís. Percurso'] = pd.to_datetime(df_seq_view['DT_PERCURSO'], errors='coerce').dt.strftime('%d/%m/%Y')
        
        st.markdown("### 📊 Tabela Dinâmica: Abertura Volumétrica Guardada por Canal Comercial")
        
        df_dinamica_seq = df_seq_view.groupby('CANAL').agg(
            Soma_de_CXS=('CXS', 'sum'),
            Soma_de_PLS=('PLS', 'sum'),
            Acessos_Agendados=('VOLUME_TOTAL', 'sum'),
            Qtd_Percursos=('PERCURSO', 'count')
        ).rename_axis('Canal Comercial')
        
        # 🛡️ INJEÇÃO COMPATIBILIDADE: Linha de Total Geral para Sequenciados
        total_seq_linha = pd.DataFrame([{
            'Soma_de_CXS': df_dinamica_seq['Soma_de_CXS'].sum(),
            'Soma_de_PLS': df_dinamica_seq['Soma_de_PLS'].sum(),
            'Acessos_Agendados': df_dinamica_seq['Acessos_Agendados'].sum(),
            'Qtd_Percursos': df_dinamica_seq['Qtd_Percursos'].sum()
        }], index=pd.Index(['TOTAL GERAL'], name='Canal Comercial'))
        df_dinamica_seq = pd.concat([df_dinamica_seq, total_seq_linha])
        
        st.dataframe(df_dinamica_seq.rename(columns={
            'Soma_de_CXS': 'Soma de CXS',
            'Soma_de_PLS': 'Soma de PLS',
            'Acessos_Agendados': 'Acessos Agendados (Total)'
        }), use_container_width=True)
        
        st.markdown("### 📋 Inspeção das Cargas em Linha")
        cols_seq = ['PERCURSO', 'CANAL', 'CXS', 'PLS', 'VOLUME_TOTAL', '1º Firme', 'Data Fís. Percurso', 'TURNO_ALOCADO', 'DEU_MATCH', 'TURNO_REALIZOU_VIEW']
        st.dataframe(
            df_seq_view[cols_seq].rename(columns={
                'VOLUME_TOTAL': 'Acessos',
                'TURNO_ALOCADO': 'Turno Planejado',
                'DEU_MATCH': 'Status SLA',
                'TURNO_REALIZOU_VIEW': 'Situação Real da Operação'
            }), use_container_width=True, hide_index=True
        )
    else:
        st.info("Nenhum percurso sequenciado de MI encontrado para a data selecionada.")