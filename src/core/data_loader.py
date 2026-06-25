import pandas as pd
import streamlit as st
import time

# ==============================================================================
# 🎯 MATRIZ DE CONEXÕES OFICIAIS (HOMOLOGADA - PCO PREMIUM 2026)
# ==============================================================================

# 1. Planilha: Demanda HT diária
URL_HT_BASE      = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQUBeTkC4k0uKXOijcXRa1TJHPVW3QYKSieUVpLKDUq9oFYUa2Jtfq8BWEURZ9eoYWoPGppTtmIxI2c/pub?gid=1836411567&single=true&output=csv"
URL_HT_ATT       = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQUBeTkC4k0uKXOijcXRa1TJHPVW3QYKSieUVpLKDUq9oFYUa2Jtfq8BWEURZ9eoYWoPGppTtmIxI2c/pub?gid=1318835351&single=true&output=csv"
URL_HT_REALIZADO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQUBeTkC4k0uKXOijcXRa1TJHPVW3QYKSieUVpLKDUq9oFYUa2Jtfq8BWEURZ9eoYWoPGppTtmIxI2c/pub?gid=1740948393&single=true&output=csv"

# 2. Planilha: Sequenciamento_previsão carregamento
URL_UNIFICADA_MI_ME = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSqUnWPArdoAcBGkShJALYLN7SzmXeKbus_mzDiT9iP3B3iHEEfRdm1LEVSKEllLLnjgcgX8Lajn7k-/pub?gid=952730620&single=true&output=csv"
URL_LASTRAS_NOVAS   = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSqUnWPArdoAcBGkShJALYLN7SzmXeKbus_mzDiT9iP3B3iHEEfRdm1LEVSKEllLLnjgcgX8Lajn7k-/pub?gid=1567949357&single=true&output=csv"

# 3. Planilha: PRODUTIVIDADE TURNO POR ACESSO MI e ME
URL_BIPES_TURNOS = {
    "TURNO 1": "https://docs.google.com/spreadsheets/d/e/2PACX-1vTS8d44ajH4_Hm7uaAWVbejIzmbMqK8fCbYEPYWddDc4pnbFBhyOye4vs6QmtJ-a51V-b9HDTFPDcSw/pub?gid=0&single=true&output=csv",
    "TURNO 2": "https://docs.google.com/spreadsheets/d/e/2PACX-1vTS8d44ajH4_Hm7uaAWVbejIzmbMqK8fCbYEPYWddDc4pnbFBhyOye4vs6QmtJ-a51V-b9HDTFPDcSw/pub?gid=1250180014&single=true&output=csv",
    "TURNO 3": "https://docs.google.com/spreadsheets/d/e/2PACX-1vTS8d44ajH4_Hm7uaAWVbejIzmbMqK8fCbYEPYWddDc4pnbFBhyOye4vs6QmtJ-a51V-b9HDTFPDcSw/pub?gid=1415290687&single=true&output=csv"
}

# 🔒 Cache independente para Demanda HT (Validade: 5 minutos)
@st.cache_data(show_spinner="⏳ Sincronizando Módulo Demanda HT...")
def carregar_e_tratar_dados():
    """ [MÓDULO: DEMANDA HT] """
    try:
        df_att = pd.read_csv(URL_HT_ATT, header=None)
        data_atualizacao = str(df_att.iloc[1, 0]).strip() if len(df_att) > 1 else "Não informada"
    except Exception:
        data_atualizacao = "Erro na leitura"

    try:
        df = pd.read_csv(URL_HT_BASE)
        if df.empty: return None, data_atualizacao
        
        df.columns = df.columns.str.strip()
        df_real = pd.DataFrame()
        
        df_real['Tipo'] = df['Tipo'] if 'Tipo' in df.columns else "Carga"
        df_real['Status'] = df.iloc[:, 1]
        df_real['Fatura'] = df.iloc[:, 8]
        df_real['Percurso'] = df.iloc[:, 9]
        df_real['Total_Plt_Percurso'] = df.iloc[:, 15] 
        df_real['Data_Carregamento'] = df.iloc[:, 16]
        df_real['Modal'] = df.iloc[:, 17]
        
        df_real = df_real.dropna(subset=['Fatura', 'Percurso'], how='all')
        df_real['Data_Carregamento'] = pd.to_datetime(df_real['Data_Carregamento'], errors='coerce')
        return df_real.dropna(subset=['Data_Carregamento']), data_atualizacao
    except Exception:
        return None, "Erro"


