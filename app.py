import streamlit as st
import requests
import math
from datetime import datetime

# --- CONFIGURAÇÃO DA API ---
API_KEY = "3a5c2b926bmsh18b3c4624ec302bp1911efjsn84e2922978ff"
HOST = "sportapi7.p.rapidapi.com"
HEADERS = {"X-RapidAPI-Key": API_KEY, "X-RapidAPI-Host": HOST}

# --- ESTADO DA SESSÃO ---
if 'analise_pronta' not in st.session_state:
    st.session_state.analise_pronta = False
    st.session_state.jogo_selecionado = None

# --- FUNÇÕES ---
def calcular_poisson(media, alvo):
    if media <= 0: return 0
    prob_acumulada = 0
    for i in range(int(alvo) + 1):
        prob_i = (math.exp(-media) * (media**i)) / math.factorial(i)
        prob_acumulada += prob_i
    return (1 - prob_acumulada) * 100

def get_color(prob):
    if prob >= 70: return "#28a745"
    if prob >= 50: return "#ffc107"
    return "#dc3545"

def prever_1x2_avancado(h_atq, h_def, a_atq, a_def):
    l_casa = h_atq * a_def * 1.10 
    l_fora = a_atq * h_def * 0.90 
    total = l_casa + l_fora
    p_empate = 31.0 if total < 2.2 else 26.0
    sobra = 100 - p_empate
    p_casa = sobra * (l_casa / total) if total > 0 else sobra / 2
    p_fora = sobra * (l_fora / total) if total > 0 else sobra / 2
    return p_casa, p_empate, p_fora, total

@st.cache_data(ttl=3600) # Cache menor para evitar travar lista vazia
def carregar_jogos(d):
    try:
        url = f"https://{HOST}/api/v1/sport/football/scheduled-events/{d}"
        res = requests.get(url, headers=HEADERS, timeout=15)
        if res.status_code == 200:
            return res.json().get('events', [])
        return []
    except:
        return []

@st.cache_data(ttl=86400)
def buscar_estatisticas(t_id, s_id, h_id, a_id):
    try:
        url = f"https://{HOST}/api/v1/tournament/{t_id}/season/{s_id}/standings/total"
        res = requests.get(url, headers=HEADERS, timeout=12)
        if res.status_code == 200:
            rows = res.json().get('standings', [{}])[0].get('rows', [])
            h_atq, h_def, a_atq, a_def = 1.4, 1.2, 1.1, 1.3
            for r in rows:
                tid = r['team']['id']
                jogos = max(r.get('matches', 1), 1)
                if tid == h_id: h_atq, h_def = r.get('scoresFor', 0)/jogos, r.get('scoresAgainst', 0)/jogos
                if tid == a_id: a_atq, a_def = r.get('scoresFor', 0)/jogos, r.get('scoresAgainst', 0)/jogos
            return h_atq, h_def, a_atq, a_def
    except: pass
    return 1.4, 1.2, 1.1, 1.3

# --- INTERFACE ---
st.set_page_config(page_title="PROBET ANALISE v5.0", layout="wide", page_icon="⚽")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #e0e0e0; }
    .res-box { text-align: center; padding: 15px; border-radius: 8px; font-weight: bold; color: white; margin-bottom: 10px; font-size: 20px; }
    .metric-container { background-color: #1c2128; padding: 15px; border-radius: 10px; border: 1px solid #30363d; margin-top: 5px; }
    .metric-row { display: flex; justify-content: space-between; margin-bottom: 8px; align-items: center; border-bottom: 1px solid #2d333b; padding-bottom: 5px; }
    .metric-row:last-child { border-bottom: none; }
    </style>
    """, unsafe_allow_html=True)

st.title("⚽ PROBET ANALISE")

# --- FILTROS DE BUSCA ---
st.sidebar.header("⚙️ Configurações")
data_sel = st.sidebar.date_input("Data das Partidas", value=datetime.now())
data_str = data_sel.strftime('%Y-%m-%d')

with st.spinner(f"Buscando jogos para {data_str}..."):
    jogos = carregar_jogos(data_str)

if jogos:
    # 1. Menu de Ligas
    ligas = sorted(list(set([j['tournament']['name'] for j in jogos])))
    ligas_sel = st.multiselect("🏆 1. Selecione as Ligas", ligas)
    
    # Filtrar jogos pelas ligas selecionadas
    jogos_f = [j for j in jogos if j['tournament']['name'] in ligas_sel] if ligas_sel else jogos
    
    # 2. Menu de Partidas
    if jogos_f:
        opcoes_partidas = {}
        for j in jogos_f:
            hora = datetime.fromtimestamp(j.get('startTimestamp',
