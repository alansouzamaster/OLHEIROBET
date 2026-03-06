import streamlit as st
import requests
import math
from datetime import datetime, timedelta

# --- CONFIGURAÇÃO DA API ---
API_KEY = "cd10359c14msheda9060d2cb34cep176fa8jsn3c42386ffb98"
HOST = "sportapi7.p.rapidapi.com"
HEADERS = {"X-RapidAPI-Key": API_KEY, "X-RapidAPI-Host": HOST}

# --- INICIALIZAÇÃO DE ESTADO ---
if 'analise_pronta' not in st.session_state:
    st.session_state.analise_pronta = False
    st.session_state.jogo_selecionado = None

# --- FUNÇÕES DE APOIO ---
def ajustar_horario(timestamp):
    # Converte UTC para Horário de Brasília (UTC-3)
    dt_utc = datetime.fromtimestamp(timestamp)
    dt_br = dt_utc - timedelta(hours=3)
    return dt_br.strftime('%H:%M')

def calcular_poisson(media, alvo):
    if media <= 0: return 0
    prob_acumulada = 0
    for i in range(int(alvo) + 1):
        prob_i = (math.exp(-media) * (media**i)) / math.factorial(i)
        prob_acumulada += prob_i
    return (1 - prob_acumulada) * 100

def prever_1x2_avancado(h_atq, h_def, a_atq, a_def):
    lambda_casa = h_atq * a_def * 1.10 
    lambda_fora = a_atq * h_def * 0.90 
    total = lambda_casa + lambda_fora
    p_empate = 31.0 if total < 2.2 else 26.0
    sobra = 100 - p_empate
    p_casa = sobra * (lambda_casa / total) if total > 0 else sobra/2
    p_fora = sobra * (lambda_fora / total) if total > 0 else sobra/2
    return p_casa, p_empate, p_fora, lambda_casa + lambda_fora

@st.cache_data(ttl=600)
def carregar_jogos(d):
    try:
        url = f"https://{HOST}/api/v1/sport/football/scheduled-events/{d}"
        res = requests.get(url, headers=HEADERS, timeout=12)
        return res.json().get('events', []) if res.status_code == 200 else []
    except: return []

@st.cache_data(ttl=86400)
def buscar_stats(t_id, s_id, h_id, a_id):
    try:
        url = f"https://{HOST}/api/v1/tournament/{t_id}/season/{s_id}/standings/total"
        res = requests.get(url, headers=HEADERS, timeout=12)
        if res.status_code == 200:
            data = res.json().get('standings', [{}])[0].get('rows', [])
            h_atq = h_def = a_atq = a_def = 1.4
            for row in data:
                tid = row['team']['id']
                m = max(row.get('matches', 1), 1)
                if tid == h_id: h_atq, h_def = row['scoresFor']/m, row['scoresAgainst']/m
                if tid == a_id: a_atq, a_def = row['scoresFor']/m, row['scoresAgainst']/m
            return h_atq, h_def, a_atq, a_def
    except: pass
    return 1.4, 1.2, 1.1, 1.3

def formatar_metric(label, prob):
    cor = "#dc3545" if prob < 50 else ("#ffc107" if prob < 75 else "#28a745")
    estrela = "⭐" if prob >= 85 else ""
    return f"""
    <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; border-bottom: 1px solid #2d333b; padding-bottom: 5px;'>
        <span style='color:#bbb; font-size:14px;'>{label}</span>
        <span style='color:{cor}; font-weight:bold; font-size:18px;'>{prob:.1f}% {estrela}</span>
    </div>
    """

