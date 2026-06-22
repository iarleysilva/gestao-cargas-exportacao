import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Laboratório Avançado MI", layout="wide")
st.title("🔬 Laboratório de Testes Avançados e Perfil de Canais — MI")
st.write("Exame profundo da base histórica focado no ciclo real (Data 1º Firme até DT PERCURSO).")
st.markdown("---")

# ─── 1. CAPTURA DA PLANILHA ORIGINAL SEM ALTERAÇÕES ───
URL_MI_RAW = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSqUnWPArdoAcBGkShJALYLN7SzmXeKbus_mzDiT9iP3B3iHEEfRdm1LEVSKEllLLnjgcgX8Lajn7k-/pub?gid=1330445331&single=true&output=csv"

@st.cache_data
def carregar_base_teste():
    try:
        df_raw = pd.read_csv(URL_MI_RAW)
        return df_raw
    except Exception as e:
        st.error(f"Erro ao conectar com a URL: {e}")
        return None

df = carregar_base_teste()

if df is None or df.empty:
    st.error("Não foi possível carregar a base de teste.")
    st.stop()

# ─── 2. PROCESSAMENTO DAS DATAS REAIS (POSIÇÃO RIGIDA SEGURO) ───
# Força o mapeamento da 3ª coluna física da planilha (índice 2) para ignorar caracteres invisíveis de espaço
df["DT_NASCIMENTO_REAL"] = pd.to_datetime(df.iloc[:, 2], dayfirst=True, errors="coerce")

# Demais datas mapeadas diretamente pelos nomes literais normais
df["DT_PRAZO_LIMITE"] = pd.to_datetime(df["DT PERCURSO"], dayfirst=True, errors="coerce")
df["DT_ESTEIRA_EXEC"] = pd.to_datetime(df["DATA SEQUENCIADO"], dayfirst=True, errors="coerce")
df["DT_DESEJADO_ANTIGO"] = pd.to_datetime(df["PROGRAMADO"], dayfirst=True, errors="coerce")

# O Tempo Real entre as duas datas soberanas (Ciclo de Vida de Atendimento)
df["CICLO_ATENDIMENTO_REAL"] = (df["DT_PRAZO_LIMITE"] - df["DT_NASCIMENTO_REAL"]).dt.days
df["GAP_DESEJADO_VS_REAL"] = (df["DT_DESEJADO_ANTIGO"] - df["DT_NASCIMENTO_REAL"]).dt.days

# ─── 3. VERTENTES VOLUMÉTRICAS SEGURAS ───
df["CXS_NUM"] = pd.to_numeric(df["CXS"], errors="coerce").fillna(0).astype(int)
df["PLS_NUM"] = pd.to_numeric(df["PLS"], errors="coerce").fillna(0).astype(int)
df["ACESSOS_NUM"] = df["CXS_NUM"] + df["PLS_NUM"]
df["PESO_NUM"] = pd.to_numeric(df["PESO"], errors="coerce").fillna(0.0)

df["M2_TOTAL_AMBIENTE"] = (
    pd.to_numeric(df["Shop M2"], errors="coerce").fillna(0.0) +
    pd.to_numeric(df["Rev M2"], errors="coerce").fillna(0.0) +
    pd.to_numeric(df["Exp M2"], errors="coerce").fillna(0.0) +
    pd.to_numeric(df["Eng M2"], errors="coerce").fillna(0.0) +
    pd.to_numeric(df["Outros M2"], errors="coerce").fillna(0.0)
)

# ─── 📊 CONSTRUÇÃO DOS DATASETS DE ANÁLISE ───
df_valid_vida = df.dropna(subset=["DT_NASCIMENTO_REAL", "DT_PRAZO_LIMITE"])
df_tempo_real = df_valid_vida.groupby("CANAL").agg(
    Ciclo_Medio_Dias=("CICLO_ATENDIMENTO_REAL", "mean"),
    Norte_Desejado_Antigo=("GAP_DESEJADO_VS_REAL", "mean"),
    Total_Percursos=("PERCURSO", "count")
).reset_index()
df_tempo_real["Ciclo_Medio_Dias"] = df_tempo_real["Ciclo_Medio_Dias"].round(1)
df_tempo_real["Norte_Desejado_Antigo"] = df_tempo_real["Norte_Desejado_Antigo"].round(1)

