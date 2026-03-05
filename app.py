import streamlit as st
import requests
import math
import random
from datetime import datetime
import time
import plotly.graph_objects as go

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
def buscar_stats_completos(tournament_id, season_id, home_id, away_id):
    try:
        url = f"https://{HOST}/api/v1/tournament/{tournament_id}/season/{season_id}/standings/total"
        response = requests.get(url, headers=HEADERS)
        
        stats = {
            "home": {"gols_f": 1.5, "gols_s": 1.1, "vitorias": 50, "posse": 52},
            "away": {"gols_f": 1.2, "gols_s": 1.3, "vitorias": 40, "posse": 48}
        }
        
        if response.status_code == 200:
            standings = response.json().get('standings', [{}])[0].get('rows', [])
            for row in standings:
                t_id = row['team']['id']
                if t_id == home_id:
                    stats["home"] = {"gols_f": row['scoresFor']/row['matches'], "gols_s": row['scoresAgainst']/row['matches'], "win_rate": (row['wins']/row['matches'])*100}
                if t_id == away_id:
                    stats["away"] = {"gols_f": row['scoresFor']/row['matches'], "gols_s": row['scoresAgainst']/row['matches'], "win_rate": (row['wins']/row['matches'])*100}
        return stats
    except:
        return stats

def radar_comparativo(nome_h, stats_h, nome_a, stats_a):
    categories = ['Ataque (Gols)', 'Defesa (Gols Sofridos Inv.)', 'Aproveitamento %', 'Força Ofensiva']
    
    # Invertemos a defesa para que "mais alto" no gráfico seja melhor (menos gols sofridos)
    val_h = [stats_h['gols_f'], 3 - stats_h['gols_s'], stats_h['win_rate']/10, stats_h['gols_f']*1.2]
    val_a = [stats_a['gols_f'], 3 - stats_a['gols_s'], stats_a['win_rate']/10, stats_a['gols_f']*1.2]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=val_h, theta=categories, fill='toself', name=nome_h, line_color='#ffc107'))
    fig.add_trace(go.Scatterpolar(r=val_a, theta=categories, fill='toself', name=nome_a, line_color='#1f77b4'))

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=False), bgcolor="#1c2128"),
        showlegend=True, paper_bgcolor="#0e1117", font_color="white", height=400,
        margin=dict(l=80, r=80, t=20, b=20)
    )
    return fig

# --- INTERFACE ---
st.set_page_config(page_title="PROBET ANALISE", layout="wide", page_icon="⚽")
st.markdown("<style>.stApp { background-color: #0e1117; color: #e0e0e0; } .stMetric { background-color: #1c2128; padding: 15px; border-radius: 12px; border: 1px solid #30363d; } .res-box { text-align: center; padding: 10px; border-radius: 6px; font-weight: bold; color: white; }</style>", unsafe_allow_html=True)

st.title(" ⚽ PROBET ANALISE ")

# --- FILTROS ---
col_d, col_l = st.columns([1, 2])
data_sel = col_d.date_input("📅 Data", value=datetime.now())

@st.cache_data(ttl=3600)
def carregar_jogos(data_str):
    try:
        url = f"https://{HOST}/api/v1/sport/football/scheduled-events/{data_str}"
        res = requests.get(url, headers=HEADERS)
        return res.json().get('events', []) if res.status_code == 200 else []
    except: return []

jogos = carregar_jogos(data_sel.strftime('%Y-%m-%d'))

if jogos:
    todas_ligas = sorted(list(set([j['tournament']['name'] for j in jogos])))
    ligas_sel = col_l.multiselect("🏆 Ligas", todas_ligas)
    
    jogos_f = [j for j in jogos if j['tournament']['name'] in ligas_sel] if ligas_sel else jogos
    
    if jogos_f:
        lista = {f"[{datetime.fromtimestamp(j.get('startTimestamp', 0)).strftime('%H:%M')}] {j['homeTeam']['name']} x {j['awayTeam']['name']}": j for j in jogos_f}
        escolha = st.selectbox("🎯 Escolha a Partida:", list(lista.keys()))
        jogo = lista[escolha]
        
        if st.button("🔍 GERAR RELATÓRIO PREDITIVO COMPLETO"):
            with st.spinner('Processando estatísticas...'):
                s = buscar_stats_completos(jogo['tournament']['id'], jogo['season']['id'], jogo['homeTeam']['id'], jogo['awayTeam']['id'])
                m_gols = s['home']['gols_f'] + s['away']['gols_f']
                
                # --- LAYOUT DE RESULTADO ---
                st.markdown("### 📊 Comparativo de Força")
                c_radar, c_1x2 = st.columns([2, 1])
                
                with c_radar:
                    st.plotly_chart(radar_comparativo(jogo['homeTeam']['shortName'], s['home'], jogo['awayTeam']['shortName'], s['away']), use_container_width=True)
                
                with c_1x2:
                    p_c, p_e, p_f = prever_1x2(s['home']['gols_f'], s['away']['gols_f'])
                    st.markdown("<br><br>", unsafe_allow_html=True)
                    st.markdown(f"<div class='res-box' style='background-color:#ffc107; color:black;'>Casa: {p_c:.1f}%</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='res-box' style='background-color:#444;'>Empate: {p_e:.1f}%</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='res-box' style='background-color:#1f77b4;'>Fora: {p_f:.1f}%</div>", unsafe_allow_html=True)

                # --- MÉTRICAS ---
                st.markdown("---")
                m1, m2, m3 = st.columns(3)
                with m1:
                    st.subheader("⚽ Gols")
                    st.metric("Over 1.5", f"{calcular_poisson(m_gols, 1):.1f}%")
                    st.metric("Over 2.5", f"{calcular_poisson(m_gols, 2):.1f}%")
                with m2:
                    st.subheader("🚩 Cantos")
                    st.metric("Over 8.5", f"{calcular_poisson(9.2, 8):.1f}%")
                    st.metric("Over 10.5", f"{calcular_poisson(9.2, 10):.1f}%")
                with m3:
                    st.subheader("🟨 Cartões")
                    st.metric("Over 3.5", f"{calcular_poisson(4.5, 3):.1f}%")
                    st.metric("Juiz", jogo.get('referee', {}).get('name', 'Pendente'))
