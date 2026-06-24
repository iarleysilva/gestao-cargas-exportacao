import streamlit as st
import pandas as pd
from datetime import datetime, time
import zoneinfo
from src.core.data_loader import carregar_dados_lastras_novas

st.set_page_config(page_title="Capacidade Separação Lastras", page_icon="📊", layout="wide")

# Estilização PCO Premium para restrições físicas
st.markdown("""
<style>
    .lastra-card { background-color: #f8fafc; border-left: 5px solid #0f766e; border-radius: 8px; padding: 20px; height: 100%; }
    .lastra-card.danger { border-left-color: #ef4444; }
    .lastra-card.warning { border-left-color: #f59e0b; }
    .lastra-title { color: #64748b; font-size: 0.85rem; font-weight: 700; text-transform: uppercase; margin-bottom: 8px; }
    .lastra-value { color: #1e293b; font-size: 2rem; font-weight: 800; line-height: 1.1; }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center; color: #0F766E;'>📊 Capacidade Operacional vs Restrição Físcas de Lastras</h1>", unsafe_allow_html=True)
st.markdown("---")

# Controle Temporal Avançado do PCO
fuso_br = zoneinfo.ZoneInfo("America/Sao_Paulo")
agora_br = datetime.now(fuso_br)
hoje_br = agora_br.date()
hora_atual = agora_br.time()
is_sabado = hoje_br.weekday() == 5

# Parametrização Dinâmica Calibrada
LIMIT_CAIXOTES = 12 if is_sabado else 20
CAP_PECAS_TURNO = 150  # Conforme matriz: 150 por turno (Meta Global 450)

_, df_lastras = carregar_dados_lastras_novas()

if df_lastras is not None and not df_lastras.empty:
    
    # Filtro e conversão matemática por percurso
    df_lastras['CX_MAQUINA'] = df_lastras.apply(lambda r: int(r['120X270'] // 20) if r['tipo_unitizacao'] == 'CAIXOTE' else 0, axis=1)
    df_lastras['CX_PAPELAO'] = df_lastras.apply(lambda r: int(r['160X160'] // 23) if r['tipo_unitizacao'] == 'CAIXOTE' else 0, axis=1)
    df_lastras['TOTAL_CAIXOTES'] = df_lastras['CX_MAQUINA'] + df_lastras['CX_PAPELAO']
    
    df_seq = df_lastras[df_lastras['STATUS'] == 'SEQUENCIADO']
    
    st.subheader(f"⚡ Horizonte Tático: {'Sábado (Escala Flexível)' if is_sabado else 'Dia de Semana Tradicional'}")
    
    c1, c2, c3 = st.columns(3)
    turnos_mapeados = [("1.0", c1), ("2.0", c2), ("3.0", c3)]
    
    for t_num, col_layout in turnos_mapeados:
        with col_layout:
            df_t = df_seq[df_seq['TURNO_ALOCADO'] == t_num]
            
            pecas_alocadas = df_t['TOTAL_GERAL'].sum()
            caixotes_gerados = df_t['TOTAL_CAIXOTES'].sum()
            
            # Se for sábado e não houver carga alocada, oculta o turno conforme alinhado
            if is_sabado and pecas_alocadas == 0:
                st.markdown(f"<div class='lastra-card' style='opacity:0.4;'><div class='lastra-title'>Turno {t_num.split('.')[0]}</div><div style='font-size:0.9rem; color:#64748b;'>Sem escala registrada neste sábado.</div></div>", unsafe_allow_html=True)
                continue
                
            # Regra de Trava Dinâmica do PCO
            cap_mecanica = pecas_alocadas if pecas_alocadas > 0 else CAP_PECAS_TURNO
            saldo_vagas = cap_mecanica - pecas_alocadas
            
            # Validação de Estouro Físico de Caixotes
            estourou_caixote = caixotes_gerados > LIMIT_CAIXOTES
            classe_card = "lastra-card danger" if estourou_caixote else ("lastra-card warning" if caixotes_gerados >= LIMIT_CAIXOTES * 0.8 else "lastra-card")
            
            st.markdown(f"""
            <div class="{classe_card}">
                <div class="lastra-title">Turno {t_num.split('.')[0]} {'🚨 ESTOURO' if estourou_caixote else ''}</div>
                <div class="lastra-value">{int(pecas_alocadas)} <span style='font-size:1rem; font-weight:400;'>peças</span></div>
                <div style='margin-top:12px; font-size:0.95rem; font-weight:600; color:#475569;'>
                    📦 Caixotes Ocupados: {int(caixotes_gerados)} / {LIMIT_CAIXOTES}
                </div>
                <div style='font-size:0.8rem; color:#94a3b8; margin-top:4px;'>
                    Capacidade Travada: {int(cap_mecanica)} un | Vagas: {int(saldo_vagas)} un
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            with st.expander("🔎 Detalhes do Turno", expanded=False):
                st.write(f"**Formatos Máquina (120x270):** {int(df_t['120X270'].sum())} peças")
                st.write(f"**Formatos Papelão (160x160):** {int(df_t['160X160'].sum())} peças")
                st.write(f"**Volume em Cavalete (Unitizar):** {int(df_t[df_t['tipo_unitizacao']=='UNITIZAR']['TOTAL_GERAL'].sum())} peças")
else:
    st.error("Erro ao estruturar base de restrições do Lastra.")