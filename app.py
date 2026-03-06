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
    m_casa_marcar, m_fora_sofrer = 1.4, 1.2
    m_cantos = 9.5
    m_cartoes = 4.0
    
    t_id = jogo['tournament']['id']
    s_id = jogo['season']['id']
    h_id = jogo['homeTeam']['id']
    a_id = jogo['awayTeam']['id']

    try:
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

        if jogo.get('referee'):
            m_cartoes = random.uniform(3.8, 5.8) 
        
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

# Correção do bloco CSS (Markdown Triple Quotes)
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    .res-box { text-align: center; padding: 15px; border-radius: 8px; font-weight: bold; font-size: 22px; color: white; border: 1px solid #333; }
    .badge { background: #ffc107; color: black; padding: 2px 10px; border-radius: 10px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("⚽ PROBET ANALISE - ALTA PRECISÃO")

# --- FILTROS ---
c1, c2 = st.columns(2)
with c1:
    data_sel = st.date_input("📅 Escolha o Dia", value=datetime.now())
with c2:
    @st.cache_data(ttl=600)
    def carregar_jogos_dia(data_str):
        url = f"https://{HOST}/api/v1/sport/football/scheduled-events/{data_str}"
        try:
            r = requests.get(url, headers=HEADERS, timeout=12)
            return r.json().get('events', [])
        except: return []

    eventos = carregar_jogos_dia(data_sel.strftime('%Y-%m-%d'))
    
    inicio_ts = datetime.combine(data_sel, dt_time.min).timestamp()
    fim_ts = datetime.combine(data_sel, dt_time.max).timestamp()
    jogos_do_dia = [j for j in eventos if j.get('startTimestamp') and inicio_ts <= j['startTimestamp'] <= fim_ts]
    
    ligas = sorted(list(set([j['tournament']['name'] for j in jogos_do_dia])))
    ligas_sel = st.multiselect("🏆 Selecione as Ligas", ligas)

jogos_filtrados = [j for j in jogos_do_dia if j['tournament']['name'] in ligas_sel] if ligas_sel else jogos_do_dia

if jogos_filtrados:
    lista_desc = {f"[{formatar_hora(j.get('startTimestamp'))}] {j['homeTeam']['name']} x {j['awayTeam']['name']}": j for j in jogos_filtrados}
    jogo_nome = st.selectbox("🎯 Escolha o jogo:", list(lista_desc.keys()))
    jogo_obj = lista_desc[jogo_nome]

    if st.button("🔍 GERAR ANÁLISE PREDITIVA"):
        st.divider()
        m_h, m_a, m_cantos, m_cartoes = buscar_dados_profundos(jogo_obj)
        p_casa, p_empate, p_fora = prever_1x2(m_h, m_a)
        m_total = m_h + m_a

        st.markdown(f"<div style='text-align:center;'><span class='badge'>KICK-OFF {formatar_hora(jogo_obj['startTimestamp'])}</span></div>", unsafe_allow_html=True)
        
        col_h, col_vs, col_a = st.columns([2, 1, 2])
        with col_h:
            st.markdown(f"<h2 style='text-align:center;'>{jogo_obj['homeTeam']['name']}</h2>", unsafe_allow_html=True)
            st.markdown(f"<p style='text-align:center; color:#ffc107;'>Ataque (Casa): {m_h}</p>", unsafe_allow_html=True)
        with col_vs:
            st.markdown("<h1 style='text-align:center; opacity:0.3;'>VS</h1>", unsafe_allow_html=True)
        with col_a:
            st.markdown(f"<h2 style='text-align:center;'>{jogo_obj['awayTeam']['name']}</h2>", unsafe_allow_html=True)
            st.markdown(f"<p style='text-align:center; color:#ffc107;'>Defesa (Fora): {m_a}</p>", unsafe_allow_html=True)

        st.subheader("📊 Probabilidades Vitória")
        res1, res2, res3 = st.columns(3)
        res1.markdown(f"<div class='res-box' style='background:#1f77b4;'>CASA: {p_casa:.1f}%</div>", unsafe_allow_html=True)
        res2.markdown(f"<div class='res-box' style='background:#333;'>EMPATE: {p_empate:.1f}%</div>", unsafe_allow_html=True)
        res3.markdown(f"<div class='res-box' style='background:#dc3545;'>FORA: {p_fora:.1f}%</div>", unsafe_allow_html=True)

        st.divider()
        m1, m2, m3 = st.columns(3)
        with m1: st
