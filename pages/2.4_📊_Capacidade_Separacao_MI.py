import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, time
import zoneinfo



# ─── BLOCO DE SEGURANÇA DE CAMINHOS ROBUSTO ───
import sys
from pathlib import Path
raiz = Path(__file__).resolve().parents[1]  # Sobe 1 nível (pages/ -> raiz do projeto)
if str(raiz) not in sys.path:
    sys.path.append(str(raiz))
# ───────────────────────────────────────────────────────────────────────────────────

from src.core.data_loader import carregar_dados_separacao_mi, carregar_matriz_capacidade

st.set_page_config(page_title="Capacidade MI", layout="wide")

st.title("📈 Módulo: Acompanhamento de Capacidade Operacional — MI")
st.markdown("---")

# ─── 1. CARREGAMENTO DOS DADOS ORIGINAIS ───
retorno_demanda = carregar_dados_separacao_mi()
df_matriz, mapa_metricas = carregar_matriz_capacidade()

if isinstance(retorno_demanda, tuple):
    df_demanda = retorno_demanda[0]
else:
    df_demanda = retorno_demanda

if df_demanda is None or df_demanda.empty:
    st.error("⚠️ Erro ao carregar os dados de demandas MI.")
    st.stop()

# Configuração de Relógio Operacional e Normalizações
fuso_br = zoneinfo.ZoneInfo("America/Sao_Paulo")
agora_br = datetime.now(fuso_br)
hoje_br = agora_br.date()
ontem_br = hoje_br - timedelta(days=1)

FERIADOS_NACIONAIS = ["01/01", "21/04", "01/05", "07/09", "12/10", "02/11", "15/11", "25/12"]

df_demanda['PERCURSO'] = df_demanda['PERCURSO'].astype(str).str.strip().str.replace('.0', '', regex=False)
df_demanda['DT_PERCURSO_DATE'] = pd.to_datetime(df_demanda['DT_PERCURSO'], errors='coerce').dt.date
df_demanda['DT_SEQUENCIADO_DATE'] = pd.to_datetime(df_demanda['DT_SEQUENCIADO'], errors='coerce').dt.date

df_demanda['CXS'] = pd.to_numeric(df_demanda['CXS'], errors='coerce').fillna(0).astype(int)
df_demanda['PLS'] = pd.to_numeric(df_demanda['PLS'], errors='coerce').fillna(0).astype(int)
df_demanda['TOTAL_CALCULADO'] = df_demanda['CXS'] + df_demanda['PLS']

# Segregação das Realidades do Pátio
df_sobras_carteira = df_demanda[df_demanda['STATUS'] == "NÃO SEQUENCIADO"].copy()
df_seq_oficial = df_demanda[df_demanda['STATUS'] == "SEQUENCIADO"].copy()

# ─── 2. LINHA DO TEMPO DINÂMICA (ONTEM + HOJE + ATÉ O ÚLTIMO ACESSO + 2 DIAS DE SEGURANÇA) ───
ultima_data_sobra = hoje_br
if not df_sobras_carteira.empty:
    data_max_detectada = df_sobras_carteira['DT_PERCURSO_DATE'].max()
    if pd.notna(data_max_detectada) and data_max_detectada > ultima_data_sobra:
        ultima_data_sobra = data_max_detectada

# A esteira avança até cobrir o último percurso e ganha mais 2 dias úteis de folga visual
data_limite_esteira = ultima_data_sobra + timedelta(days=2)

lista_dias_simulacao = []
data_corrente = ontem_br  # Inicia estritamente no dia de ontem para o retrovisor

while data_corrente <= data_limite_esteira:
    if data_corrente.weekday() == 6:  # Pula Domingo
        data_corrente += timedelta(days=1)
        continue
    if data_corrente.strftime("%d/%m") in FERIADOS_NACIONAIS:  # Pula Feriado
        data_corrente += timedelta(days=1)
        continue
    lista_dias_simulacao.append(data_corrente)
    data_corrente += timedelta(days=1)

