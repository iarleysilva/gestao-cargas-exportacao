import streamlit as st
import pandas as pd
from datetime import timedelta
from src.core.data_loader import carregar_dados_separacao, carregar_execucao_turnos

st.set_page_config(page_title="Capacidade por Data", layout="wide")

st.title("📊 Módulo 3: Painel de Capacidade e Linha de Tempo Operacional")

# Recebe os dados e a data de corte oficial da célula A3
df_demanda, data_corte_a3, txt_completo_a3 = carregar_dados_separacao()
df_execucao = carregar_execucao_turnos()

if df_demanda is not None and df_execucao is not None:
    
    st.info(f"🔄 **Última Atualização da Separação (Célula A3):** {txt_completo_a3}")
    
    # ─── BLOCO DE LEGENDA DO SEMÁFORO ───
    with st.expander("ℹ️ Legenda do Status de Capacidade (Clique para expandir)", expanded=True):
        st.markdown("""
        * ⚪ **Cinza:** Data histórica/passada (Anterior à atualização da célula A3). O saldo de vagas não se aplica.
        * 🟢 **Verde:** Dia 100% livre. Nenhuma carga alocada ainda, capacidade total disponível para receber programação (Visualização estendida para 5 dias).
        * 🟡 **Amarelo:** Operação activa. Existem percursos sendo separados na esteira, mas o volume ainda respeita o limite do dia.
        * 🔴 **Vermelho:** Estouro de capacidade. O volume total alocado para esta janela ultrapassou o teto físico dos turnos.
        """)
    
    st.markdown("---")

    # Identificação de MATCH
    df_modelo = pd.merge(df_demanda, df_execucao, on='PERCURSO', how='left')
    df_modelo['DEU_MATCH'] = df_modelo['TURNO_REALIZOU'].notna()
    
    # ─── LOGICA DO HORIZONTE MÓVEL DE 5 DIAS PARA A FRENTE ───
    # Captura as datas existentes na planilha
    datas_planilha = set(df_modelo['DT_SEQUENCIADO'].dropna().unique()) | set(df_modelo['DT_PERCURSO'].dropna().unique())
    datas_planilha = {pd.to_datetime(d) for d in datas_planilha}
    
    # Força a criação dos próximos 5 dias corridos a partir da data de corte A3
    datas_futuras_obrigatorias = {data_corte_a3 + timedelta(days=i) for i in range(6)} # Garante hoje + 5 dias para a frente
    
    # Une os dois conjuntos para não perder nenhum histórico atrasado e garantir o horizonte futuro
    todas_datas = datas_planilha | datas_futuras_obrigatorias
    datas_ordenadas = sorted(list(todas_datas))
    
    # 3. CONSTRUÇÃO DA GRADE DE CARDS CONTÍNUA
    for dt in datas_ordenadas:
        # Se for uma data antiga e não tiver nenhuma pendência sem match, pula para limpar a tela
        df_atrasos_data = df_modelo[(df_modelo['DT_SEQUENCIADO'] == dt) & (df_modelo['DEU_MATCH'] == False) & (dt < data_corte_a3)]
        if dt < data_corte_a3 and df_atrasos_data.empty:
            continue
            
        dt_formatada = dt.strftime('%d/%m/%Y (%a)')
        
        # Define capacidade do dia (Sábado = 260 | Semana = 520 | Domingo = 0)
        is_sabado = dt.weekday() == 5
        is_domingo = dt.weekday() == 6
        
        cap_t1 = 0 if is_domingo else (130 if is_sabado else 260)
        cap_t2 = 0 if is_domingo else (130 if is_sabado else 260)
        capacidade_total_dia = cap_t1 + cap_t2
        
        # Coleta de volumes existentes na base para esta data
        df_seq_nesta_data = df_modelo[(df_modelo['STATUS'] == "SEQUENCIADO") & (df_modelo['DT_SEQUENCIADO'] == dt)] if not df_modelo.empty else pd.DataFrame()
        vol_seq_total = df_seq_nesta_data['VOLUME_TOTAL'].sum() if not df_seq_nesta_data.empty else 0
        
        vol_seq_t1 = df_seq_nesta_data[df_seq_nesta_data['TURNO_ALOCADO'].str.upper().str.contains("1", na=False)]['VOLUME_TOTAL'].sum() if not df_seq_nesta_data.empty else 0
        vol_seq_t2 = df_seq_nesta_data[df_seq_nesta_data['TURNO_ALOCADO'].str.upper().str.contains("2", na=False)]['VOLUME_TOTAL'].sum() if not df_seq_nesta_data.empty else 0
        
        df_nao_seq_nesta_data = df_modelo[(df_modelo['STATUS'] == "NÃO SEQUENCIADO") & (df_modelo['DT_PERCURSO'] == dt)] if not df_modelo.empty else pd.DataFrame()
        vol_nao_seq = df_nao_seq_nesta_data['VOLUME_TOTAL'].sum() if not df_nao_seq_nesta_data.empty else 0
        
        # REGRAS DO SEMÁFORO DE CORES E SALDO PREDITIVO
        if dt < data_corte_a3:
            cor_bolinha = "⚪"
            txt_saldo = "Data Histórica Encerrada"
            saldo_disponivel = 0
        elif is_domingo:
            cor_bolinha = "⚪"
            txt_saldo = "Domingo - Fábrica Fechada"
            saldo_disponivel = 0
        else:
            saldo_disponivel = capacidade_total_dia - (vol_seq_total + vol_nao_seq)
            
            if saldo_disponivel < 0:
                cor_bolinha = "🔴"
                txt_saldo = f"Saldo Esgotado: {saldo_disponivel} Acessos"
            elif (vol_seq_total + vol_nao_seq) > 0:
                cor_bolinha = "🟡"
                txt_saldo = f"Saldo Disponível: {saldo_disponivel} Acessos"
            else:
                cor_bolinha = "🟢"
                txt_saldo = f"Totalmente Livre: {saldo_disponivel} Vagas"

        # Título dinâmico do Card Expansível
        header_card = f"{cor_bolinha} Horizonte: {dt_formatada} | {txt_saldo}"
        
        # Alerta de retorno operacional interno
        vol_risco_retorno = 0
        if not df_seq_nesta_data.empty:
            df_antecipadas_com_risco = df_seq_nesta_data[(df_seq_nesta_data['DT_PERCURSO'] > dt) & (df_seq_nesta_data['DEU_MATCH'] == False)]
            vol_risco_retorno = df_antecipadas_com_risco['VOLUME_TOTAL'].sum()
        
        with st.expander(header_card, expanded=(dt == data_corte_a3)):
            c1, c2, c3, c4 = st.columns(4)
            
            with c1:
                st.markdown(f"**Capacidade Operacional**\n* T1 (05h - 13:30): **{cap_t1}**\n* T2 (13:30 - 22h): **{cap_t2}**\n* Total Teto: **{capacidade_total_dia}**")
            
            with c2:
                st.markdown(f"**Sequenciado para Rodar**\n* Total Alocado: **{vol_seq_total}**\n* No Turno 1: **{vol_seq_t1}**\n* No Turno 2: **{vol_seq_t2}**")
                
            with c3:
                st.markdown(f"**Carteira Local da Data**\n* Não Sequenciados: **{vol_nao_seq}** Acessos")
                
            with c4:
                if dt < data_corte_a3 or is_domingo:
                    st.info("Sem pendências operacionais ativas.")
                elif vol_risco_retorno > 0:
                    st.warning(f"⚠️ **Risco de Retorno:** {vol_risco_retorno} acessos de datas futuras estão rodando nesta janela. Se não houver MATCH até o fim do turno, voltam para a carteira!")
                else:
                    st.success("Fluxo livre para novos percursos.")
            
            # Tabela micro de conferência interna (Apenas se houver dados reais na base)
            df_unido_dia = pd.concat([df_seq_nesta_data, df_nao_seq_nesta_data]).drop_duplicates(subset=['PERCURSO']) if (not df_seq_nesta_data.empty or not df_nao_seq_nesta_data.empty) else pd.DataFrame()
            if not df_unido_dia.empty:
                st.markdown("---")
                df_unido_view = df_unido_dia.copy()
                df_unido_view['Data_Origem_Percurso'] = df_unido_view['DT_PERCURSO'].dt.strftime('%d/%m/%Y')
                df_unido_view['Status_Match'] = df_unido_view['DEU_MATCH'].map({True: "Bipado (Match) ✅", False: "Aguardando Turno ⏳"})
                
                st.dataframe(
                    df_unido_view[['PERCURSO', 'VOLUME_TOTAL', 'STATUS', 'Data_Origem_Percurso', 'Status_Match']].rename(columns={
                        'VOLUME_TOTAL': 'Acessos',
                        'STATUS': 'Status Planilha',
                        'Data_Origem_Percurso': 'Data do Percurso'
                    }),
                    use_container_width=True, hide_index=True
                )

else:
    st.error("Erro ao estruturar base cruzada.")