import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Auditoria Turno 3", layout="wide")
st.title("🔬 Laboratório de Testes: Produtividade Histórica — Turno 3 (Calibrado)")
st.write("Análise analítica purificada com decodificação operacional real: Caixas vs Paletes Fechados.")
st.markdown("---")

# ─── 1. CAPTURA DA URL PÚBLICA EN FORMATO CSV ───
URL_T3_PUBLIC_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTS8d44ajH4_Hm7uaAWVbejIzmbMqK8fCbYEPYWddDc4pnbFBhyOye4vs6QmtJ-a51V-b9HDTFPDcSw/pub?gid=1415290687&single=true&output=csv"

@st.cache_data
def carregar_historico_t3():
    try:
        df_raw = pd.read_csv(URL_T3_PUBLIC_CSV)
        # Limpa espaços invisíveis que possam vir nas pontas das colunas
        df_raw.columns = df_raw.columns.str.strip()
        return df_raw
    except Exception as e:
        st.error(f"Erro ao conectar com a base do T3 via URL Pública: {e}")
        return None

df = carregar_historico_t3()

if df is None or df.empty:
    st.error("Não foi possível processar o histórico do Turno 3.")
    st.stop()

# ─── 2. HIGIENIZAÇÃO RÍGIDA E DE DUPLICIDADES ───
df["PERCURSO"] = df["PERCURSO"].astype(str).str.strip()
df["DATA_TRATADA"] = pd.to_datetime(df["DATA"], dayfirst=True, errors="coerce")

total_linhas_brutas = len(df)

# REGRA DE OURO DO IARLEY: Mantém apenas a PRIMEIRA aparição do percurso (de cima para baixo)
df_limpo = df.drop_duplicates(subset=["PERCURSO"], keep="first").copy()

