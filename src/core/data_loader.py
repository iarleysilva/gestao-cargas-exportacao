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
    [MÓDULO: DEMANDA SEPARAÇÃO]
    Carrega a aba de Sequenciamento e retorna também a data de atualização da célula A3.
    """
    ID_PUB = "2PACX-1vSqUnWPArdoAcBGkShJALYLN7SzmXeKbus_mzDiT9iP3B3iHEEfRdm1LEVSKEllLLnjgcgX8Lajn7k-"
    GID_ABA = "1997007052"
    url = f"https://docs.google.com/spreadsheets/d/e/{ID_PUB}/pub?output=csv&gid={GID_ABA}"
    
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
        df_real = pd.DataFrame()
        
        if 'STATUS' in df.columns:
            df_real['STATUS'] = df['STATUS'].astype(str).str.strip().str.upper()
        else:
            df_real['STATUS'] = df.iloc[:, 9].astype(str).str.strip().str.upper()

        if 'Percurso' in df.columns:
            df_real['PERCURSO'] = df['Percurso'].astype(str).str.strip().str.replace('.0', '', regex=False)
        else:
            df_real['PERCURSO'] = df.iloc[:, 1].astype(str).str.strip().str.replace('.0', '', regex=False)
        
        df_real['DT_1_FIRME'] = pd.to_datetime(df.iloc[:, 2], format='mixed', errors='coerce')
        df_real['DT_PERCURSO'] = pd.to_datetime(df.iloc[:, 5], format='mixed', errors='coerce')
        df_real['DT_SEQUENCIADO'] = pd.to_datetime(df.iloc[:, 7], format='mixed', errors='coerce') 
        
        cxs = pd.to_numeric(df.iloc[:, 3], errors='coerce').fillna(0)
        pls = pd.to_numeric(df.iloc[:, 4], errors='coerce').fillna(0)
        df_real['VOLUME_TOTAL'] = (cxs + pls).astype(int)
        
        df_real['CONTROLE_TACTICO'] = df.iloc[:, 0].astype(str).str.strip()
        df_real['TURNO_ALOCADO'] = df.iloc[:, 8].astype(str).str.strip()
        
        df_real = df_real.dropna(subset=['PERCURSO'])
        df_real = df_real[(df_real['PERCURSO'] != 'nan') & (df_real['PERCURSO'] != '')]
        df_real = df_real[df_real['VOLUME_TOTAL'] > 0]
        
        return df_real, data_corte_separacao, dt_a3_str
    except Exception as e:
        st.error(f"Erro no mapeamento dos dados: {e}")
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
                # Transforma todos os cabeçalhos em maiúsculas eliminando espaços laterais invisíveis
                df.columns = [str(c).strip().upper() for c in df.columns]
                
                # Faz a varredura inteligente procurando qualquer coluna que possua "PERCURSO" no nome
                col_percurso = next((c for c in df.columns if "PERCURSO" in c), None)
                
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
    [MÓDULO: LASTRAS]
    Puxa o histórico de bipes realizados e a NOVA aba unificada de planejamento de Lastras.
    """
    url_bipes = {
        "TURNO 1": "https://docs.google.com/spreadsheets/d/e/2PACX-1vTS8d44ajH4_Hm7uaAWVbejIzmbMqK8fCbYEPYWddDc4pnbFBhyOye4vs6QmtJ-a51V-b9HDTFPDcSw/pub?gid=0&single=true&output=csv",
        "TURNO 2": "https://docs.google.com/spreadsheets/d/e/2PACX-1vTS8d44ajH4_Hm7uaAWVbejIzmbMqK8fCbYEPYWddDc4pnbFBhyOye4vs6QmtJ-a51V-b9HDTFPDcSw/pub?gid=1250180014&single=true&output=csv",
        "TURNO 3": "https://docs.google.com/spreadsheets/d/e/2PACX-1vTS8d44ajH4_Hm7uaAWVbejIzmbMqK8fCbYEPYWddDc4pnbFBhyOye4vs6QmtJ-a51V-b9HDTFPDcSw/pub?gid=1415290687&single=true&output=csv"
    }
    
    URL_NOVA_LASTRA = "https://docs.google.com/spreadsheets/d/1vLyusstssHb_6mj7JUq-aXwnTweqPxxSD5DxhISB1Q0/export?format=csv&gid=2016672411"
    
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
        
        df_tec['DATA_SEQ'] = pd.to_datetime(df_tec['DATA_SEQUENCIADO'], errors='coerce')
        df_tec['PERCURSO_CHAVE'] = df_tec['PERCURSO'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
        df_tec['TURNO_CHAVE'] = df_tec['TURNO_ALOCADO'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
        
        for col in ['120X270', '160 X 160', 'PC', 'M2', 'PESO BRUTO']:
            if col in df_tec.columns:
                df_tec[col] = pd.to_numeric(df_tec[col], errors='coerce').fillna(0)
            else:
                df_tec[col] = 0
        return df_realizado, df_tec
    except Exception as e:
        st.error(f"Erro ao mapear a nova aba de Lastras: {e}")
        return df_realizado, pd.DataFrame()