# 🔒 Cache independente para Mercado Externo (Validade: 5 minutos)
@st.cache_data(show_spinner="⏳ Sincronizando Módulo Mercado Externo (ME)...")
def carregar_dados_separacao():
    """ [MÓDULO: MERCADO EXTERNO (ME)] """
    try:
        df_att = pd.read_csv(URL_HT_ATT, header=None)
        dt_a3_str = str(df_att.iloc[2, 0]).strip() if len(df_att) > 2 else "Não informada"
        data_corte_separacao = pd.to_datetime(dt_a3_str.split()[0], dayfirst=True, errors='coerce')
    except Exception:
        data_corte_separacao = pd.to_datetime(pd.Timestamp.now().date())
        dt_a3_str = "Usando data do sistema"

    df = None
    for tentativa in range(3):
        try:
            df = pd.read_csv(URL_UNIFICADA_MI_ME)
            break
        except Exception as e:
            if tentativa < 2:
                time.sleep(1)
                continue
            else:
                st.error(f"🚨 ERRO DE CONEXÃO GOOGLE (Tentativas Esgotadas ME): {e}")
                return None, data_corte_separacao, dt_a3_str

    try:
        df.columns = [str(c).strip() for c in df.columns]
        
        if 'CANAL' in df.columns:
            df = df[df['CANAL'].astype(str).str.strip() == 'Direct Sale']
        else:
            if 'MERCADO' in df.columns:
                df = df[df['MERCADO'].astype(str).str.strip().str.upper() == 'ME']
            else:
                return pd.DataFrame(columns=['PERCURSO', 'STATUS', 'VOLUME_TOTAL', 'TURNO_ALOCADO']), data_corte_separacao, dt_a3_str

        df_real = pd.DataFrame()
        if 'PERCURSO' in df.columns:
            df_real['PERCURSO'] = df['PERCURSO'].astype(str).str.strip().str.replace('.0', '', regex=False)
        else:
            st.error("🚨 ERRO CRÍTICO: Coluna 'PERCURSO' não encontrada.")
            return None, data_corte_separacao, dt_a3_str

        if 'STATUS' in df.columns:
            df_real['STATUS'] = df['STATUS'].astype(str).str.strip().str.upper()
        
        if 'Data 1º Firme' in df.columns:
            df_real['DT_1_FIRME'] = pd.to_datetime(df['Data 1º Firme'], dayfirst=True, errors='coerce')
        else:
            df_real['DT_1_FIRME'] = pd.to_datetime(df.iloc[:, 2], dayfirst=True, errors='coerce')
            
        df_real['DT_PERCURSO'] = pd.to_datetime(df['DT PERCURSO'], dayfirst=True, errors='coerce') if 'DT PERCURSO' in df.columns else df_real['DT_1_FIRME']
        df_real['DT_SEQUENCIADO'] = pd.to_datetime(df['DATA SEQUENCIADO'], dayfirst=True, errors='coerce') if 'DATA SEQUENCIADO' in df.columns else df_real['DT_1_FIRME']
        
        cxs = pd.to_numeric(df['CXS'], errors='coerce').fillna(0)
        pls = pd.to_numeric(df['PLS'], errors='coerce').fillna(0)
        df_real['VOLUME_TOTAL'] = (cxs + pls).astype(int)
        
        if 'TURNO_REAL' in df.columns:
            df_real['TURNO_ALOCADO'] = pd.to_numeric(df['TURNO_REAL'], errors='coerce').fillna(1.0).astype(str).str.strip()
            df_real['TURNO_ALOCADO'] = df_real['TURNO_ALOCADO'].apply(lambda x: f"{float(x):.1f}" if x != 'nan' and x != '' else "1.0")
        else:
            df_real['TURNO_ALOCADO'] = "1.0"
        
        df_real = df_real.dropna(subset=['PERCURSO'])
        return df_real.drop_duplicates(subset=['PERCURSO'], keep='first'), data_corte_separacao, dt_a3_str
    except Exception as e:
        st.error(f"Erro no mapeamento STATUS (ME): {e}")
        return None, pd.to_datetime(pd.Timestamp.now().date()), "Erro"


