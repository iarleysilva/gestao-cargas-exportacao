import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, time
import zoneinfo

# ─── BLOCO DE SEGURANÇA DE CAMINHOS ROBUSTO ───
import sys
from pathlib import Path
raiz = Path(__file__).resolve().parents[1]  # Sobe 1 nível
if str(raiz) not in sys.path:
    sys.path.append(str(raiz))
# ───────────────────────────────────────────────────────────────────────────────────

from src.core.data_loader import carregar_dados_separacao_mi, carregar_matriz_capacidade, carregar_execucao_turnos

st.set_page_config(page_title="Demanda MI", layout="wide")

st.title("📦 Módulo: Demanda & Fluxo de Separação — MI")
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

# ─── 2. PADRONIZAÇÃO E CONFIGURAÇÃO TÉCNICA DOS DADOS ───
df_demanda['PERCURSO'] = df_demanda['PERCURSO'].astype(str).str.strip().str.replace('.0', '', regex=False)
df_demanda['DT_PERCURSO'] = pd.to_datetime(df_demanda['DT_PERCURSO'], errors='coerce')
df_demanda['DT_SEQUENCIADO'] = pd.to_datetime(df_demanda['DT_SEQUENCIADO'], errors='coerce')

df_demanda['CXS'] = pd.to_numeric(df_demanda['CXS'], errors='coerce').fillna(0).astype(int)
df_demanda['PLS'] = pd.to_numeric(df_demanda['PLS'], errors='coerce').fillna(0).astype(int)
df_demanda['TOTAL_CALCULADO'] = df_demanda['CXS'] + df_demanda['PLS']

# Dicionário de controle de bipes físicos coletados do chão de fábrica
percursos_bipados_fabrica = set(df_execucao['PERCURSO'].dropna().unique()) if df_execucao is not None else set()

# ─── 3. RELÓGIO OPERACIONAL DE BRASÍLIA ───
fuso_br = zoneinfo.ZoneInfo("America/Sao_Paulo")
agora_br = datetime.now(fuso_br)
hoje_br = agora_br.date()
hora_atual = agora_br.time()

# ─── 4. MOTOR DO VEREDITO DO SLA OPERACIONAL COM CADEADO DO TURNO 3 ───
def classificar_fluxo_mi(row):
    status_seq = str(row['STATUS']).upper().strip()
    percurso_id = row['PERCURSO']
    bipado = percurso_id in percursos_bipados_fabrica
    
    if status_seq == "NÃO SEQUENCIADO" or pd.isna(row['DT_SEQUENCIADO']):
        if bipado:
            return "OPORTUNIDADE ⚡"
        return "SOBRA"
    
    dt_seq = row['DT_SEQUENCIADO'].date()
    turno = str(row['TURNO_ALOCADO']).strip().replace('.0', '')
    
    if dt_seq > hoje_br:
        return "Sequenciado (Vai Separar)"
        
    if dt_seq < hoje_br:
        return "ADERIDO ✅" if bipado else "SOBRA"

    # ⏱️ REGRAS DE ATIVAÇÃO DE SLA POR JANELA HORÁRIA (HOJE)
    # Turno 1 (05h00 - 13h30). Gatilho definitivo ativa às 13h45.
    if turno in ["1", "1.0"]:
        if hora_atual < time(5, 0):
            return "Sequenciado"
        elif time(5, 0) <= hora_atual < time(13, 45):
            return "Em Andamento"
        else:
            return "ADERIDO ✅" if bipado else "NÃO ADERIDO ❌"
            
    # Turno 2 (13h30 - 22h00). Gatilho definitivo ativa às 22h15.
    elif turno in ["2", "2.0"]:
        if hora_atual < time(13, 30):
            return "Sequenciado"
        elif time(13, 30) <= hora_atual < time(22, 15):
            return "Em Andamento"
        else:
            return "ADERIDO ✅" if bipado else "NÃO ADERIDO ❌"
            
    # Turno 3 (22h00 - 05h00). Cadeado operacional ajustado para acurácia de pátio.
    elif turno in ["3", "3.0"]:
        if time(22, 0) <= hora_atual or hora_atual < time(5, 15):
            return "Em Andamento"
        else:
            # 🔒 VEREDITO DEFINITIVO: Passou das 05h15 da manhã, o turno está encerrado. 
            # O dado não volta para a sobra, vira resultado de performance real do dia.
            return "ADERIDO ✅" if bipado else "TURNO FECHADO"

    return "Em Andamento"