# ─── 3. CALCULO DA MATRIZ DE CAPACIDADES DA ESTEIRA DISPONÍVEL ───
capacidades_janelas = []
for dt in lista_dias_simulacao:
    dia_sem = dt.weekday()
    is_sabado = (dia_sem == 5)
    is_segunda = (dia_sem == 0)
    
    for t_int in [1, 2, 3]:
        qtd_operadores_base = float(mapa_metricas.get(("MI", str(float(t_int)), "OPERADORES", "QTD"), 4))
        cap_por_operador = float(mapa_metricas.get(("MI", str(float(t_int)), "CAPACIDADEPOR_OPERADOR", "85"), 85))
        
        if is_sabado and t_int in [1, 2]:
            qtd_operadores_real = qtd_operadores_base * 0.50
        elif is_segunda and t_int == 3:
            qtd_operadores_real = qtd_operadores_base * 0.50
        else:
            qtd_operadores_real = qtd_operadores_base
            
        cap_nominal = int(qtd_operadores_real * cap_por_operador)
        
        # Desconta o real oficial já agendado pelo PCP
        df_ja_ocupado = df_seq_oficial[
            (df_seq_oficial['DT_SEQUENCIADO_DATE'] == dt) & 
            (df_seq_oficial['TURNO_ALOCADO'].isin([str(float(t_int)), f"{t_int}"]))
        ]
        volume_ocupado = df_ja_ocupado['TOTAL_CALCULADO'].sum()
        
        turno_fechado = not df_ja_ocupado.empty
        vagas_livres = max(0, cap_nominal - volume_ocupado) if not turno_fechado else 0
        
        percursos_janela = []
        if turno_fechado:
            for _, r_real in df_ja_ocupado.iterrows():
                percursos_janela.append({
                    "Percurso": r_real['PERCURSO'], "CXS": int(r_real['CXS']), "PLS": int(r_real['PLS']),
                    "Total (Calculado)": int(r_real['TOTAL_CALCULADO']), "Data_Original": r_real['DT_PERCURSO_DATE'],
                    "Canal": r_real['CANAL'], "Tipo": "REAL"
                })
        
        capacidades_janelas.append({
            "Data": dt,
            "Turno": t_int,
            "Capacidade_Nominal": cap_nominal,
            "Vagas_Livres": vagas_livres,
            "Simulado_Alocado": volume_ocupado,
            "Turno_Fechado": turno_fechado,
            "Percursos": percursos_janela
        })

# ─── 4. MOTOR DE DISTRIBUIÇÃO PREDITIVA DAS SOBRAS ───
if not df_sobras_carteira.empty:
    df_fila_sobras = df_sobras_carteira.sort_values(by=['DT_PERCURSO_DATE', 'CXS', 'TOTAL_CALCULADO'], ascending=[True, False, False])

    for _, row_sobra in df_fila_sobras.iterrows():
        volume_carga = int(row_sobra['TOTAL_CALCULADO'])
        percurso_id = row_sobra['PERCURSO']
        data_original_carga = row_sobra['DT_PERCURSO_DATE']
        canal_carga = row_sobra['CANAL']
        cxs_carga = int(row_sobra['CXS'])
        pls_carga = int(row_sobra['PLS'])
        
        alocado = False
        
        # Filtra apenas as janelas a partir de hoje para alocar a sobra (não mexe em ontem)
        janelas_disponiveis = [j for j in capacidades_janelas if j['Data'] >= hoje_br]
        
        # Encaixe preferencial no Turno 3 para cargas fracionadas de caixas altas
        for janela in janelas_disponiveis:
            if not janela['Turno_Fechado'] and janela['Turno'] == 3 and cxs_carga > 50 and janela['Vagas_Livres'] >= volume_carga:
                janela['Vagas_Livres'] -= volume_carga
                janela['Simulado_Alocado'] += volume_carga
                janela['Percursos'].append({
                    "Percurso": percurso_id, "CXS": cxs_carga, "PLS": pls_carga,
                    "Total (Calculado)": volume_carga, "Data_Original": data_original_carga, "Canal": canal_carga, "Tipo": "SUGERIDO"
                })
                alocado = True
                break
        
        # Escoamento padrão nos turnos vagos de hoje para a frente
        if not alocado:
            for janela in janelas_disponiveis:
                if janela['Turno_Fechado']:
                    continue
                if janela['Turno'] == 2 and janela['Vagas_Livres'] >= volume_carga:
                    tem_vaga_alternativa = any(
                        j for j in janelas_disponiveis 
                        if j['Data'] == janela['Data'] and j['Turno'] == 3 and not j['Turno_Fechado'] and j['Vagas_Livres'] >= volume_carga
                    )
                    if tem_vaga_alternativa:
                        continue
                
                if JANELA_VAGA := (janela['Vagas_Livres'] >= volume_carga):
                    janela['Vagas_Livres'] -= volume_carga
                    janela['Simulado_Alocado'] += volume_carga
                    janela['Percursos'].append({
                        "Percurso": percurso_id, "CXS": cxs_carga, "PLS": pls_carga,
                        "Total (Calculado)": volume_carga, "Data_Original": data_original_carga, "Canal": canal_carga, "Tipo": "SUGERIDO"
                    })
                    alocado = True
                    break

# ─── 5. INTERFACE ARQUITETÔNICA DO SISTEMA ───
tab_painel, tab_config = st.tabs(["📋 Acompanhamento Contínuo da Esteira", "🔐 Configurações Técnicas (PCO)"])