df_transporte = df.groupby(["CANAL", "MODELO"]).agg(
    Acessos_Totais=("ACESSOS_NUM", "sum"),
    M2_Total=("M2_TOTAL_AMBIENTE", "sum"),
    Peso_Total=("PESO_NUM", "sum"),
    Qtd_Percursos=("PERCURSO", "count")
).reset_index()

df["RELEASE_LIMPO"] = df["Release Status"].astype(str).str.strip().fillna("Não Informado")
df_trava = df.groupby(["CANAL", "RELEASE_LIMPO"]).agg(
    Qtd_Percursos=("PERCURSO", "count"),
    Acessos_Impactados=("ACESSOS_NUM", "sum")
).reset_index()

df_prioridade = df.groupby(["CANAL", "PRIORIDADE PERCURSO"]).agg(
    Acessos_Totais=("ACESSOS_NUM", "sum"),
    Qtd_Percursos=("PERCURSO", "count")
).reset_index().sort_values(["CANAL", "PRIORIDADE PERCURSO"])

# ─── 📥 MECANISMO DE DOWNLOAD EM CSV (FLEXÍVEL E SEM ERROS DE ENGINE) ───
st.sidebar.header("💾 Central de Exportação")
st.sidebar.write("Gere o arquivo consolidado do ciclo de vida real em formato de texto para análise mestre.")

csv_buffer = df_tempo_real.to_csv(index=False).encode("utf-8")

st.sidebar.download_button(
    label="📥 Baixar Ciclo Real de Vida (CSV)",
    data=csv_buffer,
    file_name="diagnostico_ciclo_real_mi.csv",
    mime="text/csv"
)

# ─── 🖥️ EXIBIÇÃO DAS TABELAS NA TELA ───
st.subheader("1. ⏱️ Ciclo de Vida Real: Nascimento (1º Firme) até o Prazo Limite (DT Percurso)")
st.dataframe(df_tempo_real.rename(columns={
    "CANAL": "Canal Comercial",
    "Ciclo_Medio_Dias": "Janela Total do Percurso na Fábrica (Dias Úteis)",
    "Norte_Desejado_Antigo": "Referência Histórica Sistema Antigo (Dias)",
    "Total_Percursos": "Amostra Percursos"
}), use_container_width=True, hide_index=True)

st.subheader("2. 🚛 Perfil de Cubagem, Pesos e Modelos de Transporte")
st.dataframe(df_transporte.rename(columns={
    "CANAL": "Canal Comercial",
    "MODELO": "Modelo do Veículo Escalado",
    "Acessos_Totais": "Total Acessos (CXS+PLS)",
    "M2_Total": "M² Total Movimentado",
    "Peso_Total": "Peso Total (KG)",
    "Qtd_Percursos": "Volume de Percursos"
}), use_container_width=True, hide_index=True)

st.subheader("3. 🛡️ Diagnóstico de Trava Administrativa: Release Status por Canal")
st.dataframe(df_trava.rename(columns={
    "CANAL": "Canal Comercial",
    "RELEASE_LIMPO": "Status de Liberação (Release Status)",
    "Qtd_Percursos": "Quantidade de Percursos",
    "Acessos_Impactados": "Acessos Retidos"
}), use_container_width=True, hide_index=True)

st.subheader("4. 🎯 Perfil de Criticidade e Priorização da Carteira")
st.dataframe(df_prioridade.rename(columns={
    "CANAL": "Canal Comercial",
    "PRIORIDADE PERCURSO": "Nível de Prioridade do Percurso",
    "Acessos_Totais": "Volume de Acessos na Fila",
    "Qtd_Percursos": "Quantidade de Cargas"
}), use_container_width=True, hide_index=True)