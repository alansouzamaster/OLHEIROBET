import streamlit as st
import requests
import math
import random
from datetime import datetime, timedelta

# --- CONFIGURAÇÃO DA API ---
API_KEY = "a19cf6b5fcmsh62790bdb0d293ddp131982jsn24158e88f703"
HOST = "sportapi7.p.rapidapi.com"
HEADERS = {"X-RapidAPI-Key": API_KEY, "X-RapidAPI-Host": HOST}

# --- FUNÇÕES MATEMÁTICAS ---
def calcular_poisson(media, alvo):
    if media <= 0: return 0
    prob_acumulada = 0
    for i in range(int(alvo) + 1):
        prob_i = (math.exp(-media) * (media**i)) / math.factorial(i)
        prob_acumulada += prob_i
    return (1 - prob_acumulada) * 100

def prever_1x2(m_casa, m_fora):
    total = m_casa + m_fora
    p_draw = 26.0 
    sobra = 100 - p_draw
    p_home = sobra * (m_casa / total) if total > 0 else 37.0
    p_away = sobra * (m_fora / total) if total > 0 else 37.0
    return p_home, p_draw, p_away

def exibir_forma(resultados):
    html = ""
    for r in resultados:
        cor = "#28a745" if r == "V" else "#ffc107" if r == "E" else "#dc3545"
        html += f'<span style="display:inline-block; width:22px; height:22px; background-color:{cor}; border-radius:4px; margin-right:4px; text-align:center; color:white; font-size:12px; line-height:22px; font-weight:bold;">{r}</span>'
    return html

# --- INTERFACE E CSS ---
st.set_page_config(page_title="OLHEIROBET PRO", layout="wide", page_icon="⚽")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #e0e0e0; }
    div[data-testid="stMetricValue"] { color: #ffc107 !important; font-size: 24px !important; }
    .stMetric { background-color: #1c2128; padding: 15px; border-radius: 12px; border: 1px solid #30363d; }
    .oportunidade-card { background-color: #1c2128; padding: 15px; border-top: 3px solid #ffc107; border-radius: 8px; margin-bottom: 10px; }
    .stButton>button { width: 100%; background-color: #ffc107 !important; color: black !important; font-weight: bold; border: none; padding: 10px; border-radius: 8px; }
    .mercado-titulo { color: #ffc107; font-weight: bold; margin-bottom: 10px; border-bottom: 1px solid #333; }
    .1x2-box { text-align: center; padding: 10px; border-radius: 5px; font-weight: bold; margin: 2px; }
    </style>
    """, unsafe_allow_html=True)

st.title("OLHEIRO PRO")

# --- SIDEBAR ---
st.sidebar.markdown("<h2 style='color: #ffc107;'>MENU</h2>", unsafe_allow_html=True)
data_sel = st.sidebar.date_input("Escolha a Data", value=datetime.now())

@st.cache_data(ttl=3600)
def carregar_jogos(data_str):
    try:
        url = f"https://{HOST}/api/v1/sport/football/scheduled-events/{data_str}"
        response = requests.get(url, headers=HEADERS)
        return response.json().get('events', []) if response.status_code == 200 else []
    except: return []

jogos = carregar_jogos(data_sel.strftime('%Y-%m-%d'))

if jogos:
    # --- JOGOS QUENTES ---
    st.subheader("🔥 Melhores Oportunidades do Dia (+2.5 Gols)")
    quentes = []
    for j in jogos:
        m_simulada = random.uniform(2.2, 3.4)
        prob = calcular_poisson(m_simulada, 2)
        if prob > 72:
            quentes.append({"obj": j, "prob": prob})
    
    if quentes:
        cols_q = st.columns(len(quentes[:4]))
        for i, q in enumerate(quentes[:4]):
            with cols_q[i]:
                st.markdown(f"""
                <div class='oportunidade-card'>