df_demanda['SITUACAO_REAL'] = df_demanda.apply(classificar_fluxo_mi, axis=1)

# As sobras coletam apenas o que é SOBRA pura ou OPORTUNIDADE sem agendamento
df_sobras_geral = df_demanda[df_demanda['SITUACAO_REAL'].isin(["SOBRA", "OPORTUNIDADE ⚡"])].copy()
df_seq_geral = df_demanda[~df_demanda['SITUACAO_REAL'].isin(["SOBRA", "OPORTUNIDADE ⚡"])].copy()

# ─── 5. FILTROS DA SIDEBAR ───
st.sidebar.header("🗓️ Filtro MI Operação")
st.sidebar.write(f"⏰ **Hora Atual:** {agora_br.strftime('%H:%M')}")
datas_planejadas = sorted(df_seq_geral['DT_SEQUENCIADO'].dropna().unique())
if datas_planejadas:
    hoje_timestamp = pd.Timestamp(hoje_br)
    indice_padrao = datas_planejadas.index(hoje_timestamp) if hoje_timestamp in datas_planejadas else len(datas_planejadas) - 1
    data_selecionada = st.sidebar.selectbox("Selecione o Dia de Controle:", options=datas_planejadas, index=indice_padrao, format_func=lambda x: pd.to_datetime(x).strftime('%d/%m/%Y'))
    df_seq_filtrado = df_seq_geral[df_seq_geral['DT_SEQUENCIADO'] == data_selecionada]
else:
    df_seq_filtrado = df_seq_geral

# Segmentação analítica dos turnos para o dia selecionado
df_t1 = df_seq_filtrado[df_seq_filtrado['TURNO_ALOCADO'].astype(str).str.contains('1', na=False)]
df_t2 = df_seq_filtrado[df_seq_filtrado['TURNO_ALOCADO'].astype(str).str.contains('2', na=False)]
df_t3 = df_seq_filtrado[df_seq_filtrado['TURNO_ALOCADO'].astype(str).str.contains('3', na=False)]

t1_tot = int(df_t1['TOTAL_CALCULADO'].sum())
t2_tot = int(df_t2['TOTAL_CALCULADO'].sum())
t3_tot = int(df_t3['TOTAL_CALCULADO'].sum())
total_dia_seq = t1_tot + t2_tot + t3_tot

# ─── 6. LÓGICA DE EXIBIÇÃO TURNO A TURNO BASEADA NO CALENDÁRIO SELECIONADO ───
is_hoje = pd.to_datetime(data_selecionada).date() == hoje_br

st_t1, st_t2, st_t3 = "Sequenciado", "Sequenciado", "Sequenciado"
style_t1, style_t2, style_t3 = "color:#64748b;", "color:#64748b;", "color:#64748b;"

def formatar_fechamento_turno(df_turno):
    tot_planejado = int(df_turno['TOTAL_CALCULADO'].sum())
    df_bipados = df_turno[df_turno['PERCURSO'].isin(percursos_bipados_fabrica)]
    tot_aderido = int(df_bipados['TOTAL_CALCULADO'].sum())
    tot_faltou = max(0, tot_planejado - tot_aderido)
    return f"Aderiu: {tot_aderido} | Faltou: {tot_faltou}", "color:#16a34a; font-size:13px; font-weight:bold;" if tot_faltou == 0 else "color:#dc2626; font-size:13px; font-weight:bold;"

