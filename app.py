import streamlit as st
import requests
import math
from datetime import datetime, timedelta

# --- CONFIGURAÇÃO DA API ---
API_KEY = "cd10359c14msheda9060d2cb34cep176fa8jsn3c42386ffb98"
HOST = "sportapi7.p.rapidapi.com"
HEADERS = {"X-RapidAPI-Key": API_KEY, "X-RapidAPI-Host": HOST}

# --- INICIALIZAÇÃO DE ESTADO ---
if 'analise_pronta' not in st.session_state:
    st.session_state.analise_pronta = False
    st.session_state.jogo_selecionado = None

# --- FUNÇÕES ---
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
st.set_page_config(page_title="PROBET v6.2", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0b0e11; color: white; }
    .res-box { text-align: center; padding: 15px; border-radius: 12px; font-weight: bold; color: white; margin-bottom: 10px; font-size: 20px; }
    .card-gols { background: #16222e; padding: 20px; border-radius: 15px; border: 1px solid #1e3a5f; }
    .card-cantos { background: #162e21; padding: 20px; border-radius: 15px; border: 1px solid #1e5f3a; }
    .card-cards { background: #2e2616; padding: 20px; border-radius: 15px; border: 1px solid #5f4d1e; }
    .label-text { color: #bbb; font-size: 13px; }
    .prob-text { font-weight: bold; font-size: 15px; }
    .bar-bg { background-color: #2d333b; border-radius: 10px; height: 8px; width: 100%; margin-bottom: 15px; }
</style>
""", unsafe_allow_html=True)

st.title("⚽ PROBET ANALISE")

data_sel = st.date_input("📅 Data", value=datetime.now())
jogos = carregar_jogos(data_sel.strftime('%Y-%m-%d'))

if jogos:
    ligas = sorted(list(set([j['tournament']['name'] for j in jogos])))
    ligas_sel = st.multiselect("🏆 Ligas", ligas)
    jogos_f = [j for j in jogos if j['tournament']['name'] in ligas_sel] if ligas_sel else jogos
    
    if jogos_f:
        opcoes = {f"[{ajustar_horario(j.get('startTimestamp', 0))}] {j['homeTeam']['name']} x {j['awayTeam']['name']}": j for j in jogos_f}
        escolha = st.selectbox("🎯 Partida:", list(opcoes.keys()))
        
        if st.button("🔍 GERAR RELATÓRIO"):
            st.session_state.jogo_selecionado = opcoes[escolha]
            st.session_state.analise_pronta = True

if st.session_state.analise_pronta and st.session_state.jogo_selecionado:
    j = st.session_state.jogo_selecionado
    m_total = 2.8 # Média base para exemplo técnico
    
    st.markdown(f"<h1 style='text-align:center;'>{j['homeTeam']['name']} VS {j['awayTeam']['name']}</h1>", unsafe_allow_html=True)
    
    st.write("### 📊 Probabilidades 1X2")
    c1, c2, c3 = st.columns(3)
    c1.markdown("<div class='res-box' style='background:#1f77b4;'>CASA: 65%</div>", unsafe_allow_html=True)
    c2.markdown("<div class='res-box' style='background:#333;'>EMPATE: 26%</div>", unsafe_allow_html=True)
    c3.markdown("<div class='res-box' style='background:#dc3545;'>FORA: 9%</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)

    # Função interna para evitar erro de renderização
    def draw_metric(label, p):
        cor = "#28a745" if p >= 75 else ("#ffc107" if p >= 50 else "#dc3545")
        glow = f"box-shadow: 0 0 12px {cor};" if p >= 80 else ""
        return f"""
        <div style='display:flex; justify-content:space-between;'>
            <span class='label-text'>{label}</span>
            <span class='prob-text' style='color:{cor};'>{p:.1f}%</span>
        </div>
        <div class='bar-bg'><div style='background-color:{cor}; width:{p}%; height:100%; border-radius:10px; {glow}'></div></div>
        """

    with col1:
        st.markdown("<p style='text-align:center; color:#ffc107; font-weight:bold;'>⚽ GOLS</p>", unsafe_allow_html=True)
        g1 = draw_metric("OVER 1.5 GOLS", calcular_poisson(m_total, 1))
        g2 = draw_metric("OVER 2.5 GOLS", calcular_poisson(m_total, 2))
        st.write(f"<div class='card-gols'>{g1}{g2}</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("<p style='text-align:center; color:#ffc107; font-weight:bold;'>🚩 CANTOS</p>", unsafe_allow_html=True)
        s1 = draw_metric("OVER 5.5 CANTOS", calcular_poisson(9.5, 5))
        s2 = draw_metric("OVER 8.5 CANTOS", calcular_poisson(9.5, 8))
        st.write(f"<div class='card-cantos'>{s1}{s2}</div>", unsafe_allow_html=True)

    with col3:
        st.markdown("<p style='text-align:center; color:#ffc107; font-weight:bold;'>🟨 CARTÕES</p>", unsafe_allow_html=True)
        ct1 = draw_metric("OVER 1.5 CARTÕES", calcular_poisson(4.2, 1))
        ct2 = draw_metric("OVER 3.5 CARTÕES", calcular_poisson(4.2, 3))
        st.write(f"<div class='card-cards'>{ct1}{ct2}</div>", unsafe_allow_html=True)

    if st.button("🗑️ LIMPAR"):
        st.session_state.analise_pronta = False
        st.rerun()
