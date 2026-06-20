import streamlit as st
import pandas as pd
from datetime import timedelta
from src.core.data_loader import carregar_dados_separacao, carregar_execucao_turnos

st.set_page_config(page_title="Capacidade ME", layout="wide")

# Título Principal com Estilo Torre de Controle (PCO)
st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>📊 Módulo 3: Capacidade & Aderência em Tempo Real - Separação ME</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 1.2rem; color: #4B5563;'>Visão tática de chão de fábrica: Sincronização instantânea de bipes de coletores, volumes pendentes e saldos operacionais.</p>", unsafe_allow_html=True)
st.markdown("---")

# Recebe os dados e a data de corte oficial da célula A3
df_demanda, data_corte_a3, txt_completo_a3 = carregar_dados_separacao()
df_execucao = carregar_execucao_turnos()

if df_demanda is not None and df_execucao is not None:
    
    # Barra de Status Superior Clean
    st.markdown(f"📊 **Status do Sistema:** Última atualização da separação (Célula A3) em `{txt_completo_a3}`")
    
    # ─── BLOCO DE LEGENDA DO SEMÁFORO (FOCADO EM PENDENTES) ───
    with st.expander("🔬 Legenda de Status e Monitoramento PCO (Clique para expandir)", expanded=True):
        st.markdown("""
        * ⚪ **Cinza:** Data histórica encerrada ou fábrica fechada.
        * 🟢 **Verde (Janela Livre):** Nenhum volume pendente na linha. Capacidade operacional total desimpedida.
        * 🟡 **Amarelo (Operação Estável):** Há volumes pendentes rodando na linha, mas o saldo de segurança do dia é positivo.
        * 🔴 **🔴 Vermelho (Gargalo Ativo):** O volume que ainda está pendente supera a capacidade máxima de escoamento dos turnos!
        """)
    
    st.markdown("---")

    # Identificação de MATCH (Realizado em Tempo Real)
    df_modelo = pd.merge(df_demanda, df_execucao, on='PERCURSO', how='left')
    df_modelo['DEU_MATCH'] = df_modelo['TURNO_REALIZOU'].notna()
    
    # ─── LOGICA DO HORIZONTE MÓVEL ───
    datas_planilha = set(df_modelo['DT_SEQUENCIADO'].dropna().unique()) | set(df_modelo['DT_PERCURSO'].dropna().unique())
    datas_planilha = {pd.to_datetime(d) for d in datas_planilha}
    
    datas_futuras_obrigatorias = {data_corte_a3 + timedelta(days=i) for i in range(6)}
    todas_datas = datas_planilha | datas_futuras_obrigatorias
    datas_ordenadas = sorted(list(todas_datas))
    
    st.markdown("### 🗓️ Linha do Tempo Dinâmica de Escoamento")
    
    # ─── CONSTRUÇÃO DA GRADE DE TIMELINE OPERACIONAL ───
    for dt in datas_ordenadas:
        df_atrasos_data = df_modelo[(df_modelo['DT_SEQUENCIADO'] == dt) & (df_modelo['DEU_MATCH'] == False) & (dt < data_corte_a3)]
        if dt < data_corte_a3 and df_atrasos_data.empty:
            continue
            
        dt_formatada = dt.strftime('%d/%m/%Y (%a)')
        
        # Definição das capacidades padrão por turno
        is_sabado = dt.weekday() == 5
        is_domingo = dt.weekday() == 6
        
        cap_t1 = 0 if is_domingo else (130 if is_sabado else 260)
        cap_t2 = 0 if is_domingo else (130 if is_sabado else 260)
        capacidade_total_dia = cap_t1 + cap_t2
        
        # 🟢 CONSOLIDAÇÃO DOS DADOS EM TEMPO REAL (MÁGICA DO PCO)
        df_seq_nesta_data = df_modelo[(df_modelo['STATUS'] == "SEQUENCIADO") & (df_modelo['DT_SEQUENCIADO'] == dt)] if not df_modelo.empty else pd.DataFrame()
        df_nao_seq_nesta_data = df_modelo[(df_modelo['STATUS'] == "NÃO SEQUENCIADO") & (df_modelo['DT_PERCURSO'] == dt)] if not df_modelo.empty else pd.DataFrame()
        
        # União de toda a carga destinada para este dia
        df_unido_dia = pd.concat([df_seq_nesta_data, df_nao_seq_nesta_data]).drop_duplicates(subset=['PERCURSO']) if (not df_seq_nesta_data.empty or not df_nao_seq_nesta_data.empty) else pd.DataFrame()
        
        volume_total_planejado = df_unido_dia['VOLUME_TOTAL'].sum() if not df_unido_dia.empty else 0
        
        # Separação por MATCH dos coletores
        volume_realizado_match = df_unido_dia[df_unido_dia['DEU_MATCH'] == True]['VOLUME_TOTAL'].sum() if not df_unido_dia.empty else 0
        volume_pendente_linha = df_unido_dia[df_unido_dia['DEU_MATCH'] == False]['VOLUME_TOTAL'].sum() if not df_unido_dia.empty else 0

        # REGRAS DO SEMÁFORO BASEADO NO FANTASMA EM LINHA (VOLUME PENDENTE)
        if dt < data_corte_a3:
            cor_bolinha = "⚪"
            txt_saldo = f"Pendências Represadas do Passado: {volume_pendente_linha} Acessos"
            saldo_disponivel = 0
        elif is_domingo:
            if volume_total_planejado <= 0: continue
            cor_bolinha = "⚪"
            txt_saldo = f"Aviso: Plantão de Domingo com {volume_pendente_linha} Pendentes"
            saldo_disponivel = 0
        else:
            # O Saldo real é quanto teto resta subtraindo apenas quem AINDA NÃO FOI BIPADO
            saldo_disponivel = capacidade_total_dia - volume_pendente_linha
            
            if saldo_disponivel < 0:
                cor_bolinha = "🔴"
                txt_saldo = f"ESTOURO DE CAPACIDADE: {saldo_disponivel} Acessos"
            elif volume_pendente_linha > 0:
                cor_bolinha = "🟡"
                txt_saldo = f"Operação Ativa: {saldo_disponivel} Vagas Disponíveis"
            else:
                cor_bolinha = "🟢"
                txt_saldo = f"FLUXO LIMPO: {saldo_disponivel} Vagas Livres"

        header_card = f"{cor_bolinha} {dt_formatada} ➔ {txt_saldo}"
        
        # Mantém aberto automaticamente se for o dia atual, se houver estouro ou se estiver 100% livre
        expandir_padrao = (dt == data_corte_a3 or volume_pendente_linha == 0 or saldo_disponivel < 0)
        
        # Alerta de retorno operacional de percursos futuros
        vol_risco_retorno = 0
        if not df_seq_nesta_data.empty:
            df_antecipadas_com_risco = df_seq_nesta_data[(df_seq_nesta_data['DT_PERCURSO'] > dt) & (df_seq_nesta_data['DEU_MATCH'] == False)]
            vol_risco_retorno = df_antecipadas_com_risco['VOLUME_TOTAL'].sum()
        
        with st.expander(header_card, expanded=expandir_padrao):
            c1, c2, c3 = st.columns(3)
            
            with c1:
                st.metric("🎯 Teto dos Turnos", f"{capacidade_total_dia} un", f"T1: {cap_t1} / T2: {cap_t2}")
            with c2:
                st.metric("📦 Carga Planejada (Total)", f"{volume_total_planejado} un", f"Match ✅: {volume_realizado_match} | Linha ⏳: {volume_pendente_linha}")
            with c3:
                # O saldo de pátio zera se for histórico ou domingo
                saldo_card = 0 if (dt < data_corte_a3 or is_domingo) else saldo_disponivel
                st.metric("⚖️ Saldo Livre em Pátio", f"{saldo_card} un", 
                          delta=saldo_card if (dt >= data_corte_a3 and not is_domingo) else None,
                          delta_color="normal" if saldo_card >= 0 else "inverse")
            
            # 📊 Barra de Progresso que responde ao Vivo conforme os bipes acontecem
            if capacidade_total_dia > 0:
                porcentagem_ocupacao_ativa = min(1.0, float(volume_pendente_linha / capacidade_total_dia))
                st.markdown(f"**Pressão de Carga Ativa na Esteira ME:** {int(porcentagem_ocupacao_ativa * 100)}% ocupado por pendências")
                st.progress(porcentagem_ocupacao_ativa)
            
            # Alertas Visuais Contextuais e Rápidos
            if dt < data_corte_a3:
                st.error(f"🛑 **Atenção PCO:** Existem {volume_pendente_linha} acessos do passado sem registro de BIP (Match). Verifique com a liderança do turno.")
            elif is_domingo:
                st.warning("⚠️ **Plantão Ativo:** Fábrica sem escala comercial padrão. Monitore se os bipes estão acontecendo.")
            elif vol_risco_retorno > 0:
                st.warning(f"⚠️ **Risco de Retorno:** {vol_risco_retorno} acessos de datas futuras estão ativos na linha. Sem o bico do coletor até o fim do turno, eles retornam à carteira.")
            elif volume_pendente_linha == 0 and volume_total_planejado > 0:
                st.success("✨ **Turno Concluído!** 100% das faturas programadas receberam MATCH dos coletores.")
            elif volume_pendente_linha == 0:
                st.success("✨ **Janela Totalmente Livre:** Momento ideal para o PCO antecipar ondas e escoar a carteira.")
            elif saldo_disponivel < 0:
                st.error("🚨 **Gargalo de Escoamento Ativo:** O volume que resta na esteira supera a velocidade máxima dos turnos correntes.")
            else:
                st.info("🔋 **Fluxo Sob Controle:** O volume pendente está perfeitamente acomodado dentro do teto operacional.")
            
            # ─── DETALHAMENTO DE CONFERÊNCIA TÉCNICA OCULTADO POR PADRÃO VIA SUB-EXPANDER ───
            if not df_unido_dia.empty:
                with st.expander("🔎 Clique para inspecionar os percursos e faturas deste horizonte", expanded=False):
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
    st.error("Erro ao cruzar as bases de dados. Certifique-se de que as tabelas de Demanda e Execução possuem a chave 'PERCURSO'.")