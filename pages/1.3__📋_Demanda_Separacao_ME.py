import streamlit as st
import pandas as pd
from datetime import datetime, time
import zoneinfo
from src.core.data_loader import carregar_dados_separacao, carregar_execucao_turnos

st.set_page_config(page_title="Demanda Separação ME", layout="wide")

st.title("📦 Módulo: Demanda & Fluxo de Separação — ME")
st.write("SLA Logístico Avançado: Validação de Permanência Física por Janela de Turno.")
st.markdown("---")

# ─── 1. CARREGAMENTO DOS DADOS ORIGINAIS DA NOVA ABA V1 ───
retorno_demanda = carregar_dados_separacao()
df_execucao = carregar_execucao_turnos()

if isinstance(retorno_demanda, tuple):
    df_demanda = retorno_demanda[0]
else:
    df_demanda = retorno_demanda

if isinstance(df_execucao, tuple):
    df_execucao = df_execucao[0]

if df_demanda is None:
    st.error("⚠️ Erro ao conectar ou extrair os dados da planilha de demandas.")
    st.stop()

# ─── 2. PADRONIZAÇÃO DO PERCURSO (CHAVE ÚNICA DE MATCH) ───
df_demanda['PERCURSO'] = df_demanda['PERCURSO'].astype(str).str.strip().str.replace('.0', '', regex=False)
df_demanda['DT_SEQUENCIADO'] = pd.to_datetime(df_demanda['DT_SEQUENCIADO'], errors='coerce')

# Cria o conjunto de busca cega para saber onde o percurso foi localizado
percursos_bipados_fabrica = set(df_execucao['PERCURSO'].dropna().unique()) if df_execucao is not None else set()

# ─── 3. RELÓGIO OPERACIONAL DE BRASÍLIA ───
fuso_br = zoneinfo.ZoneInfo("America/Sao_Paulo")
agora_br = datetime.now(fuso_br)
hoje_br = agora_br.date()
hora_atual = agora_br.time()

# ─── 4. MOTOR METICULOSO DE SLA: REGRA DE PERMANÊNCIA DO DADO ───
def calcular_SLA_permanencia(row):
    percurso_id = row['PERCURSO']
    turno_planejado = str(row['TURNO_ALOCADO']).strip().replace('.0', '')
    status_seq = str(row['STATUS']).upper().strip()
    data_carga = row['DT_SEQUENCIADO'].date() if pd.notna(row['DT_SEQUENCIADO']) else hoje_br

    # Procura cega: O percurso está presente em qualquer aba da fábrica agora?
    existe_na_fabrica = percurso_id in percursos_bipados_fabrica

    # Cenário A: Carteira de Sobras (Não Sequenciados)
    if status_seq == "NÃO SEQUENCIADO":
        if existe_na_fabrica:
            return 'OPORTUNIDADE ⚡', 'Carregado/Separado via Oportunidade ⚡'
        return 'AGUARDANDO ⏳', 'Carteira de Sobras em Aberto'

    # Cenário B: Cargas Históricas (Dias Passados)
    if data_carga < hoje_br:
        if existe_na_fabrica:
            return 'SIM 🟢', 'Confirmado e Retido no Prazo'
        return 'NÃO ADERIDO ❌', 'Não Bipado no Prazo (Dia Encerrado) 🛑'
        
    # Cenário C: Cargas para Datas Futuras
    elif data_carga > hoje_br:
        return 'AGUARDANDO INÍCIO SEP ⏳', 'Programado para Data Futura'

    # Cenário D: CARGAS DE HOJE (JULGAMENTO DO TEMPO DO EVENTO)
    if turno_planejado in ["1", "1.0"]:
        # Janela T1: 05:00 às 13:30
        if hora_atual < time(5, 0):
            return 'AGUARDANDO INÍCIO SEP ⏳', 'Aguardando Início do Turno 1'
        elif time(5, 0) <= hora_atual < time(13, 30):
            if existe_na_fabrica:
                return 'EM ANDAMENTO ⚙️', 'Identificado na Aba (Aguardando Fim do Turno)'
            return 'AGUARDANDO ⏳', 'Aguardando Entrada no Turno 1'
        else:
            if existe_na_fabrica:
                return 'SIM 🟢', 'Confirmado (Dado Permaneceu na Planilha)'
            return 'NÃO ADERIDO ❌', 'Turno 1 Encerrado sem Aderência 🛑'

    elif turno_planejado in ["2", "2.0"]:
        # Janela T2: 13:30 às 22:00
        if hora_atual < time(13, 30):
            return 'AGUARDANDO INÍCIO SEP ⏳', 'Aguardando Início do Turno 2'
        elif time(13, 30) <= hora_atual < time(22, 0):
            if existe_na_fabrica:
                return 'EM ANDAMENTO ⚙️', 'Identificado na Aba (Aguardando Fim do Turno)'
            return 'AGUARDANDO ⏳', 'Aguardando Entrada no Turno 2'
        else:
            if existe_na_fabrica:
                return 'SIM 🟢', 'Confirmado (Dado Permaneceu na Planilha)'
            return 'NÃO ADERIDO ❌', 'Turno 2 Encerrado sem Aderência 🛑'

    elif turno_planejado in ["3", "3.0"]:
        # Janela T3: 22:00 às 05:00 do dia seguinte
        if hora_atual < time(22, 0) and hora_atual >= time(5, 0):
            return 'AGUARDANDO INÍCIO SEP ⏳', 'Aguardando Início do Turno 3'
        else:
            if existe_na_fabrica:
                return 'EM ANDAMENTO ⚙️', 'Identificado na Aba (Aguardando Fim do Turno)'
            return 'AGUARDANDO ⏳', 'Aguardando Entrada no Turno 3'

    return 'AGUARDANDO ⏳', 'Sem Definição de Turno'

