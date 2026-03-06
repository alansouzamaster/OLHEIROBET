import streamlit as st
import requests
import math
from datetime import datetime, timedelta

# --- CONFIGURAÇÃO DA API ---
API_KEY = "cd10359c14msheda9060d2cb34cep176fa8jsn3c42386ffb98"
HOST = "sportapi7.p.rapidapi.com"
HEADERS = {"X-RapidAPI-Key": API_KEY, "X-RapidAPI-Host": HOST}

# --- FUNÇÕES DE APOIO ---
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

def formatar_metric(label, prob):
    cor = "#dc3545" if prob < 50 else ("#ffc107" if prob < 75 else "#28a745")
    estrela = "⭐" if prob >= 85 else ""
    # Retorna a estrutura HTML de cada linha da métrica
    return f"""
    <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; border-bottom: 1px solid #2d333b; padding-bottom: 5px;'>
        <span style='color:#bbb; font-size:14px;'>{label}</span>
        <span style='color:{cor}; font-weight:bold; font-size:18px;'>{prob:.1f}% {estrela}</span>
    </div>
    """

# --- INTERFACE ---
st.set_page_config(page_title="PROBET v4.1", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    .res-box { text-align: center; padding: 15px; border-radius: 8px; font-weight: bold; color: white; margin-bottom: 10px; font-size: 20px; }
    .metric-card { background-color: #1c2128; padding: 15px; border-radius: 10px; border: 1px solid #30363d; min-height: 100px; }
    h1, h2, h3 { color: #ffc107 !important; text-align: center; }
    .section-header { color: #ffc107; font-weight: bold; margin-bottom: 10px; font-size: 1.2rem; display: flex; align-items: center; gap: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("⚽ PROBET ANALISE")

# --- FILTROS ---
data_sel = st.date_input("📅 Data das Partidas", value=datetime.now())
data_str = data_sel.strftime('%Y-%m-%d')

@st.cache_data(ttl=600)
def carregar_jogos(d):
    try:
        url = f"https://{HOST}/api/v1/sport/football/scheduled-events/{d}"
        res = requests.get(url, headers=HEADERS, timeout=10)
        return res.json().get('events', []) if res.status_code == 200 else []
    except: return []

jogos = carregar_jogos(data_str)

if jogos:
    ligas = sorted(list(set([j['tournament']['name'] for j in jogos])))
    ligas_sel = st.multiselect("🏆 Selecione as Ligas", ligas)
    jogos_f = [j for j in jogos if j['tournament']['name'] in ligas_sel] if ligas_sel else jogos
    
    if jogos_f:
        opcoes = {f"[{ajustar_horario(j.get('startTimestamp', 0))}] {j['homeTeam']['name']} x {j['awayTeam']['name']}": j for j in jogos_f}
        escolha = st.selectbox("🎯 Escolha uma partida:", list(opcoes.keys()))
        
        if st.button("🔍 GERAR RELATÓRIO PREDITIVO"):
            st.session_state.jogo_selecionado = opcoes[escolha]
            st.session_state.analise_pronta = True

# --- EXIBIÇÃO ---
if st.session_state.get('analise_pronta') and st.session_state.get('jogo_selecionado'):
    j = st.session_state.jogo_selecionado
    st.divider()
    
    # Título e Horário (Sem escudos para evitar erro de imagem 0)
    st.markdown(f"<h1>{j['homeTeam']['name']} vs {j['awayTeam']['name']}</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; font-size: 16px; color: #888;'>{j['tournament']['name']} • {ajustar_horario(j.get('startTimestamp', 0))} (Brasília)</p>", unsafe_allow_html=True)

    # Probabilidades 1X2 (Fixas conforme seu modelo anterior)
    st.write("### Probabilidades 1X2")
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div class='res-box' style='background-color:#1f77b4;'>Casa: 65.0%</div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='res-box' style='background-color:#444;'>Empate: 26.0%</div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='res-box' style='background-color:#dc3545;'>Fora: 9.0%</div>", unsafe_allow_html=True)

    st.divider()
    
    # Mercados Secundários (GOLS, CANTOS, CARTÕES)
    m1, m2, m3 = st.columns(3)
    
    # Médias para o cálculo de Poisson (Exemplo)
    m_total = 2.8 

    with m1:
        st.markdown("<div class='section-header'>⚽ GOLS</div>", unsafe_allow_html=True)
        html_gols = formatar_metric("Over 1.5", calcular_poisson(m_total, 1))
        html_gols += formatar_metric("Over 2.5", calcular_poisson(m_total, 2))
        st.markdown(f"<div class='metric-card'>{html_gols}</div>", unsafe_allow_html=True)

    with m2:
        st.markdown("<div class='section-header'>🚩 CANTOS</div>", unsafe_allow_html=True)
        html_cantos = formatar_metric("Over 8.5", calcular_poisson(9.5, 8))
        html_cantos += formatar_metric("Over 10.5", calcular_poisson(9.5, 10))
        st.markdown(f"
