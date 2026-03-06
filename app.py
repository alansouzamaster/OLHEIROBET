import streamlit as st
import requests
import math
from datetime import datetime, timedelta

# --- CONFIGURAÇÃO DA API ---
API_KEY = "cd10359c14msheda9060d2cb34cep176fa8jsn3c42386ffb98"
HOST = "sportapi7.p.rapidapi.com"
HEADERS = {"X-RapidAPI-Key": API_KEY, "X-RapidAPI-Host": HOST}

# --- ESTADO DO APP ---
if 'analise_pronta' not in st.session_state:
    st.session_state.analise_pronta = False
    st.session_state.jogo_selecionado = None

# --- FUNÇÕES DE CÁLCULO ---
def ajustar_horario(timestamp):
    dt_utc = datetime.fromtimestamp(timestamp)
    dt_br = dt_utc - timedelta(hours=3)
    return dt_br.strftime('%H:%M')

def calcular_poisson(media, alvo):
    if media <= 0: return 0
    prob_acumulada = 0
    for i in range(int(alvo) + 1):
        prob_i = (math.exp(-media) * (media**i)) / math.factorial(i)
        prob_acumulada += prob_i
    return (1 - prob_acumulada) * 100

@st.cache_data(ttl=600)
def carregar_jogos(d):
    try:
        url = f"https://{HOST}/api/v1/sport/football/scheduled-events/{d}"
        res = requests.get(url, headers=HEADERS, timeout=12)
        return res.json().get('events', []) if res.status_code == 200 else []
    except: return []

# --- INTERFACE ---
st.set_page_config(page_title="PROBET Premium", layout="wide")

# CSS Avançado para cores individuais nas barras de progresso
st.markdown("""
<style>
    .stApp { background-color: #0b0e11; color: white; }
    
    /* Estilização Geral dos Cards */
    [data-testid="stVerticalBlock"] > div {
        background-color: #161b22;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #30363d;
    }

    /* Cores das Barras de Progresso por Coluna */
    /* Coluna 1 (Gols) - Verde */
    [data-testid="stHorizontalBlock"] > div:nth-child(1) .stProgress > div > div > div > div {
        background-color: #28a745 !important;
    }
    /* Coluna 2 (Cantos) - Azul */
    [data-testid="stHorizontalBlock"] > div:nth-child(2) .stProgress > div > div > div > div {
        background-color: #007bff !important;
    }
    /* Coluna 3 (Cartões) - Amarelo */
    [data-testid="stHorizontalBlock"] > div:nth-child(3) .stProgress > div > div > div > div {
        background-color: #ffc107 !important;
    }

    h1, h2, h3 { text-align: center; font-weight: 800; color: #ffc107 !important; }
    [data-testid="stMetricValue"] { font-size: 32px !important; }
</style>
""", unsafe_allow_html=True)

st.title(" PRO ANALISE")

# --- FILTROS ---
data_sel = st.date_input("📅 Data das Partidas", value=datetime.now())
jogos = carregar_jogos(data_sel.strftime('%Y-%m-%d'))

if jogos:
    ligas = sorted(list(set([j['tournament']['name'] for j in jogos])))
    ligas_sel = st.multiselect("🏆 Escolha a Liga", ligas)
    jogos_f = [j for j in jogos if j['tournament']['name'] in ligas_sel] if ligas_sel else jogos
    
    if jogos_f:
        opcoes = {f"[{ajustar_horario(j.get('startTimestamp', 0))}] {j['homeTeam']['name']} x {j['awayTeam']['name']}": j for j in jogos_f}
        escolha = st.selectbox("🎯 Selecione o Jogo", list(opcoes.keys()))
        
        if st.button("🔍 GERAR RELATÓRIO PREDITIVO"):
            st.session_state.jogo_selecionado = opcoes[escolha]
            st.session_state.analise_pronta = True

# --- EXIBIÇÃO ---
if st.session_state.analise_pronta and st.session_state.jogo_selecionado:
    j = st.session_state.jogo_selecionado
    st.divider()
    
    st.header(f"{j['homeTeam']['name']} VS {j['awayTeam']['name']}")
    st.markdown(f"<p style='text-align:center; color:#888;'>{j['tournament']['name']} • {ajustar_horario(j.get('startTimestamp', 0))} (Brasília)</p>", unsafe_allow_html=True)

    # Probabilidades Principais
    st.subheader("📊 Vitória / Empate")
    c1, c2, c3 = st.columns(3)
    c1.metric("Casa (1)", "65.0%")
    c2.metric("Empate (X)", "26.0%")
    c3.metric("Fora (2)", "9.0%")

    st.divider()

    # Mercados de Valor com Barras Coloridas
    m_total = 2.8 
    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("⚽ GOLS")
        p15, p25 = calcular_poisson(m_total, 1), calcular_poisson(m_total, 2)
        st.write(f"**Over 1.5:** {p15:.1f}%")
        st.progress(p15/100)
        st.write(f"**Over 2.5:** {p25:.1f}%")
        st.progress(p25/100)

    with col2:
        st.subheader("🚩 CANTOS")
        c55, c85 = calcular_poisson(9.5, 5), calcular_poisson(9.5, 8)
        st.write(f"**Over 5.5:** {c55:.1f}%")
        st.progress(c55/100)
        st.write(f"**Over 8.5:** {c85:.1f}%")
        st.progress(c85/100)

    with col3:
        st.subheader("🟨 CARTÕES")
        ct15, ct35 = calcular_poisson(4.2, 1), calcular_poisson(4.2, 3)
        st.write(f"**Over 1.5:** {ct15:.1f}%")
        st.progress(ct15/100)
        st.write(f"**Over 3.5:** {ct35:.1f}%")
        st.progress(ct35/100)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🗑️ NOVA CONSULTA"):
        st.session_state.analise_pronta = False
        st.rerun()