# 🔒 Cache independente para Mercado Interno (Validade: 5 minutos)
@st.cache_data(show_spinner="⏳ Sincronizando Módulo Mercado Interno (MI)...")
def carregar_dados_separacao_mi():
    """ [MÓDULO: MERCADO INTERNO (MI)] """
    try:
        df_att = pd.read_csv(URL_HT_ATT, header=None)
        dt_a3_str = str(df_att.iloc[2, 0]).strip() if len(df_att) > 2 else "Não informada"
        data_corte_separacao = pd.to_datetime(dt_a3_str.split()[0], dayfirst=True, errors='coerce')
    except Exception:
        data_corte_separacao = pd.to_datetime(pd.Timestamp.now().date())
        dt_a3_str = "Usando data do sistema"

    df = None
    for tentativa in range(3):
        try:
            df = pd.read_csv(URL_UNIFICADA_MI_ME)
            break
        except Exception as e:
            if tentativa < 2:
                time.sleep(1)
                continue
            else:
                st.error(f"🚨 ERRO DE CONEXÃO GOOGLE (Tentativas Esgotadas MI): {e}")
                return None, data_corte_separacao, dt_a3_str

    try:
        df.columns = [str(c).strip() for c in df.columns]
        
        if 'CANAL' in df.columns:
            df = df[df['CANAL'].astype(str).str.strip() != 'Direct Sale']

        df_real = pd.DataFrame()
        df_real['PERCURSO'] = df['PERCURSO'].astype(str).str.strip().str.replace('.0', '', regex=False)
        df_real['STATUS'] = df['STATUS'].astype(str).str.strip().str.upper()
        df_real['CANAL'] = df['CANAL'].astype(str).str.strip() if 'CANAL' in df.columns else "Não Informado"
        
        df_real['DT_1_FIRME'] = pd.to_datetime(df['Data 1º Firme'], dayfirst=True, errors='coerce') if 'Data 1º Firme' in df.columns else pd.to_datetime(df.iloc[:, 2], dayfirst=True, errors='coerce')
        df_real['DT_PERCURSO'] = pd.to_datetime(df['DT PERCURSO'], dayfirst=True, errors='coerce') if 'DT PERCURSO' in df.columns else df_real['DT_1_FIRME']
        df_real['DT_SEQUENCIADO'] = pd.to_datetime(df['DATA SEQUENCIADO'], dayfirst=True, errors='coerce') if 'DATA SEQUENCIADO' in df.columns else df_real['DT_1_FIRME']
        
        df_real['CXS'] = pd.to_numeric(df['CXS'], errors='coerce').fillna(0).astype(int)
        df_real['PLS'] = pd.to_numeric(df['PLS'], errors='coerce').fillna(0).astype(int)
        df_real['VOLUME_TOTAL'] = df_real['CXS'] + df_real['PLS']
        
        if 'TURNO_REAL' in df.columns:
            df_real['TURNO_ALOCADO'] = pd.to_numeric(df['TURNO_REAL'], errors='coerce').fillna(1.0).astype(str).str.strip()
            df_real['TURNO_ALOCADO'] = df_real['TURNO_ALOCADO'].apply(lambda x: f"{float(x):.1f}" if x != 'nan' and x != '' else "1.0")
        else:
            df_real['TURNO_ALOCADO'] = "1.0"
        
        df_real = df_real.dropna(subset=['PERCURSO'])
        return df_real.drop_duplicates(subset=['PERCURSO'], keep='first'), data_corte_separacao, dt_a3_str
    except Exception as e:
        st.error(f"Erro no mapeamento STATUS (MI): {e}")
        return None, pd.to_datetime(pd.Timestamp.now().date()), "Erro"


# 🔒 Cache independente para Execução de Turnos (Validade: 5 minutos)
@st.cache_data(show_spinner="⏳ Atualizando Produtividade dos Turnos...")
def carregar_execucao_turnos():
    """ [MÓDULO: BIPES DOS TURNOS] """
    df_consolidado = []
    for turno, url in URL_BIPES_TURNOS.items():
        try:
            df = pd.read_csv(url)
            if not df.empty:
                df.columns = [str(c).strip().upper() for c in df.columns]
                col_percurso = next((cHeader for cHeader in df.columns if "PERCURSO" in cHeader), None)
                
                if col_percurso:
                    df_turno = pd.DataFrame()
                    df_turno['PERCURSO'] = df[col_percurso].astype(str).str.strip().str.replace('.0', '', regex=False)
                    df_turno['TURNO_REALIZOU'] = turno
                    df_consolidado.append(df_turno)
        except Exception:
            continue
            
    if df_consolidado:
        return pd.concat(df_consolidado, ignore_index=True).drop_duplicates()
    return pd.DataFrame(columns=['PERCURSO', 'TURNO_REALIZOU'])