# --- INTERFACE ---
st.set_page_config(page_title="PROBET v3.8", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    .res-box { text-align: center; padding: 15px; border-radius: 8px; font-weight: bold; color: white; margin-bottom: 10px; font-size: 20px; }
    .metric-card { background-color: #1c2128; padding: 15px; border-radius: 10px; border: 1px solid #30363d; }
    h1, h2, h3 { color: #ffc107 !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("⚽ PROBET ANALISE")

# --- FILTROS ---
data_sel = st.date_input("📅 Data das Partidas", value=datetime.now())
data_str = data_sel.strftime('%Y-%m-%d')

jogos = carregar_jogos(data_str)

if jogos:
    ligas = sorted(list(set([j['tournament']['name'] for j in jogos])))
    ligas_sel = st.multiselect("🏆 Selecione as Ligas", ligas)
    jogos_f = [j for j in jogos if j['tournament']['name'] in ligas_sel] if ligas_sel else jogos
    
    if jogos_f:
        opcoes = {f"[{ajustar_horario(j.get('startTimestamp', 0))}] {j['homeTeam']['name']} x {j['awayTeam']['name']}": j for j in jogos_f}
        escolha = st.selectbox("🎯 Escolha uma partida:", list(opcoes.keys()))
        
        if st.button("🔍 GERAR RELATÓRIO PREDITIVO"):
            st.session_state.jogo_selecionado = opcoes[escolha]
            st.session_state.analise_pronta = True

# --- EXIBIÇÃO ---
if st.session_state.analise_pronta and st.session_state.jogo_selecionado:
    j = st.session_state.jogo_selecionado
    st.divider()
    
    # Processamento de Dados
    h_atq, h_def, a_atq, a_def = buscar_stats(j['tournament']['id'], j['season']['id'], j['homeTeam']['id'], j['awayTeam']['id'])
    p_c, p_e, p_f, m_total = prever_1x2_avancado(h_atq, h_def, a_atq, a_def)

    # Cabeçalho
    c_l, c_m, c_r = st.columns([1, 3, 1])
    with c_l: st.image(f"https://www.sofascore.com/api/v1/team/{j['homeTeam']['id']}/image", width=100)
    with c_m:
        st.markdown(f"<h1 style='text-align:center;'>{j['homeTeam']['name']} vs {j['awayTeam']['name']}</h1>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align:center; font-size:18px;'>{j['tournament']['name']} • {ajustar_horario(j.get('startTimestamp', 0))} (Brasília)</p>", unsafe_allow_html=True)
    with c_r: st.image(f"https://www.sofascore.com/api/v1/team/{j['awayTeam']['id']}/image", width=100)

    # Vitórias
    st.write("### Probabilidades 1X2")
    v1, v2, v3 = st.columns(3)
    v1.markdown(f"<div class='res-box' style='background-color:#1f77b4;'>Casa: {p_c:.1f}%</div>", unsafe_allow_html=True)
    v2.markdown(f"<div class='res-box' style='background-color:#444;'>Empate: {p_e:.1f}%</div>", unsafe_allow_html=True)
    v3.markdown(f"<div class='res-box' style='background-color:#dc3545;'>Fora: {p_f:.1f}%</div>", unsafe_allow_html=True)

    # Métricas Duplas por Mercado
    st.divider()
    m1, m2, m3 = st.columns(3)
    
    with m1:
        st.subheader("⚽ GOLS")
        html = formatar_metric("Over 1.5", calcular_poisson(m_total, 1))
        html += formatar_metric("Over 2.5", calcular_poisson(m_total, 2))
        st.markdown(f"<div class='metric-card'>{html}</div>", unsafe_allow_html=True)

    with m2:
        st.subheader("🚩 CANTOS")
        html = formatar_metric("Over 8.5", calcular_poisson(9.5, 8))
        html += formatar_metric("Over 10.5", calcular_poisson(9.5, 10))
        st.markdown(f"<div class='metric-card'>{html}</div>", unsafe_allow_html=True)

    with m3:
        st.subheader("🟨 CARTÕES")
        html = formatar_metric("Over 3.5", calcular_poisson(4.2, 3))
        html += formatar_metric("Over 4.5", calcular_poisson(4.2, 4))
        st.markdown(f"<div class='metric-card'>{html}</div>", unsafe_allow_html=True)

elif not jogos:
    st.info("Nenhum jogo encontrado para a data selecionada.")
