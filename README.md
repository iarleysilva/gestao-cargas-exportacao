# 📦 Sistema Integrado de Controle PCO & Fluxo de Separação (MI / ME)

Este ecossistema de software foi projetado para gerenciar, sequenciar e auditar o fluxo operacional e pátio do **Planejamento / PCO**. Ele une uma aplicação em tempo real desenvolvida em **Python (Streamlit)** para monitoramento analítico de pátio com uma camada automatizada de **Google Apps Script** para processamento e governança de dados operacionais de Mercado Interno (MI) e Mercado Externo (ME).

---

## 🚀 1. O Painel Analítico (Python / Streamlit)

A aplicação visual segmenta as demandas de forma estrita de acordo com as janelas operacionais de Brasília (`America/Sao_Paulo`). O motor interno calcula a performance real baseado nos bipes físicos do chão de fábrica.

### ⏱️ Regras Horárias e Veredito de SLA por Turno
O monitoramento adota um gatilho de **15 minutos de tolerância** pós-fechamento do turno físico para congelamento das metas:

* **Turno 1 (05h00 - 13h30):** Gatilho definitivo às **13h45**.
* **Turno 2 (13h30 - 22h00):** Gatilho definitivo às **22h15**.
* **Turno 3 (22h00 - 05h00):** Gatilho definitivo às **05h15** da madrugada seguinte.

> 🔒 **Trava de Meio-Dia / Tarde:** Se o relógio do sistema passar das 05h15 da tarde e houver registros atômicos do Turno 3 da madrugada passada, o painel congela o card visual exibindo o status cinza **`MATE EM MADRUGADA 🔒`** e rotula os itens no banco de dados como **`TURNO FECHADO`**, impedindo que dados históricos sumam da tela ou inflem erraticamente a carteira de sobras.

---

## ⚙️ 2. Motor de Sequenciamento Inteligente (Google Apps Script)

O sistema de processamento de comandos aceita chaves brutas de digitação rápida do operador (inclusive formatos colados sem espaços como `i2m22/06`) e realiza a quebra lógica através de expressões regulares (**Regex**).

### 🗺️ Padrão Ouro de Digitação:
```text
[Mercado][Turno][Motivo] [Data]