# 🔒 Cache independente para Realizado HT (Validade: 5 minutos)
@st.cache_data(show_spinner="⏳ Puxando Histórico Realizado HT...")
def carregar_realizado_ht(ano_selecionado="2026"):
    """ [MÓDULO: REALIZADO HT - CORRIGIDO] """
    try:
        df = pd.read_csv(URL_HT_REALIZADO, dtype=str)
        if df.empty: return None
        
        df.columns = df.columns.str.strip()
        df_realizado = pd.DataFrame()
        df_realizado['CONCAT'] = df['CONCAT'].fillna('').astype(str).str.strip()
        df_realizado['TURNO'] = df['Tur. Início'].fillna('').astype(str).str.strip().str.upper()
        df_realizado['PERCURSO_RAW'] = df['Percurso'].fillna('').astype(str).str.strip().str.replace('.0', '', regex=False)
        df_realizado['PALLETS'] = pd.to_numeric(df['Pallets'], errors='coerce').fillna(0).astype(int)
        
        # 🔌 Mantendo o nome exato em português conforme sua planilha
        txt_data_original = df['data produção ini'].fillna('').astype(str).str.strip()
        df_realizado['DATA_PROD'] = pd.to_datetime(txt_data_original, format='mixed', errors='coerce')
        df_realizado['NUM_MES'] = df_realizado['DATA_PROD'].dt.month.fillna(6).astype(int)
        
        df_realizado = df_realizado[df_realizado['CONCAT'] != '']
        df_realizado['TIPO_FLUXO'] = df_realizado['PERCURSO_RAW'].apply(lambda x: "CARGA" if x.isdigit() else "ESTRADO")
        return df_realizado
    except Exception as e:
        st.error(f"Erro crítico no motor realizado HT: {e}")
        return None


# 🔒 Cache independente para Faturamento HT (Validade: 5 minutos)
@st.cache_data(show_spinner="⏳ Puxando Faturamento HT...")
def carregar_faturamento_ht(ano_selecionado="2026"):
    """ [MÓDULO: FATURAMENTO HT] """
    try:
        df = pd.read_csv(URL_HT_REALIZADO, dtype=str)
        if df.empty: return None
        df.columns = df.columns.str.strip()
        return df
    except Exception:
        return None


