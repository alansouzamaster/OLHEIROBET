import streamlit as st
import requests
import math
import random
from datetime import datetime
import time

# --- CONFIGURAÇÃO DA API ---
API_KEY = "a19cf6b5fcmsh62790bdb0d293ddp131982jsn24158e88f703"
HOST = "sportapi7.p.rapidapi.com"
HEADERS = {"X-RapidAPI-Key": API_KEY, "X-RapidAPI-Host": HOST}

# --- FUNÇÕES DE CÁLCULO ---
def calcular_poisson(media, alvo):
    if media <= 0: return 0
    prob_acumulada = 0
    for i in range(int(alvo) + 1):
        prob_i = (math.exp(-media) * (media**i)) / math.factorial(i)
        prob_acumulada += prob_i
    return (1 - prob_acumulada) * 100

def prever_1x2(m_casa, m_fora):
    total = m_casa + m_fora
    p_empate = 26.0
    sobra = 100 - p_empate
    if total > 0:
        p_casa = sobra * (m_casa / total)
        p_fora = sobra * (m_fora / total)
    else:
        p_casa = p_fora = sobra / 2
    return p_casa, p_empate, p_fora

@st.cache_data(ttl=86400)
def buscar_medias_reais(tournament_id, season_id, home_id, away_id):
    try:
        url = f"https://{HOST}/api/v1/tournament/{tournament_id}/season/{season_id}/standings/total"
        response = requests.get(url, headers=HEADERS, timeout=12)
        if response.status_code == 200:
            data = response.json()
            standings_list = data.get('standings', [])
            if not standings_list: return 1.5, 1.0
            rows = standings_list[0].get('rows', [])
            m_casa, m_fora = 1.4, 1.1
            for row in rows:
                t_id = row['team']['id']
                jogos = row.get('matches', 1) or 1
                if t_id == home_id: m_casa = row.get('scoresFor', 0)/jogos
                if t_id == away_id: m_fora = row.get('scoresFor', 0)/jogos
            return round(m_casa, 2), round(m_fora, 2)
    except:
        return 1.5, 1.0
    return 1.5, 1.0

def formatar_hora(timestamp):
    if not timestamp: return "--:--"
    return datetime.fromtimestamp(timestamp).strftime('%H:%M')

def formatar_data_br(data_obj):
    return data_obj.strftime('%d/%m/%Y')

# --- INTERFACE E CSS AVANÇADO ---
st.set_page_config(page_title="PROBET ANALISE PRO", layout="wide", page_icon="⚽")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
    
    html, body, [class*="st-"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #0b0e14; color: #ffffff; }
    
    /* Progress Bar Customizada */
    .stProgress > div > div > div > div { background-image: linear-gradient(to right, #ffc107 , #ff9800); }
    
    /* Cards Estilo Glassmorphism */
    .oportunidade-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 20px;
        border-radius: 15px;
        margin-bottom: 15px;
        transition: all 0.3s ease;
    }
    .oportunidade-card:hover {
        background: rgba(255, 255, 255, 0.08);
        transform: translateY(-5px);
        border-color: #ffc107;
    }
    
    /* Badge de Horário */
    .horario-badge {
        background: #ffc107;
        color: #000;
        padding: 4px 12px;
        border-radius: 6px;
        font-weight: 900;
        font-size: 12px;
        text-transform: uppercase;
    }
    
    /* Box de Probabilidade */
    .res-box-v2 {
        background: #161b22;
        padding: 15px;
        border-radius: 12px;
        text-align: center;
        border-bottom: 4px solid #333;
    }
    
    /* Títulos */
    .main-title {
        background: linear-gradient(90deg, #ffc107, #ffffff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 900;
        font-size: 3rem;
        text-align: center;
        margin-bottom: 0;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h1 class='main-title'>PROBET ANALISE PRO</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #888; margin-bottom: 30px;'>SISTEMA DE INTELIGÊNCIA PREDITIVA ESPORTIVA</p>", unsafe_allow_html=True)

# --- SIDEBAR / FILTROS ---
with st.sidebar:
    st.markdown("### 🛠️ FILTROS DE ELITE")
    data_sel = st.date_input("📅 Data da Rodada", value=datetime.now())
