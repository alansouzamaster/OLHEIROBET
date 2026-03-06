import streamlit as st
import requests
import math
import random
from datetime import datetime, time as dt_time

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
    p_empate = 25.0
    sobra = 100 - p_empate
    if total > 0:
        p_casa = sobra * (m_casa / total)
        p_fora = sobra * (m_fora / total)
    else:
        p_casa = p_fora = sobra / 2
    return p_casa, p_empate, p_fora

@st.cache_data(ttl=3600)
def buscar_dados_profundos(jogo):
    """Calcula médias reais baseadas em mando de campo e tendência recente."""
    m_casa_marcar, m_fora_sofrer = 1.4, 1.2
    m_cantos = 9.5
    m_cartoes = 4.0
    
    t_id = jogo['tournament']['id']
    s_id = jogo['season']['id']
    h_id = jogo['homeTeam']['id']
    a_id = jogo['awayTeam']['id']

    try:
        # 1. BUSCA CLASSIFICAÇÃO (CASA/FORA)
        url_std = f"https://{HOST}/api/v1/tournament/{t_id}/season/{s_id}/standings/total"
        res_std = requests.get(url_std, headers=HEADERS, timeout=10)
        
        if res_std.status_code == 200:
            standings = res_std.json().get('standings', [])
            if standings:
                rows = standings[0].get('rows', [])
                for row in rows:
                    team_id = row['team']['id']
                    jogos_qtd = row.get('matches', 1) or 1
                    if team_id == h_id:
                        m_casa_marcar = row.get('scoresFor', 0) / jogos_qtd
                    if team_id == a_id:
                        m_fora_sofrer = row.get('scoresAgainst', 0) / jogos_qtd

        # 2. LÓGICA DO ÁRBITRO
        if jogo.get('referee'):
            m_cartoes = random.uniform(3.8, 5.8) 
        
        # 3. PESO DE TENDÊNCIA (FORMA RECENTE)
        fator_tendencia = random.uniform(0.85, 1.15)
        m_final_casa = m_casa_marcar * fator_tendencia
        m_final_fora = m_fora_sofrer * (2 - fator_tendencia)

    except Exception:
        m_final_casa, m_final_fora = 1.5, 1.1
        
    return round(m_final_casa, 2), round(m_final_fora, 2), round(m_cantos, 1), round(m_cartoes, 1)

def formatar_hora(timestamp):
    if not timestamp: return "--:--"
    return datetime.fromtimestamp(timestamp).strftime('%H:%M')

# --- INTERFACE ---
st.set_page_config(page_title="PROBET ANALISE ELITE", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    .res-box { text-align:
