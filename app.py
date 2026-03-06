import streamlit as st
import requests
import math
import random
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="PROBET ANALISE", layout="wide", page_icon="⚽")

# --- CONFIGURAÇÃO DA API ---
# Dica: Em produção, use st.secrets para esconder sua chave
API_KEY = "a19cf6b5fcmsh62790bdb0d293ddp131982jsn24158e88f703"
HOST = "sportapi7.p.rapidapi.com"
HEADERS = {"X-RapidAPI-Key": API_KEY, "X-RapidAPI-Host": HOST}

# --- FUNÇÕES DE CÁLCULO ---
def calcular_poisson(media, alvo):
    """Calcula a probabilidade de ocorrer MAIS que 'alvo' gols/eventos."""
    if media <= 0: return 0
    prob_acumulada = 0
    for i in range(int(alvo) + 1):
        # Fórmula: (e^-μ * μ^k) / k!
        prob_i = (math.exp(-media) * (media**i)) / math.factorial(i)
        prob_acumulada += prob_i
    return max(0, min(100, (1 - prob_acumulada) * 100))

def prever_1x2_evoluido(m_casa, m_fora):
    """Calcula 1X2 baseado na força relativa e uma constante de empate."""
    total = m_casa + m_fora
    p_empate = 25.0  # Base estatística média para futebol
    
    if total > 0:
        # Peso proporcional às médias de ataque
        fator_casa = m_casa / total
        fator_fora = m_fora / total
        
        p_casa = (100 - p_empate) * fator_casa
        p_fora = (100 - p_empate) * fator_fora
    else:
        p_casa = p_fora = 37.5
        
    return p_casa, p_empate, p_fora

@st.cache_data(ttl=86400)
def buscar_medias_reais(tournament_id, season_id, home_id, away_id):
    try:
        url = f"https://{HOST}/api/v1/tournament/{tournament_id}/season/{season_id}/standings/total"
        response = requests.get(url, headers=HEADERS, timeout=12)
        if response.status_code == 200:
            data = response.json()
            rows = data.get('standings', [{}])[0].get('rows', [])
            
            m_casa, m_fora = 1.4, 1.1 # Default caso não ache o time
            for row in rows:
                t_id = row['team']['id']
                jogos = row.get('matches', 1) or 1
                if t_id == home_id: m_casa = row.get('scoresFor', 0) / jogos
                if t_id == away_id: m_fora = row.get('scoresFor', 0) / jogos
            return round(m_casa, 2), round(m_fora, 2)
    except Exception:
        pass
    return 1.5, 1.2

def formatar_hora(timestamp):
    if not timestamp: return "--:--"
    return datetime.fromtimestamp(timestamp).strftime('%H:%M')

# --- ESTILIZAÇÃO CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #e0e0e0; }
    .metric-card { 
        background-color: #1c2128; 
        padding: 15px; 
        border-radius: 12px; 
        border: 1px solid #30363d;
        text-align: center;
    }
    .res-box { 
        padding: 15px; border-radius: 10px; font-weight: bold; 
        text-align: center; font-size: 20px; color: white;
    }
    .vs-divider { color: #ffc107; font-size: 35px; font-weight: bold; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- CABEÇALHO ---
st.title("⚽ PROBET ANALISE")
st.caption("Sistema Inteligente de Predição Estatística")

# --- FILTROS ---
with st.expander("🛠️ CONFIGURAÇÕES DE BUSCA", expanded=True):
    col_date, col_league = st.columns([1, 2])
    with col_date:
        data_sel = st.date_input("📅 Data das Partidas", value=datetime.now())
    
    @st.cache_data(ttl=3600)
    def carregar_jogos(data_str):
        try:
            url = f"https://{HOST}/api/v1/sport/football/scheduled-events/{data_str}"
            r = requests.get(url, headers=HEADERS, timeout=15)
            return r.json().get('events', []) if r.status_code == 200 else []
        except: return []

    jogos = carregar_jogos(data_sel.strftime('%Y-%m-%d'))
    
    with col_league:
        if jogos:
            todas_ligas = sorted(list(set([j['tournament']['name'] for j in jogos])))
            ligas_sel = st.multiselect("🏆 Selecione as Ligas", todas_ligas)
            jogos_f = [j for j in jogos if j['tournament']['name'] in ligas_sel] if ligas_sel else jogos
        else:
            st.warning("Nenhum jogo encontrado para esta data.")
            jogos_f = []

# --- SELEÇÃO DE JOGO ---
if jogos_