if is_hoje:
    # Cenário A: Início da manhã, antes do corte do Turno 1
    if hora_atual < time(5, 0):
        st_t1 = "Sequenciado"
    # Cenário B: Turno 1 em andamento
    elif time(5, 0) <= hora_atual < time(13, 45):
        st_t1 = "EM ANDAMENTO ⚙️"
        style_t1 = "color:#ea580c; font-size:18px; font-weight:900; background-color:#ffedd5; padding:2px 6px; border-radius:4px;"
    # Cenário C: Turno 2 em andamento
    elif time(13, 30) <= hora_atual < time(22, 15):
        st_t1, style_t1 = formatar_fechamento_turno(df_t1)
        st_t2 = "EM ANDAMENTO ⚙️"
        style_t2 = "color:#ea580c; font-size:18px; font-weight:900; background-color:#ffedd5; padding:2px 6px; border-radius:4px;"
        
        # 🔒 AJUSTE DE RECONHECIMENTO: Como o relógio já passou das 05h15 da tarde, o T3 da madrugada passada está trancado
        st_t3 = "MATE EM MADRUGADA 🔒"
        style_t3 = "color:#475569; font-size:13px; font-weight:bold; background-color:#f1f5f9; padding:2px 6px; border-radius:4px;"
    # Cenário D: Turno 3 em andamento ativo
    elif time(22, 0) <= hora_atual:
        st_t1, style_t1 = formatar_fechamento_turno(df_t1)
        st_t2, style_t2 = formatar_fechamento_turno(df_t2)
        st_t3 = "EM ANDAMENTO ⚙️"
        style_t3 = "color:#ea580c; font-size:18px; font-weight:900; background-color:#ffedd5; padding:2px 6px; border-radius:4px;"
    # Cenário E: Madrugada do dia seguinte antes do corte definitivo (00h00 - 05h15)
    elif hora_atual < time(5, 15):
        st_t1, style_t1 = formatar_fechamento_turno(df_t1)
        st_t2, style_t2 = formatar_fechamento_turno(df_t2)
        st_t3 = "EM ANDAMENTO ⚙️"
        style_t3 = "color:#ea580c; font-size:18px; font-weight:900; background-color:#ffedd5; padding:2px 6px; border-radius:4px;"
    else:
        st_t1, style_t1 = formatar_fechamento_turno(df_t1)
        st_t2, style_t2 = formatar_fechamento_turno(df_t2)
        st_t3, style_t3 = formatar_fechamento_turno(df_t3)
else:
    st_t1, style_t1 = formatar_fechamento_turno(df_t1)
    st_t2, style_t2 = formatar_fechamento_turno(df_t2)
    st_t3, style_t3 = formatar_fechamento_turno(df_t3)

tab_seq, tab_sobras = st.tabs(["✅ Demandas Sequenciadas MI", "⚠️ Carteira Geral de Sobras (Visão Gerencial)"])

