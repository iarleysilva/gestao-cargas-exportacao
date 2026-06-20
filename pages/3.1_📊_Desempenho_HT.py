import streamlit as st
import pandas as pd
from datetime import datetime
from src.core.data_loader import carregar_realizado_ht

st.set_page_config(page_title="Desempenho HT", layout="wide")

st.title("📊 Módulo 5: Indicadores de Desempenho e Realizado HT")
st.write("Métricas operacionais baseadas estritamente nos registros consolidados da planilha.")
st.markdown("---")

MESES_PT = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
    5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
    9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
}

ano_alvo = st.sidebar.selectbox("1️⃣ Selecione o Ano:", options=["2026", "2027"], index=0)

df_historico = carregar_realizado_ht(ano_alvo)

if df_historico is not None and not df_historico.empty:
    
    # ─── EXTRAÇÃO DE MÊS SEM DELETAR LINHAS (ANTI-LIMBO) ───
    # Em vez de jogar fora linhas que falham no datetime automático, extraímos o mês baseados no texto puro
    def extrair_mes_da_string(data_val):
        data_str = str(data_val).strip()
        # Procura por padrões comuns DD/MM/AAAA ou AAAA-MM-DD
        if '/' in data_str:
            partes = data_str.split('/')
            if len(partes) >= 2:
                try: return int(partes[1])
                except: pass
        elif '-' in data_str:
            partes = data_str.split('-')
            if len(partes) >= 2:
                try: return int(partes[1])
                except: pass
        return 6 # Padrão seguro para Junho caso o formato seja totalmente atípico

    # Usamos uma coluna auxiliar para o mês sem mexer na coluna oficial de data
    df_historico['NUM_MES'] = df_historico['DATA_PROD'].apply(extrair_mes_da_string)
    
    # 1️⃣ Filtro de Mês
    meses_numeros_disponiveis = sorted(df_historico['NUM_MES'].unique(), reverse=True)
    opcoes_mes = ["TODOS O MESES"] + [MESES_PT[m] for m in meses_numeros_disponiveis if m in MESES_PT]
    mes_selecionado_txt = st.sidebar.selectbox("2️⃣ Selecione o Mês:", options=opcoes_mes, index=0)
    
    if mes_selecionado_txt != "TODOS O MESES":
        num_mes_alvo = [k for k, v in MESES_PT.items() if v == mes_selecionado_txt][0]
        df_base_filtrada = df_historico[df_historico['NUM_MES'] == num_mes_alvo]
        label_mes = f"Mês de {mes_selecionado_txt}"
    else:
        df_base_filtrada = df_historico.copy()
        label_mes = "Todos os Meses"

    # 2️⃣ Filtro de Dia (Refinamento)
    st.sidebar.markdown("---")
    refino_dia = st.sidebar.radio("3️⃣ Refinar por Dia?", options=["Todos os Dias do Período", "Data Específica"])
    
    label_dia = ""
    if refino_dia == "Data Específica":
        # Converte para string pura de exibição para o seletor não travar com NaT
        df_base_filtrada['DATA_DISPLAY'] = df_base_filtrada['DATA_PROD'].astype(str).str.slice(0, 10)
        datas_unicas = sorted(df_base_filtrada['DATA_DISPLAY'].unique(), reverse=True)
        
        if datas_unicas:
            data_selecionada_str = st.sidebar.selectbox("Escolha o Dia:", datas_unicas)
            df_base_filtrada = df_base_filtrada[df_base_filtrada['DATA_DISPLAY'] == data_selecionada_str]
            label_dia = f" - Dia {data_selecionada_str}"

    # ─── CONTABILIDADE DIRETA: QUEM FEZ E O QUE FEZ ───
    if not df_base_filtrada.empty:
        
        # Padroniza string de turnos tirando espaços
        df_base_filtrada['TURNO_AUX'] = df_base_filtrada['TURNO'].astype(str).str.replace(" ", "", regex=False).str.upper()
        
        # Separação exata pelos códigos limpos (Alinhado com algarismos romanos da base)
        df_t1 = df_base_filtrada[df_base_filtrada['TURNO_AUX'] == "TURNOI"]
        df_t2 = df_base_filtrada[df_base_filtrada['TURNO_AUX'] == "TURNOII"]
        df_t3 = df_base_filtrada[df_base_filtrada['TURNO_AUX'] == "TURNOIII"]
        
        # --- EXECUÇÃO DAS MÉTRICAS ---
        ciclos_t1 = df_t1['CONCAT'].nunique() if not df_t1.empty else 0
        carga_t1 = df_t1[df_t1['TIPO_FLUXO'] == "CARGA"]['PALLETS'].sum() if not df_t1.empty else 0
        estrados_t1 = df_t1[df_t1['TIPO_FLUXO'] == "ESTRADO"]['PALLETS'].sum() if not df_t1.empty else 0
        total_t1 = carga_t1 + estrados_t1
        
        ciclos_t2 = df_t2['CONCAT'].nunique() if not df_t2.empty else 0
        carga_t2 = df_t2[df_t2['TIPO_FLUXO'] == "CARGA"]['PALLETS'].sum() if not df_t2.empty else 0
        estrados_t2 = df_t2[df_t2['TIPO_FLUXO'] == "ESTRADO"]['PALLETS'].sum() if not df_t2.empty else 0
        total_t2 = carga_t2 + estrados_t2
        
        ciclos_t3 = df_t3['CONCAT'].nunique() if not df_t3.empty else 0
        carga_t3 = df_t3[df_t3['TIPO_FLUXO'] == "CARGA"]['PALLETS'].sum() if not df_t3.empty else 0
        estrados_t3 = df_t3[df_t3['TIPO_FLUXO'] == "ESTRADO"]['PALLETS'].sum() if not df_t3.empty else 0
        total_t3 = carga_t3 + estrados_t3
        
        # Totais unificados por soma direta
        total_ciclos_global = ciclos_t1 + ciclos_t2 + ciclos_t3
        total_carga_global = carga_t1 + carga_t2 + carga_t3
        total_estrados_global = estrados_t1 + estrados_t2 + estrados_t3
        total_pallets_global = total_t1 + total_t2 + total_t3
        
        # Interface gráfica
        st.markdown(f"### 📋 Período: {label_mes}{label_dia}")
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Estufas Processadas (Ciclos)", f"{total_ciclos_global} Ciclos")
        m2.metric("PLTs Tratados (Carga)", f"{total_carga_global} PLT")
        m3.metric("Estrados (Produção)", f"{total_estrados_global} Unid")
        m4.metric("Movimentação Total", f"{total_pallets_global} Pallets")
        
        st.markdown("---")
        st.markdown("### ⏱️ Performance Operacional por Turno")
        
        t1, t2, t3 = st.columns(3)
        
        with t1:
            st.markdown(f"""
            <div style="background-color: #f8f9fa; border-radius: 10px; padding: 20px; border: 1px solid #e9ecef;">
                <h3 style="margin-top:0; color:#1c3d5a; border-bottom: 2px solid #dee2e6; padding-bottom: 5px;">Turno I</h3>
                <p style="margin: 8px 0; font-size:15px;"><b>Nº de Tratamentos (Ciclos):</b> <span style="float:right; font-size:16px; font-weight:bold; color:#007ebd;">{ciclos_t1}</span></p>
                <p style="margin: 8px 0; font-size:15px;"><b>PLTs Tratados (Carga):</b> <span style="float:right; font-weight:bold;">{carga_t1}</span></p>
                <p style="margin: 8px 0; font-size:15px;"><b>Estrados (Produção):</b> <span style="float:right; font-weight:bold;">{estrados_t1}</span></p>
                <hr style="margin:10px 0; border:0; border-top:1px solid #ced4da;">
                <p style="margin: 5px 0; font-size:16px; font-weight:bold;">Total de Pallets: <span style="float:right; font-size:18px; color:#2b8a3e;">{total_t1}</span></p>
            </div>
            """, unsafe_allow_html=True)

        with t2:
            st.markdown(f"""
            <div style="background-color: #f8f9fa; border-radius: 10px; padding: 20px; border: 1px solid #e9ecef;">
                <h3 style="margin-top:0; color:#1c3d5a; border-bottom: 2px solid #dee2e6; padding-bottom: 5px;">Turno II</h3>
                <p style="margin: 8px 0; font-size:15px;"><b>Nº de Tratamentos (Ciclos):</b> <span style="float:right; font-size:16px; font-weight:bold; color:#007ebd;">{ciclos_t2}</span></p>
                <p style="margin: 8px 0; font-size:15px;"><b>PLTs Tratados (Carga):</b> <span style="float:right; font-weight:bold;">{carga_t2}</span></p>
                <p style="margin: 8px 0; font-size:15px;"><b>Estrados (Produção):</b> <span style="float:right; font-weight:bold;">{estrados_t2}</span></p>
                <hr style="margin:10px 0; border:0; border-top:1px solid #ced4da;">
                <p style="margin: 5px 0; font-size:16px; font-weight:bold;">Total de Pallets: <span style="float:right; font-size:18px; color:#2b8a3e;">{total_t2}</span></p>
            </div>
            """, unsafe_allow_html=True)

        with t3:
            st.markdown(f"""
            <div style="background-color: #f8f9fa; border-radius: 10px; padding: 20px; border: 1px solid #e9ecef;">
                <h3 style="margin-top:0; color:#1c3d5a; border-bottom: 2px solid #dee2e6; padding-bottom: 5px;">Turno III</h3>
                <p style="margin: 8px 0; font-size:15px;"><b>Nº de Tratamentos (Ciclos):</b> <span style="float:right; font-size:16px; font-weight:bold; color:#007ebd;">{ciclos_t3}</span></p>
                <p style="margin: 8px 0; font-size:15px;"><b>PLTs Tratados (Carga):</b> <span style="float:right; font-weight:bold;">{carga_t3}</span></p>
                <p style="margin: 8px 0; font-size:15px;"><b>Estrados (Produção):</b> <span style="float:right; font-weight:bold;">{estrados_t3}</span></p>
                <hr style="margin:10px 0; border:0; border-top:1px solid #ced4da;">
                <p style="margin: 5px 0; font-size:16px; font-weight:bold;">Total de Pallets: <span style="float:right; font-size:18px; color:#2b8a3e;">{total_t3}</span></p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.warning("Nenhum registro encontrado para este período.")
else:
    st.error("Erro ao carregar a base de dados.")