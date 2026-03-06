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

# --- FUNÇÕES DE CÁLCULO ---
def calcular_poisson(media, alvo):
    if media <= 0: return 0
    prob_acumulada = 0
    for i in range(int(alvo) + 1):
        prob_i = (math.exp(-media) * (media**i)) / math.factorial(i)
        prob_acumulada += prob_i
    return (1 - prob_acumulada) * 100

def get_color(prob):
    if prob >= 70: return "#28a745" # Verde
    if prob >= 50: return "#ffc107" # Amarelo
    return "#dc3545" # Vermelho

def prever_1x2_avancado(h_atq, h_def, a_atq, a_def):
    lambda_casa = h_atq * a_def * 1.10 
    lambda_fora = a_atq * h_def * 0.90 
    total = lambda_casa + lambda_fora
    p_empate = 31.0 if total < 2.2 else 26.0
    sobra = 100 - p_empate
    p_casa = sobra * (lambda_casa / total) if total > 0 else sobra / 2
    p_fora = sobra * (lambda_fora / total) if total > 0 else sobra / 2
    return p_casa, p_empate, p_fora, total

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

# --- FILTROS ---
data_sel = st.date_input("📅 Data das Partidas", value=datetime.now())
data_str = data_sel.strftime('%Y-%m-%d')

@st.cache_data(ttl=600)
def carregar_jogos(d):
    try:
        res = requests.get(f"https://{HOST}/api/v1/sport/football/scheduled-events/{d}", headers=HEADERS, timeout=10)
        return res.json().get('events', []) if res.status_code == 200 else []
    except: return []

jogos = carregar_jogos(data_str)

if jogos:
    ligas = sorted(list(set([j['tournament']['name'] for j in jogos])))
    ligas_sel = st.multiselect("🏆 Selecione as Ligas", ligas)
    jogos_f = [j for j in jogos if j['tournament']['name'] in ligas_sel] if ligas_sel else jogos
    
    if jogos_f:
        lista = {f"[{datetime.fromtimestamp(j.get('startTimestamp', 0)).strftime('%H:%M')}] {j['homeTeam']['name']} x {j['awayTeam']['name']}": j for j in jogos_f}
        escolha = st.selectbox("🎯 Escolha uma partida:", list(lista.keys()))
        
        if st.button("🔍 GERAR RELATÓRIO PREDITIVO"):
            st.session_state.jogo_selecionado = lista[escolha]
            st.session_state.analise_pronta = True

# --- EXIBIÇÃO DE RESULTADOS ---
if st.session_state.analise_pronta and st.session_state.jogo_selecionado:
    j = st.session_state.jogo_selecionado
    st.divider()
    
    # IDs e Logos
    id_h, id_a = j['homeTeam']['id'], j['awayTeam']['id']
    logo_h = f"https://api.sofascore.app/api/v1/team/{id_h}/image"
    logo_a = f"https://api.sofascore.app/api/v1/team/{id_a}/image"

    h_atq, h_def, a_atq, a_def = buscar_estatisticas(j['tournament']['id'], j['season']['id'], id_h, id_a)
    p_c, p_e, p_f, m_t = prever_1x2_avancado(h_atq, h_def, a_atq, a_def)

    # Cabeçalho
    c_l1, c_mid, c_l2 = st.columns([1, 4, 1])
    with c_l1: st.image(logo_h, width=100)
    with c_mid:
        st.markdown(f"<h1 style='text-align: center; color:#ffc107;'>{j['homeTeam']['name']} vs {j['awayTeam']['name']}</h1>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center; font-size: 1.2rem;'>{j['tournament']['name']} • {datetime.fromtimestamp(j.get('startTimestamp', 0)).strftime('%H:%M')}</p>", unsafe_allow_html=True)
    with c_l2: st.image(logo_a, width=100)

    # Probabilidades 1X2
    v1, v2, v3 = st.columns(3)
    v1.markdown(f"<div class='res-box' style='background-color:#1f77b4;'>Casa: {p_c:.1f}%</div>", unsafe_allow_html=True)
    v2.markdown(f"<div class='res-box' style='background-color:#444;'>Empate: {p_e:.1f}%</div>", unsafe_allow_html=True)
    v3.markdown(f"<div class='res-box' style='background-color:#dc3545;'>Fora: {p_f:.1f}%</div>", unsafe_allow_html=True)

    # Mercados Detalhados
    st.divider()
    m1, m2, m3 = st.columns(3)

    def draw_box(title, items):
        st.markdown(f"### {title}")
        html = "<div class='metric-container'>"
        for label, prob in items:
            color = get_color(prob)
            star = "⭐" if prob >= 85 else ""
            html += f"""
            <div class='metric-row'>
                <span style='color:#bbb;'>{label}</span>
                <span style='color:{color}; font-weight:bold; font-size:20px;'>{prob:.1f}% {star}</span>
            </div>
            """
        html += "</div>"
        st.markdown(html, unsafe_allow_html=True)

    with m1:
        draw_box("⚽ GOLS", [("Over 1.5", calcular_poisson(m_t, 1)), ("Over 2.5", calcular_poisson(m_t, 2))])
    with m2:
        draw_box("🚩 CANTOS", [("Over 8.5", calcular_poisson(9.5, 8)), ("Over 10.5", calcular_poisson(9.5, 10))])
    with m3:
        draw_box("🟨 CARTÕES", [("Over 3.5", calcular_poisson(4.2, 3)), ("Over 4.5", calcular_poisson(4.2, 4))])

    st.caption("⭐ Probabilidade de Alta Confiança (+85%). Cálculos baseados em Poisson e Médias de Temporada.")

elif not jogos:
    st.info("Nenhum jogo encontrado para esta data.")
