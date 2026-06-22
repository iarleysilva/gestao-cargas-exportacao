import streamlit as st

# ─── BLOCO DE SEGURANÇA DE CAMINHOS ROBUSTO ───
import sys
from pathlib import Path
raiz = Path(__file__).resolve().parents[1]  # Sobe 1 nível (pages/ -> raiz do projeto)
if str(raiz) not in sys.path:
    sys.path.append(str(raiz))
# ──────────────────────────────────────────────

st.set_page_config(page_title="Capacidade Lastras", layout="wide")

# Frase de manutenção simples e direta, sem expor detalhes técnicos
st.title("🪵 Módulo: Capacidade de Separação — Lastras")
st.markdown("---")
st.warning("⚠️ **Aviso:** Este módulo de planejamento técnico está temporariamente em manutenção para melhorias de infraestrutura.")
st.info("💡 Os demais dashboards e painéis de controle do portal continuam operando normalmente.")