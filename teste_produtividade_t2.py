import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Auditoria Turno 2", layout="wide")
st.title("🔬 Laboratório de Testes: Produtividade Histórica — Turno 2 (Calibrado)")
st.write("Análise purificada focada em capacidade humana e volumetria diária: Caixas vs Paletes Fechados.")
st.markdown("---")

# ─── 1. CAPTURA DA URL PÚBLICA DO TURNO 2 EM FORMATO CSV ───
URL_T2_PUBLIC_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTS8d44ajH4_Hm7uaAWVbejIzmbMqK8fCbYEPYWddDc4pnbFBhyOye4vs6QmtJ-a51V-b9HDTFPDcSw/pub?gid=1250180014&single=true&output=csv"

@st.cache_data
def carregar_historico_t2():
    try:
        df_raw = pd.read_csv(URL_T2_PUBLIC_CSV)
        df_raw.columns = df_raw.columns.str.strip()
        return df_raw
    except Exception as e:
        st.error(f"Erro ao conectar com a base do T2 via URL Pública: {e}")
        return None

df = carregar_historico_t2()

if df is None or df.empty:
    st.error("Não foi possível processar o histórico do Turno 2.")
    st.stop()

# ─── 2. HIGIENIZAÇÃO RÍGIDA E DE DUPLICIDADES (REGRA DE OURO) ───
df["PERCURSO"] = df["PERCURSO"].astype(str).str.strip()
df["DATA_TRATADA"] = pd.to_datetime(df["DATA"], dayfirst=True, errors="coerce")

total_linhas_brutas = len(df)

# REGRA DE OURO: Mantém apenas a primeira aparição do percurso para eliminar recheques e duplicidades
df_limpo = df.drop_duplicates(subset=["PERCURSO"], keep="first").copy()