with tab_painel:
    # Renderização sequencial empilhada na tela, sem abas de navegação de dias
    for dt in lista_dias_simulacao:
        if dt == ontem_br:
            header_linha = f"🕒 Retrovisor Operacional — Histórico de Ontem ({dt.strftime('%d/%m/%Y')})"
            cor_sub = "#475569"
        elif dt == hoje_br:
            header_linha = f"⚙️ Jornada Ativa — Capacidade de Hoje ({dt.strftime('%d/%m/%Y')})"
            cor_sub = "#1e3a8a"
        else:
            header_linha = f"🔮 Projeção Avançada — Janela Futura ({dt.strftime('%d/%m/%Y')})"
            cor_sub = "#0f766e"
            
        st.markdown(f"<h4 style='color: {cor_sub}; margin-top:20px;'>{header_linha}</h4>", unsafe_allow_html=True)
        
        janelas_do_dia = [j for j in capacidades_janelas if j['Data'] == dt]
        col1, col2, col3 = st.columns(3)
        blocos_colunas = [col1, col2, col3]
        
        for idx_j, jan in enumerate(janelas_do_dia):
            with blocos_colunas[idx_j]:
                total_acessos_turno = jan['Simulado_Alocado']
                total_capacidade = jan['Capacidade_Nominal']
                ratio_simulado = (total_acessos_turno / total_capacidade) * 100 if total_capacidade > 0 else 0.0
                
                if jan['Turno_Fechado']:
                    cor_box, texto_status = "#eff6ff", "🔒 Fechado / Confirmado PCP"
                elif ratio_simulado > 100:
                    cor_box, texto_status = "#fef2f2", "🚨 Turno Estourado"
                elif ratio_simulado >= 90:
                    cor_box, texto_status = "#fffbeb", "⚠️ Turno Limite"
                elif 0 < ratio_simulado < 90:
                    cor_box, texto_status = "#ecfdf5", "🟢 Ocupação Otimizada"
                else:
                    cor_box, texto_status = "#f8fafc", "✨ Vagas Totalmente Livres"
                    
                st.markdown(f"""
                <div style="background-color: {cor_box}; border: 1px solid #cbd5e1; border-radius: 6px; padding: 12px; margin-bottom: 5px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-weight: 700; font-size: 1rem; color: #1e293b;">⚡ Turno {jan['Turno']}</span>
                        <span style="font-weight: bold; font-size: 0.8rem; color: #334155;">{texto_status}</span>
                    </div>
                    <div style="margin-top: 6px; font-size: 0.85rem; color: #334155;">
                        📊 <b>Volume:</b> {total_acessos_turno} / {total_capacidade} Acessos | 📈 <b>Ratio:</b> {ratio_simulado:.1f}%
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                if jan['Percursos']:
                    df_sugestao_turno = pd.DataFrame(jan['Percursos'])
                    df_resumo_canal = df_sugestao_turno.groupby('Canal').agg(
                        Soma_de_CXS=('CXS', 'sum'), Soma_de_PLS=('PLS', 'sum'),
                        Total_Calculado=('Total (Calculado)', 'sum'), Qtd_Rotas=('Percurso', 'count')
                    ).reset_index()
                    
                    st.dataframe(df_resumo_canal.rename(columns={
                        'Soma_de_CXS': 'Soma de CXS', 'Soma_de_PLS': 'Soma de PLS', 
                        'Total_Calculado': 'Total (Calculado)', 'Qtd_Rotas': 'Qtd Rotas'
                    }), use_container_width=True, hide_index=True)
                else:
                    st.caption("Sem cargas alocadas para esta janela.")
        st.markdown("---")

with tab_config:
    st.subheader("🔐 Área Restrita de Calibração Técnica")
    senha = st.text_input("Insira a senha do PCO para liberar as configurações de engenharia:", type="password")
    
    if senha == "pco123":
        st.success("✅ Acesso Liberado! Modo Desenvolvedor Ativo.")
        
        todos_percursos_simulados = []
        for jan in capacidades_janelas:
            for p in jan['Percursos']:
                p_copy = p.copy()
                p_copy['Data_Janela'] = jan['Data']
                p_copy['Turno_Janela'] = jan['Turno']
                todos_percursos_simulados.append(p_copy)
                
        if todos_percursos_simulados:
            df_analitico_dev = pd.DataFrame(todos_percursos_simulados)
            st.dataframe(df_analitico_dev[[
                'Data_Janela', 'Turno_Janela', 'Percurso', 'Canal', 'CXS', 'PLS', 'Total (Calculado)', 'Tipo'
            ]].rename(columns={
                'Data_Janela': 'Data Alocada', 'Turno_Janela': 'Turno Alocado', 'Tipo': 'Origem do Dado'
            }), use_container_width=True, hide_index=True)