# ─── 3. PROCESSAMENTO NUMÉRICO E MOTOR DE CALIBRAÇÃO OPERACIONAL ───
# Tratamento de strings e vírgulas nas colunas registradas para evitar quebras de leitura do Python
df_limpo["MI_REG"] = pd.to_numeric(df_limpo["Total Acessos MI"].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
df_limpo["ME_REG"] = pd.to_numeric(df_limpo["Total Acessos ME"].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
df_limpo["EXP_M2_CHECK"] = pd.to_numeric(df_limpo["Exportação"].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)

df_limpo["CXS_NUM"] = pd.to_numeric(df_limpo["Acessos Caixa"], errors="coerce").fillna(0).astype(int)
df_limpo["PLS_NUM"] = pd.to_numeric(df_limpo["Acessos Palete"], errors="coerce").fillna(0).astype(int)

# REGRA 1: Desprezar absolutamente linhas onde Exportação, Total MI e Total ME são 0 (Não é separação)
linhas_antes_filtro_zero = len(df_limpo)
mask_zeros = (df_limpo["EXP_M2_CHECK"] == 0) & (df_limpo["MI_REG"] == 0) & (df_limpo["ME_REG"] == 0)
df_limpo = df_limpo[~mask_zeros].copy()
linhas_zeradas_expurgadas = linhas_antes_filtro_zero - len(df_limpo)

# REGRA 2: Decodificação Operacional (Caixas vs Paletes Reais vs Desprezados)
def processar_linhas_calibradas(row):
    cx = row["CXS_NUM"]
    pl = row["PLS_NUM"]
    me = row["ME_REG"]
    mi = row["MI_REG"]
    operador = str(row["OPERADOR"]).upper().strip()
    
    # Identifica se a linha pertence ao Mercado Externo (ME) ou Mercado Interno (MI)
    is_me = (me > 0) or (row["EXP_M2_CHECK"] > 0 and mi == 0)
    total_registrado = me if is_me else mi
    
    # Se o operador for explicitamente CONFERENTE ou se o total digitado bate cravado apenas com a caixa 
    # tendo palete preenchido na linha, o sistema identifica o DESPREZO DO PALETE FECHADO
    if operador == "CONFERENTE" or (total_registrado == cx and pl > 0):
        paletes_desprezados = pl
        paletes_reais = 0
        caixas_reais = cx
    else:
        # Sem correspondência de desprezo, damos o ponto total (esforço combinado completo)
        paletes_desprezados = 0
        paletes_reais = pl
        caixas_reais = cx

    return pd.Series([caixas_reais, paletes_reais, paletes_desprezados, is_me])

df_limpo[["CX_REAL", "PL_REAL", "PL_DESPREZADO", "IS_ME"]] = df_limpo.apply(processar_linhas_calibradas, axis=1)

# O esforço real do Turno passa a ser a soma dos acessos físicos filtrados pela calibração
df_limpo["ACESSOS_REAIS"] = df_limpo["CX_REAL"] + df_limpo["PL_REAL"]

# Painel lateral informativo e auditado sobre a saúde da base de dados
st.sidebar.header("🛡️ Auditoria de Saneamento")
st.sidebar.metric("Linhas Brutas Lidas", total_linhas_brutas)
st.sidebar.metric("Percursos Saneados (Sem Duplicidade)", linhas_antes_filtro_zero)
st.sidebar.metric("Linhas Operacionais Ativas", len(df_limpo))
st.sidebar.warning(f"🚨 {total_linhas_brutas - linhas_antes_filtro_zero} Duplicidades e {linhas_zeradas_expurgadas} linhas de burocracia foram removidas.")

# ─── 📊 RELATÓRIO 1: RANKING DE PERFORMANCE POR OPERADOR ───
st.subheader("1. 🏃‍♂️ Comportamento e Entrega Real por Operador (Média de Acessos Calibrados)")

df_operadores = df_limpo.groupby("OPERADOR").agg(
    Percursos_Realizados=("PERCURSO", "count"),
    Soma_Caixas=("CX_REAL", "sum"),
    Soma_Paletes=("PL_REAL", "sum"),
    Total_Acessos_Limpos=("ACESSOS_REAIS", "sum"),
    Media_Acessos_Por_Carga=("ACESSOS_REAIS", "mean"),
    Paletes_Desprezados_Pelo_Modelo=("PL_DESPREZADO", "sum")
).reset_index()

# Filtra operadores que realmente geraram movimentação física no período
df_operadores = df_operadores[df_operadores["Total_Acessos_Limpos"] > 0].sort_values("Media_Acessos_Por_Carga", ascending=False)
df_operadores["Media_Acessos_Por_Carga"] = df_operadores["Media_Acessos_Por_Carga"].round(1)

st.dataframe(
    df_operadores.rename(columns={
        "OPERADOR": "Nome do Operador",
        "Percursos_Realizados": "Qtd Cargas Separadas",
        "Soma_Caixas": "Acessos Caixa Reais",
        "Soma_Paletes": "Acessos Palete Reais",
        "Total_Acessos_Limpos": "Total Acessos Válidos",
        "Media_Acessos_Por_Carga": "Média de Acessos por Carga (Target: 85)",
        "Paletes_Desprezados_Pelo_Modelo": "🪵 Paletes Ocultos (Desprezados)"
    }),
    use_container_width=True,
    hide_index=True
)

# ─── 📊 RELATÓRIO 2: VOLUME HISTÓRICO DE M² POR VERTENTE DE CANAL ───
st.subheader("2. 📐 Cubagem de M² por Canal Identificado")

canais_colunas = ["Revenda", "Exportação", "Log", "PB SHOP", "Engenharia", "Outros"]
for c in canais_colunas:
    df_limpo[f"{c}_M2"] = pd.to_numeric(df_limpo[c], errors="coerce").fillna(0.0)

df_canais_resumo = pd.DataFrame([{
    "Canal / Vertente": c,
    "M² Total Movimentado": df_limpo[f"{c}_M2"].sum(),
    "Percursos Associated": df_limpo[df_limpo[f"{c}_M2"] > 0]["PERCURSO"].count()
} for c in canais_colunas])

st.dataframe(
    df_canais_resumo.sort_values("M² Total Movimentado", ascending=False),
    use_container_width=True,
    hide_index=True
)

# ─── 📊 RELATÓRIO 3: EVOLUÇÃO CRONOLÓGICA DIÁRIA DO TURNO ───
st.subheader("3. 📅 Termômetro Diário do Turno 3 (Demanda Realizada)")

df_diario = df_limpo.dropna(subset=["DATA_TRATADA"]).groupby("DATA_TRATADA").agg(
    Cargas_No_Dia=("PERCURSO", "count"),
    Acessos_MI=("CX_REAL", lambda x: x[~df_limpo.loc[x.index, "IS_ME"]].sum() + df_limpo.loc[x.index, "PL_REAL"][~df_limpo.loc[x.index, "IS_ME"]].sum()),
    Acessos_ME=("CX_REAL", lambda x: x[df_limpo.loc[x.index, "IS_ME"]].sum() + df_limpo.loc[x.index, "PL_REAL"][df_limpo.loc[x.index, "IS_ME"]].sum()),
    Acessos_Totais=("ACESSOS_REAIS", "sum"),
    Operadores_Ativos=("OPERADOR", "nunique")
).reset_index().sort_values("DATA_TRATADA", ascending=False)

df_diario["DATA_TRATADA"] = df_diario["DATA_TRATADA"].dt.strftime("%d/%m/%Y")

st.dataframe(
    df_diario.rename(columns={
        "DATA_TRATADA": "Data da Operação",
        "Cargas_No_Dia": "Total Cargas Limpas",
        "Acessos_MI": "Acessos MI Calibrados",
        "Acessos_ME": "Acessos ME Calibrados",
        "Acessos_Totais": "Soma Acessos Total",
        "Operadores_Ativos": "Qtd Operadores na Noite"
    }),
    use_container_width=True,
    hide_index=True
)

# ─── 📊 4. SEÇÃO DE AUDITORIA DE PERDAS DE MODELO (PALETES IGNORADOS) ───
st.markdown("---")
st.subheader("🪵 4. Relatório de Desperdício de Modelo (O que o preenchimento antigo ignorava)")
total_desprezado = df_operadores["Paletes_Desprezados_Pelo_Modelo"].sum()
st.metric("Total de Paletes Desprezados no Período", int(total_desprezado), help="Quantidade de movimentações físicas de paletes que o modelo de digitação original acabou anulando.")

# ─── 📥 CENTRAL DE EXPORTAÇÃO EXCLUSIVA DO T3 ───
st.sidebar.markdown("---")
st.sidebar.header("💾 Exportar Limpeza")
csv_buffer = df_limpo.to_csv(index=False).encode("utf-8")
st.sidebar.download_button(
    label="📥 Baixar Base T3 Purificada",
    data=csv_buffer,
    file_name="base_turno3_calibrada.csv",
    mime="text/csv"
)