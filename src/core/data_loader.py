import pandas as pd
import streamlit as st

def carregar_e_tratar_dados():
    """
    [MÓDULO: DEMANDA HT]
    Conecta à planilha original de demandas HT e lê a célula A2 para atualização.
    """
    ID_PLANILHA = "1BYnAn1HYGkrJgCC-L0TCKVepLt3do6zqCPJvYhzcq_Y"
    url_base = f"https://docs.google.com/spreadsheets/d/{ID_PLANILHA}/export?format=csv&gid=1836411567"
    url_atualizacao = f"https://docs.google.com/spreadsheets/d/{ID_PLANILHA}/export?format=csv&gid=1318835351"
    
    try:
        df_att = pd.read_csv(url_atualizacao, header=None)
        data_atualizacao = str(df_att.iloc[1, 0]).strip() if len(df_att) > 1 else "Não informada"
    except Exception:
        data_atualizacao = "Erro na leitura"

    try:
        df = pd.read_csv(url_base)
        if df.empty: return None, data_atualizacao
        df.columns = df.columns.str.strip()
        df_real = pd.DataFrame()
        
        df_real['Tipo'] = df['Tipo'] if 'Tipo' in df.columns else "Carga"
        df_real['Status'] = df['Status Perc'] if 'Status Perc' in df.columns else df.iloc[:, 1]
        df_real['Fatura'] = df['Fatura'] if 'Fatura' in df.columns else df.iloc[:, 8]
        df_real['Percurso'] = df['Percurso'] if 'Percurso' in df.columns else df.iloc[:, 9]
        df_real['Total_Plt_Percurso'] = df['Total_Plt_Percurso'] if 'Total_Plt_Percurso' in df.columns else df.iloc[:, 15]
        df_real['Data_Carregamento'] = df['Data_Carregamento'] if 'Data_Carregamento' in df.columns else df.iloc[:, 16]
        df_real['Modal'] = df['Modal'] if 'Modal' in df.columns else df.iloc[:, 17]
        
        df_real = df_real.dropna(subset=['Fatura', 'Percurso'], how='all')
        df_real['Data_Carregamento'] = pd.to_datetime(df_real['Data_Carregamento'], errors='coerce')
        return df_real.dropna(subset=['Data_Carregamento']), data_atualizacao
    except Exception:
        return None, "Erro"