# 🔒 Cache independente para Sequenciamento de Lastras (Validade: 5 minutos)
# 🛡️ VERSÃO FINAL V7.4: Inteligente e adaptável para cabeçalhos unificados ou originais
@st.cache_data(show_spinner="⏳ Sincronizando Painel de Lastras...")
def carregar_dados_lastras_novas():
    """ [MÓDULO: SEQUENCIAMENTO DE LASTRAS - PADRÃO MI/ME FLEXÍVEL] """
    try:
        df_tec = pd.read_csv(URL_LASTRAS_NOVAS)
        if df_tec.empty:
            return pd.DataFrame(columns=['PERCURSO', 'TURNO_REALIZOU']), pd.DataFrame()
            
        df_tec.columns = [str(c).strip() for c in df_tec.columns]
        df_real_lastras = pd.DataFrame()
        
        # Percurso inteligente (aceita 'Percurso' ou 'percurso')
        col_percurso = next((c for c in df_tec.columns if c.lower() == 'percurso'), None)
        if col_percurso:
            df_real_lastras['PERCURSO'] = df_tec[col_percurso].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
        else:
            return pd.DataFrame(columns=['PERCURSO', 'TURNO_REALIZOU']), pd.DataFrame()
        
        # Status, Canais e Mercados
        df_real_lastras['STATUS'] = df_tec['STATUS'].astype(str).str.strip().str.upper() if 'STATUS' in df_tec.columns else "NÃO SEQUENCIADO"
        df_real_lastras['CANAL'] = df_tec['CANAL'].astype(str).str.strip() if 'CANAL' in df_tec.columns else "Não Informado"
        df_real_lastras['tipo_unitizacao'] = df_tec['tipo_unitizacao'].astype(str).str.strip().str.upper() if 'tipo_unitizacao' in df_tec.columns else "NÃO INFORMADO"
        df_real_lastras['MOTIVO'] = df_tec['MOTIVO'].astype(str).str.strip() if 'MOTIVO' in df_tec.columns else ""
        df_real_lastras['MERCADO'] = df_tec['MERCADO'].astype(str).str.strip().str.upper() if 'MERCADO' in df_tec.columns else "LASTRA"
        df_real_lastras['qtd_itens'] = pd.to_numeric(df_tec['qtd_itens'], errors='coerce').fillna(0).astype(int) if 'qtd_itens' in df_tec.columns else 0

        # Regra específica e obrigatória de cubagem do Lastrão (frentes especiais)
        f_maquina = pd.to_numeric(df_tec['120X270'], errors='coerce').fillna(0).astype(int) if '120X270' in df_tec.columns else 0
        f_papelao = pd.to_numeric(df_tec['160X160'], errors='coerce').fillna(0).astype(int) if '160X160' in df_tec.columns else 0
        df_real_lastras['120X270'] = f_maquina
        df_real_lastras['160X160'] = f_papelao
        
        # Puxa o TOTAL_GERAL de forma flexível (aceita sua padronização ou o nome com espaço original)
        if 'TOTAL_GERAL' in df_tec.columns:
            df_real_lastras['TOTAL_GERAL'] = pd.to_numeric(df_tec['TOTAL_GERAL'], errors='coerce').fillna(0).astype(int)
        elif 'Total Geral' in df_tec.columns:
            df_real_lastras['TOTAL_GERAL'] = pd.to_numeric(df_tec['Total Geral'], errors='coerce').fillna(0).astype(int)
        else:
            df_real_lastras['TOTAL_GERAL'] = f_maquina + f_papelao

        # Datas dinâmicas (aceita tanto o padronizado 'DT PERCURSO' quanto o original 'data_percurso')
        if 'DT PERCURSO' in df_tec.columns:
            df_real_lastras['DT_PERCURSO'] = pd.to_datetime(df_tec['DT PERCURSO'], dayfirst=True, errors='coerce')
        else:
            df_real_lastras['DT_PERCURSO'] = pd.to_datetime(df_tec['data_percurso'], dayfirst=True, errors='coerce') if 'data_percurso' in df_tec.columns else pd.NaT
            
        df_real_lastras['DT_SEQUENCIADO'] = pd.to_datetime(df_tec['DATA SEQUENCIADO'], dayfirst=True, errors='coerce') if 'DATA SEQUENCIADO' in df_tec.columns else df_real_lastras['DT_PERCURSO']

        # Alocação de turnos padrão da matriz
        for t_base in ['BASE T1', 'BASE T2', 'BASE T3']:
            df_real_lastras[t_base.replace(' ', '_')] = pd.to_numeric(df_tec[t_base], errors='coerce').fillna(0).astype(int) if t_base in df_tec.columns else 0

        if 'TURNO_REAL' in df_tec.columns:
            df_real_lastras['TURNO_ALOCADO'] = pd.to_numeric(df_tec['TURNO_REAL'], errors='coerce').fillna(1.0).astype(str).str.strip()
            df_real_lastras['TURNO_ALOCADO'] = df_real_lastras['TURNO_ALOCADO'].apply(lambda x: f"{float(x):.1f}" if x != 'nan' and x != '' else "1.0")
        else:
            df_real_lastras['TURNO_ALOCADO'] = "1.0"

        df_real_lastras = df_real_lastras.dropna(subset=['PERCURSO'])
        
        # Controle de bipes locais para mitigar concorrência de requisições http 400
        df_bipes_vazio = pd.DataFrame(columns=['PERCURSO', 'TURNO_REALIZOU'])
        return df_bipes_vazio, df_real_lastras
        
    except Exception as e:
        st.error(f"Erro na aba de Lastras v7.4: {e}")
        return pd.DataFrame(columns=['PERCURSO', 'TURNO_REALIZOU']), pd.DataFrame()


# 🔒 Cache independente para Matriz de Capacidade (Validade: 5 minutos)
@st.cache_data(show_spinner="⏳ Carregando Parâmetros Mestre...")
def carregar_matriz_capacidade():
    """ [MÓDULO: PARAMETRIZAÇÃO DINÂMICA] """
    try:
        df = pd.read_csv(URL_HT_ATT)
        if df.empty: return None, {}
        
        df.columns = df.columns.str.strip()
        for col in ['ATIVIDADE', 'METRICA_NOME', 'SUB_DIVISAO']:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
        
        def definir_valor_atual(row):
            override = str(row['OVERRIDE_VALOR']).strip()
            if override and override != 'nan' and override != '':
                try: return float(override) if '.' in override or override == '0.75' else int(float(override))
                except: return override
            val_padrao = row['VALOR_PADRAO']
            try: return float(val_padrao) if int(val_padrao) != float(val_padrao) else int(val_padrao)
            except: return val_padrao

        df['VALOR_REAL'] = df.apply(definir_valor_atual, axis=1)
        
        mapa_metricas = {}
        for _, row in df.iterrows():
            chave = (str(row['ATIVIDADE']), str(row['TURNO']), str(row['METRICA_NOME']), str(row['SUB_DIVISAO']))
            mapa_metricas[chave] = row['VALOR_REAL']
            
        return df, mapa_metricas
    except Exception as e:
        st.error(f"Erro ao carregar a matriz mestre de capacidades: {e}")
        return None, {}