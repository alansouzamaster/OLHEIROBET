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

# --- FUNÇÕES ---
def ajustar_horario(timestamp):
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
    return p_casa, p_empate, p_fora, lambda_casa, lambda_fora

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
    <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; border-bottom: 1px solid #2d333b; padding-bottom: 5px;'>
        <span style='color:#bbb; font-size:14px;'>{label}</span>
        <span style='color:{cor}; font-weight:bold; font-size:18px;'>{prob:.1f}% {estrela}</span>
    </div>
    """

# --- INTERFACE ---
st.set_page_config(page_title="PROBET v3.5", layout="wide")
st.markdown("<style>.stApp { background-color: #0e1117; color: white; } .metric-card { background-color: #1c2128; padding: 15px; border-radius: 10px; border: 1px solid #30363d; }</style>", unsafe_allow_html=True)

st.title("⚽ PROBET ANALISE")

data_sel = st.date_input("📅 Data", value=datetime.now())
jogos = carregar_jogos(data_sel.strftime('%Y-%m-%d')) # (Função carregar_jogos omitida para brevidade, use a sua anterior)

# ... (Menu de seleção de ligas e jogos igual ao anterior) ...

if st.session_state.analise_pronta and st.session_state.jogo_selecionado:
    j = st.session_state.jogo_selecionado
    st.divider()
    
    # Cálculos
    h_atq, h_def, a_atq, a_def = buscar_stats(j['tournament']['id'], j['season']['id'], j['homeTeam']['id'], j['awayTeam']['id'])
    p_c, p_e, p_f, l_h, l_a = prever_1x2_avancado(h_atq, h_def, a_atq, a_def)
    m_total = l_h + l_a

    # Cabeçalho
    c_l, c_m, c_r = st.columns([1, 3, 1])
    c_l.image(f"https://www.sofascore.com/api/v1/team/{j['homeTeam']['id']}/image", width=100)
    c_m.markdown(f"<h1 style='text-align:center;'>{j['homeTeam']['name']} vs {j['awayTeam']['name']}</h1>", unsafe_allow_html=True)
    c_m.markdown(f"<p style='text-align:center;'>{ajustar_horario(j['startTimestamp'])} (Brasília)</p>", unsafe_allow_html=True)
    c_r.image(f"https://www.sofascore.com/api/v1/team/{j['awayTeam']['id']}/image", width=100)

    # Mercados Secundários (Aqui está a correção das duas métricas)
    st.write("### Análise de Mercados")
    m1, m2, m3 = st.columns(3)
    
    with m1:
        st.subheader("⚽ GOLS")
        # Unindo Over 1.5 e Over 2.5
        html_gols = formatar_metric("Over 1.5", calcular_poisson(m_total, 1))
        html_gols += formatar_metric("Over 2.5", calcular_poisson(m_total, 2))
        st.markdown(f"<div class='metric-card'>{html_gols}</div>", unsafe_allow_html=True)

    with m2:
        st.subheader("🚩 CANTOS")
        # Unindo Over 8.5 e Over 10.5
        html_cantos = formatar_metric("Over 8.5", calcular_poisson(9.5, 8))
        html_cantos += formatar_metric("Over 10.5", calcular_poisson(9.5, 10))
        st.markdown(f"<div class='metric-card'>{html_cantos}</div>", unsafe_allow_html=True)

    with m3:
        st.subheader("🟨 CARTÕES")
        # Unindo Over 3.5 e Over 4.5
        html_cards = formatar_metric("Over 3.5", calcular_poisson(4.2, 3))
        html_cards += formatar_metric("Over 4.5", calcular_poisson(4.2, 4))
        st.markdown(f"<div class='metric-card'>{html_cards}</div>", unsafe_allow_html=True)
