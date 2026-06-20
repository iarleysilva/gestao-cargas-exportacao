import streamlit as st
import pandas as pd
from datetime import timedelta
from src.core.data_loader import carregar_e_tratar_dados

st.set_page_config(page_title="Capacidade HT", layout="wide")

st.title("🚛 Módulo 4: Capacidade de Carregamento HT")
st.write("Visão Dinâmica de Linha do Tempo: Identificação ativa de janelas e oportunidades de encaixe.")
st.markdown("---")

df_ht, txt_completo_a2 = carregar_e_tratar_dados()

if df_ht is not None:
    
    try:
        dt_a2_str = txt_completo_a2.split()[0]
        data_corte_a2 = pd.to_datetime(dt_a2_str, dayfirst=True, errors='coerce')
        if pd.isna(data_corte_a2):
            data_corte_a2 = pd.to_datetime(pd.Timestamp.now().date())
    except Exception:
        data_corte_a2 = pd.to_datetime(pd.Timestamp.now().date())

    st.info(f"🔄 **Última Atualização do Carregamento HT (Célula A2):** {txt_completo_a2}")
    
    with st.expander("ℹ️ Legenda do Status de Carregamento", expanded=False):
        st.markdown("""
        * ⚪ **Cinza:** Data histórica/passada com pendências ou Domingo (Sem operação padrão).
        * 🟢 **Verde (Oportunidade):** Janela vazia detectada no meio do fluxo ou próximo dia útil livre. Perfeito para antecipações!
        * 🟡 **Amarelo:** Carteira ativa ocupando o pátio, respeitando o limite físico de escoamento.
        * 🔴 **Vermelho:** Alerta de Estouro! Volume total planejado ultrapassou os 12 ciclos de estufas (350 PLT).
        """)
        
    st.markdown("---")

    df_ht['Data_Ajustada'] = pd.to_datetime(df_ht['Data_Carregamento']).dt.normalize()
    
    # Captura as datas que têm volume real
    df_com_volume = df_ht[df_ht['Total_Plt_Percurso'] > 0]
    datas_reais = set(df_com_volume['Data_Ajustada'].dropna().unique())
    datas_reais = {pd.to_datetime(d) for d in datas_reais}
    
    # ─── LÓGICA INTELIGENTE DE PREENCHIMENTO DE LACUNAS (BURACOS) ───
    if datas_reais:
        menor_data = min(datas_reais)
        # O limite inferior de análise deve ser pelo menos a data de corte A2 ou a menor data com carga atrasada
        inicio_timeline = min(menor_data, data_corte_a2)
        
        # O limite superior será a maior data da planilha + 1 dia útil para projeção de vaga futura
        maior_data_real = max(datas_reais)
        fim_timeline = maior_data_real + timedelta(days=1)
        if fim_timeline.weekday() == 6: # Se cair no domingo, joga para segunda
            fim_timeline += timedelta(days=1)
            
        # Criamos uma sequência contínua dia a dia do início ao fim da linha do tempo
        total_dias_intervalo = (fim_timeline - inicio_timeline).days + 1
        sequencia_continua = {inicio_timeline + timedelta(days=i) for i in range(total_dias_intervalo)}
        
        # União unificada (Garante o histórico passado, o meio preenchido e o dia futuro livre)
        datas_para_renderizar = sorted(list(sequencia_continua))
    else:
        datas_para_renderizar = [data_corte_a2]

    # ─── RENDERIZAÇÃO DA GRADE DE CARDS ───
    for dt in datas_para_renderizar:
        df_cargas_da_data = df_ht[df_ht['Data_Ajustada'] == dt] if not df_ht.empty else pd.DataFrame()
        total_plt_planejado = df_cargas_da_data['Total_Plt_Percurso'].sum() if not df_cargas_da_data.empty else 0
        
        dt_formatada = dt.strftime('%d/%m/%Y (%a)')
        is_domingo = dt.weekday() == 6
        capacidade_nominal_ht = 0 if is_domingo else 350
        
        # REGRAS DO SEMÁFORO EVOLUÍDO
        if dt < data_corte_a2:
            # Se for data passada e por acaso ficou zerada na linha do tempo contínua, pula para não poluir
            if total_plt_planejado <= 0:
                continue
            cor_bolinha = "⚪"
            txt_saldo = f"Sobras do Passado Acumuladas: {total_plt_planejado} PLT"
        elif is_domingo:
            # Só mostra o domingo se o PCP enfiou carga lá por erro, servindo de aviso
            if total_plt_planejado <= 0:
                continue
            cor_bolinha = "⚪"
            txt_saldo = f"Atenção: {total_plt_planejado} PLT alocados em Domingo (Fábrica Fechada)"
        else:
            saldo_disponivel = capacidade_nominal_ht - total_plt_planejado
            
            if total_plt_planejado == 0:
                cor_bolinha = "🟢"
                # Identifica se é um dia saltado no meio da semana ou o último dia livre do horizonte
                if dt < max(datas_para_renderizar):
                    txt_saldo = f"OPORTUNIDADE DE ENCAIXE: {saldo_disponivel} PLT Totalmente Livres!"
                else:
                    txt_saldo = f"Próxima Janela Disponível: {saldo_disponivel} PLT Livres"
            elif saldo_disponivel < 0:
                cor_bolinha = "🔴"
                txt_saldo = f"Estouro de Estufas: {saldo_disponivel} PLT"
            else:
                cor_bolinha = "🟡"
                txt_saldo = f"Saldo de Pátio Livre: {saldo_disponivel} PLT"
                
        header_card = f"{cor_bolinha} Janela de Carregamento: {dt_formatada} | {txt_saldo}"
        
        # Deixa expandido se for o dia atual do corte ou se for um dia de oportunidade vazio
        expandir_padrao = (dt == data_corte_a2 or total_plt_planejado == 0)
        
        with st.expander(header_card, expanded=expandir_padrao):
            c1, c2, c3 = st.columns(3)
            
            with c1:
                st.markdown(f"**Teto de Escoamento**\n* Capacidade Máxima: **{capacidade_nominal_ht}** PLT\n* Equivalência: **12 Ciclos de Estufas**")
            
            with c2:
                ciclos_estimados = round(total_plt_planejado / 27, 1)
                st.markdown(f"**Demanda Alocada para a Data**\n* Volume Planejado: **{total_plt_planejado}** Paletes\n* Ocupação Estimada: **{ciclos_estimados}** Estufas")
                
            with c3:
                if dt < data_corte_a2:
                    st.error("⚠️ **Cargas Atrasadas:** Estes paletes deveriam ter saído. Estão represando o pátio!")
                elif total_plt_planejado == 0:
                    st.success("🟢 **Janela Vazia:** Perfeito para puxar adiantamentos da semana e aliviar os dias amarelos/vermelhos.")
                elif saldo_disponivel < 0:
                    st.warning(f"🚨 **Gargalo Preditivo:** Volume acima do limite diário do pátio.")
                else:
                    st.success("Volume absorvido pela capacidade padrão.")
                    
            if not df_cargas_da_data.empty:
                st.markdown("---")
                st.dataframe(
                    df_cargas_da_data[['Fatura', 'Percurso', 'Total_Plt_Percurso', 'Status', 'Modal']].rename(columns={
                        'Total_Plt_Percurso': 'Paletes',
                        'Status': 'Status Atual'
                    }),
                    use_container_width=True, hide_index=True
                )