# ─── 3. PROCESSAMENTO NUMÉRICO E MOTOR DE REGRAS OPERACIONAL (T2) ───
df_limpo["MI_REG"] = pd.to_numeric(df_limpo["Total Acessos MI"].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
df_limpo["ME_REG"] = pd.to_numeric(df_limpo["Total Acessos ME"].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
df_limpo["EXP_M2_CHECK"] = pd.to_numeric(df_limpo["Exportação"].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)

df_limpo["CXS_NUM"] = pd.to_numeric(df_limpo["Acessos Caixa"], errors="coerce").fillna(0).astype(int)
df_limpo["PLS_NUM"] = pd.to_numeric(df_limpo["Acessos Palete"], errors="coerce").fillna(0).astype(int)

# REGRA 1: Expurgar linhas sem atividade de movimentação (Burocracias zeradas)
linhas_antes_filtro_zero = len(df_limpo)
mask_zeros = (df_limpo["EXP_M2_CHECK"] == 0) & (df_limpo["MI_REG"] == 0) & (df_limpo["ME_REG"] == 0)
df_limpo = df_limpo[~mask_zeros].copy()
linhas_zeradas_expurgadas = linhas_antes_filtro_zero - len(df_limpo)

# REGRA 2: Decodificação Operacional (Identificação de Desprezo de Paletes)
def processar_linhas_calibradas_t2(row):
    cx = row["CXS_NUM"]
    pl = row["PLS_NUM"]
    me = row["ME_REG"]
    mi = row["MI_REG"]
    operador = str(row["OPERADOR"]).upper().strip()
    
    is_me = (me > 0) or (row["EXP_M2_CHECK"] > 0 and mi == 0)
    total_registrado = me if is_me else mi
    
    if operador == "CONFERENTE" or (total_registrado == cx and pl > 0):
        paletes_desprezados = pl
        paletes_reais = 0
        caixas_reais = cx
    else:
        paletes_desprezados = 0
        paletes_reais = pl
        caixas_reais = cx

    return pd.Series([caixas_reais, paletes_reais, paletes_desprezados, is_me])

df_limpo[["CX_REAL", "PL_REAL", "PL_DESPREZADO", "IS_ME"]] = df_limpo.apply(processar_linhas_calibradas_t2, axis=1)
df_limpo["ACESSOS_REAIS"] = df_limpo["CX_REAL"] + df_limpo["PL_REAL"]

# Painel lateral informativo simplificado
st.sidebar.header("🛡️ Auditoria de Saneamento — T2")
st.sidebar.metric("Linhas Brutas Lidas", total_linhas_brutas)
st.sidebar.metric("Linhas Operacionais Ativas", len(df_limpo))
st.sidebar.warning(f"🚨 {total_linhas_brutas - len(df_limpo)} registros (duplicidades/burocracias) foram removidos.")

# ─── 📊 RELATÓRIO 1: RANKING DE PERFORMANCE POR OPERADOR ───
st.subheader("1. 🏃‍♂️ Comportamento e Entrega Real por Operador (Média de Acessos Calibrados — T2)")

df_operadores = df_limpo.groupby("OPERADOR").agg(
    Percursos_Realizados=("PERCURSO", "count"),
    Soma_Caixas=("CX_REAL", "sum"),
    Soma_Paletes=("PL_REAL", "sum"),
    Total_Acessos_Limpos=("ACESSOS_REAIS", "sum"),
    Media_Acessos_Por_Carga=("ACESSOS_REAIS", "mean"),
    Paletes_Desprezados_Pelo_Modelo=("PL_DESPREZADO", "sum")
).reset_index()

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

# ─── 📊 RELATÓRIO 2: EVOLUÇÃO CRONOLÓGICA DIÁRIA DO TURNO 2 (APENAS MI) ───
st.subheader("2. 📅 Termômetro Diário do Turno 2 (Mercado Interno Puro)")

# Filtra rigorosamente mantendo apenas linhas onde NÃO é Mercado Externo (IS_ME == False)
df_mi_puro = df_limpo[df_limpo["IS_ME"] == False].copy()

df_diario_mi = df_mi_puro.dropna(subset=["DATA_TRATADA"]).groupby("DATA_TRATADA").agg(
    Cargas_No_Dia=("PERCURSO", "count"),
    Soma_Caixas_MI=("CX_REAL", "sum"),
    Soma_Paletes_MI=("PL_REAL", "sum"),
    Acessos_Totais_MI=("ACESSOS_REAIS", "sum"),
    Operadores_Ativos=("OPERADOR", "nunique")
).reset_index().sort_values("DATA_TRATADA", ascending=False)

df_diario_mi["DATA_TRATADA"] = df_diario_mi["DATA_TRATADA"].dt.strftime("%d/%m/%Y")

st.dataframe(
    df_diario_mi.rename(columns={
        "DATA_TRATADA": "Data da Operação",
        "Cargas_No_Dia": "Total Cargas Limpas",
        "Soma_Caixas_MI": "Acessos Caixa MI",
        "Soma_Paletes_MI": "Acessos Palete MI",
        "Acessos_Totais_MI": "Soma Acessos Total MI",
        "Operadores_Ativos": "Qtd Operadores"
    }),
    use_container_width=True,
    hide_index=True
)

# ─── 📊 3. RELATÓRIO DE DESPERDÍCIO DE MODELO (PALETES IGNORADOS) ───
st.markdown("---")
st.subheader("🪵 3. Relatório de Desperdício de Modelo (Turno 2)")
total_desprezado = df_operadores["Paletes_Desprezados_Pelo_Modelo"].sum()
st.metric("Total de Paletes Desprezados no Turno 2", int(total_desprezado))

# ─── 📥 CENTRAL DE EXPORTAÇÃO DO T2 ───
st.sidebar.markdown("---")
st.sidebar.header("💾 Exportar Limpeza — T2")
csv_buffer = df_limpo.to_csv(index=False).encode("utf-8")
st.sidebar.download_button(
    label="📥 Baixar Base T2 Purificada",
    data=csv_buffer,
    file_name="base_turno2_calibrada.csv",
    mime="text/csv"
)