# Aplica a inteligência de classificação
res_SLA = df_demanda.apply(calcular_SLA_permanencia, axis=1)
df_demanda['DEU_MATCH'] = [x[0] for x in res_SLA]
df_demanda['TURNO_REALIZOU_VIEW'] = [x[1] for x in res_SLA]

# Segrega as visões de tabelas
df_sobras_geral = df_demanda[df_demanda['STATUS'].astype(str).str.upper().str.strip() == "NÃO SEQUENCIADO"]
df_seq_geral = df_demanda[df_demanda['STATUS'].astype(str).str.upper().str.strip() == "SEQUENCIADO"]

# ─── 5. FILTROS E INTERFACE GRÁFICA DO STREAMLIT ───
st.sidebar.header("🗓️ Filtro de Operação")
st.sidebar.write(f"⏰ **Hora Atual (BR):** {agora_br.strftime('%H:%M')}")

datas_planejadas = sorted(df_seq_geral['DT_SEQUENCIADO'].dropna().unique())
if datas_planejadas:
    hoje_timestamp = pd.Timestamp(hoje_br)
    indice_padrao = datas_planejadas.index(hoje_timestamp) if hoje_timestamp in datas_planejadas else len(datas_planejadas) - 1
    data_selecionada = st.sidebar.selectbox(
        "Selecione o Dia:", 
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
    st.metric("🔴 Sobras Geral", f"{v_sobras} Acessos")
with c2:
    v_filtrado = df_seq_filtrado['VOLUME_TOTAL'].sum() if not df_seq_filtrado.empty else 0
    st.metric("🟢 Programado no Dia", f"{v_filtrado} Acessos")
with c3:
    total_match = len(df_seq_filtrado[df_seq_filtrado['DEU_MATCH'].str.contains('SIM|EM ANDAMENTO', regex=True)])
    st.metric("📊 Cargas Ativas/Feitas", f"{total_match} Registros")

st.markdown("---")
tab_seq, tab_sobras = st.tabs(["✅ Demandas Sequenciadas ME", "⚠️ Carteira Geral de Sobras (Não Sequenciadas)"])

with tab_seq:
    if not df_seq_filtrado.empty:
        df_seq_view = df_seq_filtrado.copy()
        df_seq_view['1º Firme'] = pd.to_datetime(df_seq_view['DT_1_FIRME'], errors='coerce').dt.strftime('%d/%m/%Y').fillna(df_seq_view['DT_1_FIRME'].astype(str))
        df_seq_view['Data Fís. Percurso'] = pd.to_datetime(df_seq_view['DT_PERCURSO'], errors='coerce').dt.strftime('%d/%m/%Y').fillna(df_seq_view['DT_PERCURSO'].astype(str))
        
        cols_seq = ['PERCURSO', 'VOLUME_TOTAL', '1º Firme', 'Data Fís. Percurso', 'TURNO_ALOCADO', 'DEU_MATCH', 'TURNO_REALIZOU_VIEW']
        st.dataframe(
            df_seq_view[cols_seq].rename(columns={
                'VOLUME_TOTAL': 'Acessos',
                'TURNO_ALOCADO': 'Turno Planejado',
                'DEU_MATCH': 'Status SLA',
                'TURNO_REALIZOU_VIEW': 'Situação Real da Operação'
            }), use_container_width=True, hide_index=True
        )
    else:
        st.info("Nenhum percurso sequenciado encontrado para este dia.")

with tab_sobras:
    if not df_sobras_geral.empty:
        df_sobras_view = df_sobras_geral.copy()
        df_sobras_view['Status SLA'] = df_sobras_view['DEU_MATCH']
        cols_sobras = ['PERCURSO', 'VOLUME_TOTAL', 'Status SLA', 'TURNO_REALIZOU_VIEW']
        st.dataframe(
            df_sobras_view[cols_sobras].rename(columns={'VOLUME_TOTAL': 'Acessos', 'TURNO_REALIZOU_VIEW': 'Histórico / Situação'}), 
            use_container_width=True, hide_index=True
        )