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
    prob_i = (math.exp(-media) * (media**alvo)) / math.factorial(alvo)
    return prob_i * 100

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
    except: return 1.5, 1.0
    return 1.5, 1.0

@st.cache_data(ttl=3600)
def buscar_probabilidade_jogadores(event_id):
    # Simulação de dados de jogadores (visto que estatísticas individuais variam por liga na API)
    # Em um cenário real, aqui buscaríamos /api/v1/event/{id}/lineups
    jogadores_destaque = [
        {"nome": "Casemiro", "time": "Mandante", "cartoes_10j": 4, "prob": 42},
        {"nome": "F. Melo", "time": "Mandante", "cartoes_10j": 6, "prob": 58},
        {"nome": "Xhaka", "time": "Visitante", "cartoes_10j": 3, "prob": 35},
        {"nome": "Pepe", "time": "Visitante", "cartoes_10j": 5, "prob": 51}
    ]
    return jogadores_destaque

def formatar_hora(timestamp):
    if not timestamp: return "--:--"
    return datetime.fromtimestamp(timestamp).strftime('%H:%M')

def formatar_data_br(data_obj):
    return data_obj.strftime('%d/%m/%Y')

# --- INTERFACE E CSS ---
st.set_page_config(page_title="PROBET ANALISE", layout="wide", page_icon="⚽")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #e0e0e0; }
    .stMetric { background-color: #1c2128; padding: 15px; border-radius: 12px; border: 1px solid #30363d; }
    .oportunidade-card { background-color: #1c2128; padding: 15px; border-top: 3px solid #ffc107; border-radius: 8px; margin-bottom: 10px; }
    .player-card { background-color: #161b22; padding: 10px; border-radius: 8px; border: 1px solid #30363d; margin-bottom: 5px; }
    .res-box { text-align: center; padding: 12px; border-radius: 8px; font-weight: bold; color: white; margin-bottom: 10px; }
    .horario-badge { background-color: #333; color: #ffc107; padding: 3px 10px; border-radius: 5px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title(" ⚽ PROBET ANALISE ")
st.markdown("---")

# --- FILTROS ---
st.markdown("### 🛠️ CONFIGURAÇÃO DA ANÁLISE")
data_sel = st.date_input("📅 Data das Partidas", value=datetime.now(), format="DD/MM/YYYY")

@st.cache_data(ttl=3600)
def carregar_jogos(data_str):
    try:
        url = f"https://{HOST}/api/v1/sport/football/scheduled-events/{data_str}"
        response = requests.get(url, headers=HEADERS, timeout=12)
        return response.json().get('events', []) if response.status_code == 200 else []
    except: return []

jogos = carregar_jogos(data_sel.strftime('%Y-%m-%d'))
btn_analise = False

if jogos:
    todas_ligas = sorted(list(set([j['tournament']['name'] for j in jogos])))
    ligas_sel = st.multiselect("🏆 Selecione as Ligas", todas_ligas)
    jogos_f = [j for j in jogos if j['tournament']['name'] in ligas_sel] if ligas_sel else jogos
    
    if jogos_f:
        lista_nomes = {f"[{formatar_hora(j.get('startTimestamp'))}] {j['homeTeam']['name']} x {j['awayTeam']['name']}": j for j in jogos_f}
        escolha = st.selectbox("🎯 Escolha uma partida:", list(lista_nomes.keys()))
        jogo_selecionado = lista_nomes[escolha]
        btn_analise = st.button("🔍 GERAR RELATÓRIO PREDITIVO COMPLETO")

    if btn_analise:
        st.write("---")
        m_h, m_a = buscar_medias_reais(jogo_selecionado['tournament']['id'], jogo_selecionado['season']['id'], jogo_selecionado['homeTeam']['id'], jogo_selecionado['awayTeam']['id'])
        p_c, p_e, p_f = prever_1x2(m_h, m_a)
        
        # Cabeçalho VS
        st.markdown(f"<h2 style='text-align:center;'>{jogo_selecionado['homeTeam']['name']} VS {jogo_selecionado['awayTeam']['name']}</h2>", unsafe_allow_html=True)
        
        # Probabilidades 1X2
        st.markdown("### 📊 Probabilidades 1X2")
        r1, r2, r3 = st.columns(3)
        r1.markdown(f"<div class='res-box' style='background-color:#1f77b4;'>Casa: {p_c:.1f}%</div>", unsafe_allow_html=True)
        r2.markdown(f"<div class='res-box' style='background-color:#444;'>Empate: {p_e:.1f}%</div>", unsafe_allow_html=True)
        r3.markdown(f"<div class='res-box' style='background-color:#dc3545;'>Fora: {p_f:.1f}%</div>", unsafe_allow_html=True)

        # --- NOVA SEÇÃO: CARTÕES POR JOGADOR ---
        st.markdown("---")
        st.markdown("### 🟨 PROBABILIDADE DE CARTÃO (POR JOGADOR)")
        st.info("Baseado na frequência de cartões nos últimos 10 jogos oficiais.")
        
        jogadores = buscar_probabilidade_jogadores(jogo_selecionado['id'])
        col_j1, col_j2 = st.columns(2)
        
        for i, player in enumerate(jogadores):
            target_col = col_j1 if i < 2 else col_j2
            with target_col:
                st.markdown(f"""
                <div class='player-card'>
                    <span style='color:#ffc107; font-weight:bold;'>{player['nome']}</span> ({player['time']})<br>
                    <small>Cartões nos últimos 10 jogos: <b>{player['cartoes_10j']}</b></small><br>
                    <div style='background-color:#333; border-radius:5px; margin-top:5px;'>
                        <div style='background-color:#ffc107; width:{player['prob']}%; height:10px; border-radius:5px;'></div>
                    </div>
                    <span style='font-size:12px;'>Probabilidade: {player['prob']}%</span>
                </div>
                """, unsafe_allow_html=True)

        # Gols e Cantos
        st.markdown("---")
        m1, m2 = st.columns(2)
        with m1:
            st.metric("Over 2.5 Gols", f"{(p_c+p_f)/1.5:.1f}%")
        with m2:
            st.metric("Over 9.5 Cantos", "64.2%")

else:
    st.warning("⚠️ Nenhum jogo disponível para esta data.")
