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

def prever_1x2_avancado(h_atq, h_def, a_atq, a_def):
    l_casa = h_atq * a_def * 1.10 
    l_fora = a_atq * h_def * 0.90 
    total = l_casa + l_fora
    p_empate = 31.0 if total < 2.2 else 26.0
    sobra = 100 - p_empate
    p_casa = sobra * (l_casa / total) if total > 0 else sobra / 2
    p_fora = sobra * (l_fora / total) if total > 0 else sobra / 2
    return p_casa, p_empate, p_fora, total

@st.cache_data(ttl=600)
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
def buscar_estatisticas_completas(tournament_id, season_id, home_id, away_id):
    try:
        url = f"https://{HOST}/api/v1/tournament/{tournament_id}/season/{season_id}/standings/total"
        res = requests.get(url, headers=HEADERS, timeout=12)
        if res.status_code == 200:
            data = res.json().get('standings', [{}])
            if not data: return 1.4, 1.2, 1.1, 1.3
            rows = data[0].get('rows', [])
            h_atq, h_def, a_atq, a_def = 1.4, 1.2, 1.1, 1.3
            for row in rows:
                t_id = row['team']['id']
                jogos_t = max(row.get('matches', 1), 1)
                gp, gs = row.get('scoresFor', 0), row.get('scoresAgainst', 0)
                if t_id == home_id: h_atq, h_def = gp/jogos_t, gs/jogos_t
                if t_id == away_id: a_atq, a_def = gp/jogos_t, gs/jogos_t
            return h_atq, h_def, a_atq, a_def
    except: pass
    return 1.4, 1.2, 1.1, 1.3

def formatar_metric(label, prob):
    cor = "#dc3545" 
    if prob >= 70: cor = "#28a745"
    elif prob >= 50: cor = "#ffc107"
    estrela = "⭐" if prob >= 85 else ""
    return f"<div style='margin-bottom:8px;'><span style='color:#bbb; font-size:14px;'>{label}:</span> <span style='color:{cor}; font-weight:bold; font-size:18px;'>{prob:.1f}%</span> <span>{estrela}</span></div>"

# --- INTERFACE ---
st.set_page_config(page_title="PROBET ANALISE v5.0", layout="wide", page_icon="⚽")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #e0e0e0; }
    .res-box { text-align: center; padding: 15px; border-radius: 8px; font-weight: bold; color: white; margin-bottom: 10px; font-size: 20px; }
    .metric-card { background-color: #1c2128; padding: 15px; border-radius: 10px; border: 1px solid #30363d; min-height: 100px; }
    h1, h2, h3 { color: #ffc107 !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("⚽ PROBET ANALISE")

# --- BARRA LATERAL (FILTROS) ---
st.sidebar.header("⚙️ Configurações")
data_sel = st.sidebar.date_input("Data das Partidas", value=datetime.now())
data_str = data_sel.strftime('%Y-%m-%d')

with st.spinner(f"Carregando jogos de {data_str}..."):
    jogos = carregar_jogos(data_str)

if jogos:
    # 1. Filtro de Ligas
    todas_ligas = sorted(list(set([j['tournament']['name'] for j in jogos])))
    ligas_sel = st.multiselect("🏆 1. Selecione as Ligas", todas_ligas)
    
    # 2. Filtro de Jogos
    jogos_f = [j for j in jogos if j['tournament']['name'] in ligas_sel] if ligas_sel else jogos
    
    if jogos_f:
        lista_nomes = {f"[{datetime.fromtimestamp(j.get('startTimestamp', 0)).strftime('%H:%M')}] {j['homeTeam']['name']} x {j['awayTeam']['name']}": j for j in jogos_f}
        escolha = st.selectbox("🎯 2. Escolha uma partida:", list(lista_nomes.keys()))
        
        if st.button("🔍 GERAR RELATÓRIO PREDITIVO"):
            st.session_state.jogo_selecionado = lista_nomes[escolha]
            st.session_state.analise_pronta = True
    else:
        st.info("Nenhum jogo encontrado para as ligas selecionadas.")
else:
    st.error(f"Nenhum jogo retornado para {data_str}. Verifique se a chave API está ativa ou tente mudar a data.")

# --- RESULTADOS ---
if st.session_state.analise_pronta and st.session_state.jogo_selecionado:
    j = st.session_state.jogo_selecionado
    st.divider()
    
    id_h, id_a = j['homeTeam']['id'], j['awayTeam']['id']
    logo_h = f"https://api.sofascore.app/api/v1/team/{id_h}/image"
    logo_a = f"https://api.sofascore.app/api/v1/team/{id_a}/image"

    h_atq, h_def, a_atq, a_def = buscar_estatisticas_completas(j['tournament']['id'], j['season']['id'], id_h, id_a)
    p_c, p_e, p_f, m_t = prever_1x2_avancado(h_atq, h_def, a_atq, a_def)

    # Topo Visual
    c_l, c_m, c_r = st.columns([1, 3, 1])
    with c_l: st.image(logo_h, width=110)
    with c_m:
        st.markdown(f"<h1 style='text-align: center;'>{j['homeTeam']['name']} x {j['awayTeam']['name']}</h1>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center;'>{j['tournament']['name']} • {datetime.fromtimestamp(j.get('startTimestamp', 0)).strftime('%H:%M')}</p>", unsafe_allow_html=True)
    with c_r: st.image(logo_a, width=110)
    
    # 1X2
    v1, v2, v3 = st.columns(3)
    v1.markdown(f"<div class='res-box' style='background-color:#1f77b4;'>Casa: {p_c:.1f}%</div>", unsafe_allow_html=True)
    v2.markdown(f"<div class='res-box' style='background-color:#444;'>Empate: {p_e:.1f}%</div>", unsafe_allow_html=True)
    v3.markdown(f"<div class='res-box' style='background-color:#dc3545;'>Fora: {p_f:.1f}%</div>", unsafe_allow_html=True)

    # Detalhes (Gols, Cantos, Cartões)
    st.divider()
    m1, m2, m3 = st.columns(3)
    
    with m1:
        st.subheader("⚽ GOLS")
        html = formatar_metric('Over 1.5', calcular_poisson(m_t, 1)) + formatar_metric('Over 2.5', calcular_poisson(m_t, 2))
        st.markdown(f"<div class='metric-card'>{html}</div>", unsafe_allow_html=True)
    with m2:
        st.subheader("🚩 CANTOS")
        html = formatar_metric('Over 8.5', calcular_poisson(9.5, 8)) + formatar_metric('Over 10.5', calcular_poisson(9.5, 10))
        st.markdown(f"<div class='metric-card'>{html}</div>", unsafe_allow_html=True)
    with m3:
        st.subheader("🟨 CARTÕES")
        html = formatar_metric('Over 3.5', calcular_poisson(4.2, 3)) + formatar_metric('Over 4.5', calcular_poisson(4.2, 4))
        st.markdown(f"<div class='metric-card'>{html}</div>", unsafe_allow_html=True)