def carregar_dados_separacao():
    """
    [MÓDULO: DEMANDA SEPARAÇÃO COMPATIBILIDADE]
    Carrega os dados mapeando estritamente a nova aba oficial 'Sequenciamento_Exportação_v1' 
    identificando a coluna TURNO_REAL de forma prioritária.
    """
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSqUnWPArdoAcBGkShJALYLN7SzmXeKbus_mzDiT9iP3B3iHEEfRdm1LEVSKEllLLnjgcgX8Lajn7k-/pub?gid=2016672411&single=true&output=csv"
    
    ID_PLANILHA_ATT = "1BYnAn1HYGkrJgCC-L0TCKVepLt3do6zqCPJvYhzcq_Y"
    url_atualizacao = f"https://docs.google.com/spreadsheets/d/{ID_PLANILHA_ATT}/export?format=csv&gid=1318835351"
    
    try:
        df_att = pd.read_csv(url_atualizacao, header=None)
        dt_a3_str = str(df_att.iloc[2, 0]).strip() if len(df_att) > 2 else "Não informada"
        data_corte_separacao = pd.to_datetime(dt_a3_str.split()[0], dayfirst=True, errors='coerce')
        if pd.isna(data_corte_separacao):
            data_corte_separacao = pd.to_datetime(pd.Timestamp.now().date())
    except Exception:
        data_corte_separacao = pd.to_datetime(pd.Timestamp.now().date())
        dt_a3_str = "Usando data do sistema"

    try:
        df = pd.read_csv(url)
        # Remove espaços extras dos nomes originais das colunas antes de converter
        df.columns = [str(c).strip() for c in df.columns]
        
        df_real = pd.DataFrame()
        
        # 1. PERCURSO (Chave Principal)
        if 'PERCURSO' in df.columns:
            df_real['PERCURSO'] = df['PERCURSO'].astype(str).str.strip().str.replace('.0', '', regex=False)
        elif 'Percurso' in df.columns:
            df_real['PERCURSO'] = df['Percurso'].astype(str).str.strip().str.replace('.0', '', regex=False)
        else:
            df_real['PERCURSO'] = df.iloc[:, 1].astype(str).str.strip().str.replace('.0', '', regex=False)

        # 2. STATUS
        df_real['STATUS'] = df['STATUS'].astype(str).str.strip().str.upper() if 'STATUS' in df.columns else "SEQUENCIADO"
        
        # 3. DATAS
        df_real['DT_1_FIRME'] = pd.to_datetime(df['DATA 1º FIRME'], errors='coerce') if 'DATA 1º FIRME' in df.columns else pd.to_datetime(pd.Timestamp.now().date())
        df_real['DT_PERCURSO'] = pd.to_datetime(df['DT PERCURSO'], errors='coerce') if 'DT PERCURSO' in df.columns else df_real['DT_1_FIRME']
        
        if 'DATA SEQUENCIADO' in df.columns:
            df_real['DT_SEQUENCIADO'] = pd.to_datetime(df['DATA SEQUENCIADO'], dayfirst=True, errors='coerce')
        else:
            df_real['DT_SEQUENCIADO'] = pd.to_datetime(df['PROGRAMADO'], errors='coerce') if 'PROGRAMADO' in df.columns else df_real['DT_1_FIRME']
        
        # 4. VOLUMES
        cxs = pd.to_numeric(df['CXS'], errors='coerce').fillna(0) if 'CXS' in df.columns else 0
        pls = pd.to_numeric(df['PLS'], errors='coerce').fillna(0) if 'PLS' in df.columns else 0
        df_real['VOLUME_TOTAL'] = (cxs + pls).astype(int)
        
        # 5. MAPEAMENTO DO TURNO (Tratando a nova coluna TURNO_REAL)
        colunas_turno_possiveis = ['TURNO_REAL', 'TURNO REAL', 'TURNO_REALIZOU', 'TURNO']
        col_turno_encontrada = next((c for c in colunas_turno_possiveis if c in df.columns), None)
        
        if col_turno_encontrada:
            df_real['TURNO_ALOCADO'] = pd.to_numeric(df[col_turno_encontrada], errors='coerce').fillna(1.0).astype(str).str.strip()
            df_real['TURNO_ALOCADO'] = df_real['TURNO_ALOCADO'].apply(lambda x: f"{float(x):.1f}" if x != 'nan' and x != '' else "1.0")
        else:
            df_real['TURNO_ALOCADO'] = "1.0"
        
        # Filtra linhas vazias
        df_real = df_real.dropna(subset=['PERCURSO'])
        df_real = df_real[(df_real['PERCURSO'] != 'nan') & (df_real['PERCURSO'] != '')]
        
        return df_real, data_corte_separacao, dt_a3_str
    except Exception as e:
        st.error(f"Erro no mapeamento unificado da aba com TURNO_REAL: {e}")
        return None, pd.to_datetime(pd.Timestamp.now().date()), "Erro"


def carregar_execucao_turnos():
    """
    [MÓDULO: DEMANDA SEPARAÇÃO]
    Carrega os turnos limpando e normalizando os cabeçalhos para garantir o MATCH do Percurso Puro.
    """
    ID_PUB_TURNOS = "2PACX-1vTS8d44ajH4_Hm7uaAWVbejIzmbMqK8fCbYEPYWddDc4pnbFBhyOye4vs6QmtJ-a51V-b9HDTFPDcSw"
    GIDS = {"TURNO 1": "0", "TURNO 2": "1250180014", "TURNO 3": "1415290687"}
    df_consolidado = []
    
    for turno, gid in GIDS.items():
        url = f"https://docs.google.com/spreadsheets/d/e/{ID_PUB_TURNOS}/pub?output=csv&gid={gid}"
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