# ─── 📂 ABA 1: DEMANDAS SEQUENCIADAS MI ───
with tab_seq:
    st.markdown("#### ⏱️ Absorvido por Turno (Acessos Pendentes Sequenciados e Em Andamento)")
    col_t1, col_t2, col_t3, col_tot = st.columns(4)
    with col_t1:
        st.markdown(f'<div style="background-color:#f9fafb; border-left:5px solid #007ebd; padding:15px; border-radius:6px; border-right:1px solid #e5e7eb; border-top:1px solid #e5e7eb; border-bottom:1px solid #e5e7eb;"><b>TURNO 1 (05h00 - 13h30)</b><br><span style="{style_t1}">{st_t1}</span><br><h2 style="margin:5px 0 0 0;">{t1_tot} <span style="font-size:12px; color:#6b7280; font-weight:normal;">Acessos</span></h2></div>', unsafe_allow_html=True)
    with col_t2:
        st.markdown(f'<div style="background-color:#f9fafb; border-left:5px solid #007ebd; padding:15px; border-radius:6px; border-right:1px solid #e5e7eb; border-top:1px solid #e5e7eb; border-bottom:1px solid #e5e7eb;"><b>TURNO 2 (13h30 - 22h00)</b><br><span style="{style_t2}">{st_t2}</span><br><h2 style="margin:5px 0 0 0;">{t2_tot} <span style="font-size:12px; color:#6b7280; font-weight:normal;">Acessos</span></h2></div>', unsafe_allow_html=True)
    with col_t3:
        st.markdown(f'<div style="background-color:#f9fafb; border-left:5px solid #007ebd; padding:15px; border-radius:6px; border-right:1px solid #e5e7eb; border-top:1px solid #e5e7eb; border-bottom:1px solid #e5e7eb;"><b>TURNO 3 (22h00 - 05h00)</b><br><span style="{style_t3}">{st_t3}</span><br><h2 style="margin:5px 0 0 0;">{t3_tot} <span style="font-size:12px; color:#6b7280; font-weight:normal;">Acessos</span></h2></div>', unsafe_allow_html=True)
    with col_tot:
        st.markdown(f'<div style="background-color:#ecfdf5; border-left:5px solid #10b981; padding:15px; border-radius:6px; border-right:1px solid #a7f3d0; border-top:1px solid #a7f3d0; border-bottom:1px solid #a7f3d0;"><b>📊 DEMANDA TOTAL DO DIA</b><br><span style="color:#10b981; font-weight:bold; font-size:13px;">Agendamento Firme</span><br><h2 style="margin:5px 0 0 0; color:#047857;">{total_dia_seq} <span style="font-size:12px; color:#047857; font-weight:normal;">Acessos Totais</span></h2></div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    data_titulo_seq = pd.to_datetime(data_selecionada).strftime('%d/%m/%Y') if datas_planejadas else ""
    st.markdown(f"### 📋 Detalhamento Técnico do Agendamento ({data_titulo_seq})")
    
    if not df_seq_filtrado.empty:
        df_dinamica_seq = df_seq_filtrado.groupby(['TURNO_ALOCADO', 'CANAL']).agg(
            Soma_de_CXS=('CXS', 'sum'),
            Soma_de_PLS=('PLS', 'sum'),
            Total_Calculado=('TOTAL_CALCULADO', 'sum'),
            Qtd_Percursos=('PERCURSO', 'count')
        ).reset_index().rename(columns={'TURNO_ALOCADO': 'Turno', 'CANAL': 'Canal Comercial'})
        
        linha_total_seq = pd.DataFrame([{
            'Turno': 'TOTAL', 'Canal Comercial': 'GERAL DIA',
            'Soma_de_CXS': df_dinamica_seq['Soma_de_CXS'].sum(),
            'Soma_de_PLS': df_dinamica_seq['Soma_de_PLS'].sum(),
            'Total_Calculado': df_dinamica_seq['Total_Calculado'].sum(),
            'Qtd_Percursos': df_dinamica_seq['Qtd_Percursos'].sum()
        }])
        df_dinamica_seq = pd.concat([df_dinamica_seq, linha_total_seq], ignore_index=True)
        
        st.dataframe(df_dinamica_seq.rename(columns={
            'Soma_de_CXS': 'Soma de CXS', 'Soma_de_PLS': 'Soma de PLS', 'Total_Calculado': 'Total (Calculado)', 'Qtd_Percursos': 'Qtd Rotas'
        }), use_container_width=True, hide_index=True)
        
        st.markdown("### 📋 Inspeção de Roteiros Individuais e Veredito de SLA")
        df_seq_render = df_seq_filtrado.copy()
        df_seq_render['DT_PERCURSO'] = df_seq_render['DT_PERCURSO'].dt.strftime('%d/%m/%Y')
        
        cols_exibir = ['PERCURSO', 'CANAL', 'CXS', 'PLS', 'TOTAL_CALCULADO', 'DT_PERCURSO', 'TURNO_ALOCADO', 'SITUACAO_REAL']
        st.dataframe(
            df_seq_render[cols_exibir].rename(columns={
                'CANAL': 'Canal', 'TOTAL_CALCULADO': 'Total (Calculado)', 'DT_PERCURSO': 'Data Origem', 'TURNO_ALOCADO': 'Turno Alocado', 'SITUACAO_REAL': 'Status Operação / SLA'
            }), use_container_width=True, hide_index=True
        )
    else:
        st.info("Nenhum percurso sequenciado de MI encontrado para a data selecionada.")

# ─── 📂 ABA 2: CARTEIRA GERAL DE SOBRAS ───
with tab_sobras:
    s_cxs = int(df_sobras_geral['CXS'].sum()) if not df_sobras_geral.empty else 0
    s_pls = int(df_sobras_geral['PLS'].sum()) if not df_sobras_geral.empty else 0
    s_tot = s_cxs + s_pls
    
    st.markdown(f"### 🔎 Sobras da Carteira (Acessos Pendentes Brutos: {s_tot} un)")
    
    sc1, sc2, sc3 = st.columns(3)
    with sc1:
        st.markdown(f'<div style="background-color:#f9fafb; border-left:5px solid #ef4444; padding:15px; border-radius:6px; border-right:1px solid #e5e7eb; border-top:1px solid #e5e7eb; border-bottom:1px solid #e5e7eb;"><b>CXS</b><br><h2 style="margin:5px 0 0 0;">{s_cxs}</h2><span style="font-size:12px; color:#6b7280;">cxs não seq.</span></div>', unsafe_allow_html=True)
    with sc2:
        st.markdown(f'<div style="background-color:#f9fafb; border-left:5px solid #ef4444; padding:15px; border-radius:6px; border-right:1px solid #e5e7eb; border-top:1px solid #e5e7eb; border-bottom:1px solid #e5e7eb;"><b>PLS</b><br><h2 style="margin:5px 0 0 0;">{s_pls}</h2><span style="font-size:12px; color:#6b7280;">pls não seq.</span></div>', unsafe_allow_html=True)
    with sc3:
        st.markdown(f'<div style="background-color:#fef2f2; border-left:5px solid #b91c1c; padding:15px; border-radius:6px; border-right:1px solid #fca5a5; border-top:1px solid #fca5a5; border-bottom:1px solid #fca5a5;"><b>TOTAL</b><br><h2 style="margin:5px 0 0 0;">{s_tot}</h2><span style="font-size:12px; color:#b91c1c;">total não seq.</span></div>', unsafe_allow_html=True)
    
    st.markdown("<br>#### 📊 Tabela Dinâmica Consolidada por Data de Percurso e Canal", unsafe_allow_html=True)
    
    if not df_sobras_geral.empty:
        df_sobras_processamento = df_sobras_geral.copy()
        df_sobras_processamento['DT_PERCURSO_NORMALIZADA'] = pd.to_datetime(df_sobras_processamento['DT_PERCURSO'], errors='coerce')
        
        df_dinamica_sobras = df_sobras_processamento.groupby([df_sobras_processamento['DT_PERCURSO_NORMALIZADA'].dt.strftime('%d/%m/%Y'), 'CANAL']).agg(
            Soma_CXS=('CXS', 'sum'),
            Soma_PLS=('PLS', 'sum'),
            Total_Calculado=('TOTAL_CALCULADO', 'sum'),
            Qtd_Rotas=('PERCURSO', 'count')
        ).rename_axis(['Data Percurso', 'Canal Comercial'])
        
        total_sobras_linha = pd.DataFrame([{
            'Soma_CXS': df_dinamica_sobras['Soma_CXS'].sum(),
            'Soma_PLS': df_dinamica_sobras['Soma_PLS'].sum(),
            'Total_Calculado': df_dinamica_sobras['Total_Calculado'].sum(),
            'Qtd_Rotas': df_dinamica_sobras['Qtd_Rotas'].sum()
        }], index=pd.MultiIndex.from_tuples([('TOTAL GERAL', '')], names=['Data Percurso', 'Canal Comercial']))
        df_dinamica_sobras = pd.concat([df_dinamica_sobras, total_sobras_linha])
        
        st.dataframe(df_dinamica_sobras.rename(columns={
            'Soma_CXS': 'Soma de CXS', 'Soma_PLS': 'Soma de PLS', 'Total_Calculado': 'Total (Calculado)', 'Qtd_Rotas': 'Qtd Rotas'
        }), use_container_width=True)
        
        with st.expander("🔍 Expandir Inspeção Analítica a Nível de Percursos (Linha por Linha)", expanded=False):
            df_sobras_processamento['Data_Origem'] = df_sobras_processamento['DT_PERCURSO_NORMALIZADA'].dt.strftime('%d/%m/%Y')
            st.dataframe(
                df_sobras_processamento[['PERCURSO', 'CANAL', 'CXS', 'PLS', 'TOTAL_CALCULADO', 'Data_Origem']].rename(columns={
                    'PERCURSO': 'Roteiro / Percurso', 'CANAL': 'Canal', 'TOTAL_CALCULADO': 'Total (Calculado)', 'Data_Origem': 'Data Origem Percurso'
                }), use_container_width=True, hide_index=True
            )
    else:
        st.success("✨ Excelente! Nenhuma sobra de Mercado Interno na carteira.")