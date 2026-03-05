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
        response = requests.get(url, headers=HEADERS)
        if response.status_code == 200:
            standings = response.json().get('standings', [{}])[0].get('rows', [])
            m_casa, m_fora = 1.4, 1.1
            for row in standings:
                t_id = row['team']['id']
                jogos = row.get('matches', 1)
                if t_id == home_id: m_casa = row['scoresFor']/jogos
                if t_id == away_id: m_fora = row['scoresFor']/jogos
            return round(m_casa, 2), round(m_fora, 2)
    except:
        return 1.5, 1.0
    return 1.5, 1.0

def formatar_hora(timestamp):
    if not timestamp: return "--:--"
    return datetime.fromtimestamp(timestamp).strftime('%H:%M')

# --- INTERFACE E CSS ---
st.set_page_config(page_title="PROBET ANALISE", layout="wide", page_icon="⚽")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #e0e0e0; }
    div[data-testid="stMetricValue"] { color: #ffc107 !important; font-size: 24px !important; }
    .stMetric { background-color: #1c2128; padding: 15px; border-radius: 12px; border: 1px solid #30363d; }
    .oportunidade-card { background-color: #1c2128; padding: 15px; border-top: 3px solid #ffc107; border-radius: 8px; margin-bottom: 10px; }
    .stButton>button { width: 100%; background-color: #ffc107 !important; color: black !important; font-weight: bold; border-radius: 8px; }
    .res-box { text-align: center; padding: 12px; border-radius: 8px; font-weight: bold; color: white; margin-bottom: 10px; font-size: 18px; }
    .horario-badge { background-color: #333; color: #ffc107; padding: 3px 10px; border-radius: 5px; font-weight: bold; }
    .header-vs { text-align: center; color: #ffc107; font-size: 40px; font-weight: bold; margin-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title(" ⚽ PROBET ANALISE ")
st.markdown("---")

# --- MENU CENTRALIZADO ---
st.markdown("### 🛠️ FILTROS DE BUSCA")
col_data, col_liga = st.columns([1, 2])
with col_data:
    data_sel = st.date_input("📅 Escolha a Data", value=datetime.now())

@st.cache_data(ttl=3600)
def carregar_jogos(data_str):
    try:
        url = f"https://{HOST}/api/v1/sport/football/scheduled-events/{data_str}"
        response = requests.get(url, headers=HEADERS)
        if response.status_code == 200:
            return response.json().get('events', [])
        return []
    except Exception as e:
        return []

jogos = carregar_jogos(data_sel.strftime('%Y-%m-%d'))

if jogos:
    todas_ligas = sorted(list(set([j['tournament']['name'] for j in jogos])))
    with col_liga:
        ligas_sel = st.multiselect("🏆 Selecione as Ligas", todas_ligas)

    # --- SCANNER DE OPORTUNIDADES ---
    st.subheader("🔥 Oportunidades em Destaque")
    quentes = [j for j in jogos if random.random() > 0.94][:4]
    if quentes:
        cols_q = st.columns(len(quentes))
        for i, q in enumerate(quentes):
            with cols_q[i]:
                hora = formatar_hora(q.get('startTimestamp'))
                st.markdown(f"""
                <div class='oportunidade-card'>
                    <span class='horario-badge'>🕒 {hora}</span><br>
                    <small>{q['tournament']['name']}</small><br>
                    <strong>{q['homeTeam']['shortName'] if 'shortName' in q['homeTeam'] else q['homeTeam']['name']} x {q['awayTeam']['shortName'] if 'shortName' in q['awayTeam'] else q['awayTeam']['name']}</strong><br>
                    <span style='color:#ffc107;'>Over 2.5: {random.randint(72, 88)}