def carregar_realizado_ht(ano_selecionado="2026"):
    """
    [MÓDULO: REALIZADO HT]
    Carrega a aba de tratamentos realizados sem perda de linhas por falha de tipo.
    """
    ID_PLANILHA = "1BYnAn1HYGkrJgCC-L0TCKVepLt3do6zqCPJvYhzcq_Y"
    GIDS_ANOS = {"2026": "1740948393", "2027": "1740948393"}
    
    gid = GIDS_ANOS.get(ano_selecionado, "1740948393")
    url = f"https://docs.google.com/spreadsheets/d/{ID_PLANILHA}/export?format=csv&gid={gid}"
    
    try:
        df = pd.read_csv(url, dtype=str)
        if df.empty: return None
        
        df.columns = df.columns.str.strip()
        
        df_realizado = pd.DataFrame()
        df_realizado['CONCAT'] = df['CONCAT'].fillna('').astype(str).str.strip()
        df_realizado['TURNO'] = df['Tur. Início'].fillna('').astype(str).str.strip().str.upper()
        df_realizado['PERCURSO_RAW'] = df['Percurso'].fillna('').astype(str).str.strip().str.replace('.0', '', regex=False)
        df_realizado['PALLETS'] = pd.to_numeric(df['Pallets'], errors='coerce').fillna(0).astype(int)
        
        txt_data_original = df['data produção ini'].fillna('').astype(str).str.strip()
        df_realizado['DATA_PROD'] = pd.to_datetime(txt_data_original, format='mixed', errors='coerce')
        
        def processar_mes_linha(row):
            if pd.notna(row['DATA_PROD']):
                return row['DATA_PROD'].month
            
            idx = row.name
            string_data = txt_data_original.iloc[idx] if idx < len(txt_data_original) else ""
            partes = string_data.split('/')
            if len(partes) >= 2:
                try: return int(partes[1])
                except: pass
            return 6
            
        df_realizado['NUM_MES'] = df_realizado.apply(processar_mes_linha, axis=1)
        df_realizado['DATA_PROD'] = df_realizado['DATA_PROD'].fillna(pd.Timestamp.normalize(pd.Timestamp.now()))
        df_realizado = df_realizado[df_realizado['CONCAT'] != '']
        df_realizado = df_realizado[df_realizado['CONCAT'] != 'nan']
        
        def classificar_tipo(percurso_str):
            if percurso_str.isdigit() and percurso_str != '':
                return "CARGA"
            return "ESTRADO"
            
        df_realizado['TIPO_FLUXO'] = df_realizado['PERCURSO_RAW'].apply(classificar_tipo)
        return df_realizado
    except Exception as e:
        st.error(f"Erro crítico no motor data_loader (Módulo 5): {e}")
        return None


def carregar_dados_lastras_novas():
    """
    [MÓDULO: LASTRAS & SEPARAÇÃO ME V1]
    Busca os dados diretamente da nova aba unificada 'Sequenciamento_Exportação_v1'
    vinculada diretamente ao seu link CSV de alta performance.
    """
    url_bipes = {
        "TURNO 1": "https://docs.google.com/spreadsheets/d/e/2PACX-1vTS8d44ajH4_Hm7uaAWVbejIzmbMqK8fCbYEPYWddDc4pnbFBhyOye4vs6QmtJ-a51V-b9HDTFPDcSw/pub?gid=0&single=true&output=csv",
        "TURNO 2": "https://docs.google.com/spreadsheets/d/e/2PACX-1vTS8d44ajH4_Hm7uaAWVbejIzmbMqK8fCbYEPYWddDc4pnbFBhyOye4vs6QmtJ-a51V-b9HDTFPDcSw/pub?gid=1250180014&single=true&output=csv",
        "TURNO 3": "https://docs.google.com/spreadsheets/d/e/2PACX-1vTS8d44ajH4_Hm7uaAWVbejIzmbMqK8fCbYEPYWddDc4pnbFBhyOye4vs6QmtJ-a51V-b9HDTFPDcSw/pub?gid=1415290687&single=true&output=csv"
    }
    
    URL_NOVA_LASTRA = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSqUnWPArdoAcBGkShJALYLN7SzmXeKbus_mzDiT9iP3B3iHEEfRdm1LEVSKEllLLnjgcgX8Lajn7k-/pub?gid=2016672411&single=true&output=csv"
    
    lista_turnos = []
    for t_nome in ["TURNO 1", "TURNO 2", "TURNO 3"]:
        try:
            df = pd.read_csv(url_bipes[t_nome])
            df.columns = [str(c).strip().upper() for c in df.columns]
            data_col = next(c for c in df.columns if "DATA" in c)
            df['DATA_REF'] = pd.to_datetime(df[data_col], dayfirst=True, errors='coerce')
            df['TURNO_ID'] = t_nome.split()[-1]
            per_col = next(c for c in df.columns if "PERCURSO" in c)
            df['PERCURSO_LIMP'] = df[per_col].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
            
            c_mi = next((c for c in df.columns if "MI" in c and "TOTAL" in c), None)
            c_me = next((c for c in df.columns if "ME" in c and "TOTAL" in c), None)
            c_gat = next((c for c in df.columns if "LASTRA" in c and "ACESSOS" in c), None)
            
            df['MI_VAL'] = pd.to_numeric(df[c_mi], errors='coerce').fillna(0) if c_mi else 0
            df['ME_VAL'] = pd.to_numeric(df[c_me], errors='coerce').fillna(0) if c_me else 0
            df['GATILHO'] = pd.to_numeric(df[c_gat], errors='coerce').fillna(0) if c_gat else 0
            
            lista_turnos.append(df[['DATA_REF', 'TURNO_ID', 'PERCURSO_LIMP', 'GATILHO', 'MI_VAL', 'ME_VAL']])
        except Exception:
            continue
        
    df_realizado = pd.concat(lista_turnos, ignore_index=True).dropna(subset=['DATA_REF'])

    try:
        df_tec = pd.read_csv(URL_NOVA_LASTRA)
        df_tec.columns = [str(c).strip().upper() for c in df_tec.columns]
        
        if 'DATA SEQUENCIADO' in df_tec.columns:
            df_tec['DATA_SEQ'] = pd.to_datetime(df_tec['DATA SEQUENCIADO'], dayfirst=True, errors='coerce')
        else:
            df_tec['DATA_SEQ'] = pd.to_datetime(df_tec['PROGRAMADO'], errors='coerce')
            
        df_tec['PERCURSO_CHAVE'] = df_tec['PERCURSO'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
        
        if 'TURNO' in df_tec.columns:
            df_tec['TURNO_CHAVE'] = pd.to_numeric(df_tec['TURNO'], errors='coerce').fillna(1.0).astype(str).str.strip()
            df_tec['TURNO_CHAVE'] = df_tec['TURNO_CHAVE'].apply(lambda x: f"{float(x):.1f}" if x != 'nan' and x != '' else "1.0")
        else:
            df_tec['TURNO_CHAVE'] = "1.0"
        
        for col in ['120X270', '160 X 160', 'PC', 'M2', 'PESO BRUTO']:
            if col in df_tec.columns:
                df_tec[col] = pd.to_numeric(df_tec[col], errors='coerce').fillna(0)
            else:
                df_tec[col] = 0
        return df_realizado, df_tec
    except Exception as e:
        st.error(f"Erro ao mapear a nova aba de Sequenciamento v1: {e}")
        return df_realizado, pd.DataFrame()