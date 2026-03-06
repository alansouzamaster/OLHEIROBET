import streamlit as st
import requests
import math
from datetime import datetime, timedelta

# --- CONFIGURAÇÃO DA API ---
API_KEY = "cd10359c14msheda9060d2cb34cep176fa8jsn3c42386ffb98"
HOST = "sportapi7.p.rapidapi.com"
HEADERS = {"X-RapidAPI-Key": API_KEY, "X-RapidAPI-Host": HOST}

# --- FUNÇÕES DE APOIO ---
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

def formatar_metric(label, prob):
    cor = "#dc3545" if prob < 50 else ("#ffc107" if prob < 75 else "#28a745")
    estrela = "⭐" if prob >= 85 else ""
    # Retorna HTML puro para ser usado com markdown
    return f"""
    <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;'>
        <span style='color:#bbb; font-size:14px;'>{label}</span>
        <span style='color:{cor}; font-weight:bold; font-size:18px;'>{prob:.1f}% {estrela}</span>
    </div>
    """

# --- INTERFACE ---
st.set_page_config(page_title="PROBET v4.0", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    .res-box { text-align: center; padding: 15px; border-radius: 8px; font-weight: bold; color: white; margin-bottom: 10px; font-size: 20px; }
    .metric-card { background-color: #1c2128; padding: 15px; border-radius: 10px; border: 1px solid #30363d; min-height: 80px; }
    h1, h2, h3 { color: #ffc107 !important; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

st.title("⚽ PROBET ANALISE")

# --- FILTROS ---
data_sel = st.date_input("📅 Data das Partidas", value=datetime.now())
data_str = data_sel.strftime('%Y-%m-%d')

@st.cache_data(ttl=600)
def carregar_jogos(d):
    try:
        url = f"https://{HOST}/api/v1/sport/football/scheduled-events/{d}"
        res = requests.get(url, headers=HEADERS, timeout=10)
        return res.json().get('events', []) if res.status_code == 200 else []
    except: return []

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

# --- RESULTADOS (REMOVIDO ESCUDOS E CORRIGIDO HTML) ---
if st.session_state.get('analise_pronta') and st.session_state.get('jogo_selecionado'):
    j = st.session_state.jogo_selecionado
    st.divider()
    
    # Cabeçalho Centralizado (Sem colunas para escudos)
    st.markdown(f"<h1>{j['homeTeam']['name']} vs {j['awayTeam']['name']}</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; font-size: 16px; color: #888;'>{j['tournament']['name']} • {ajustar_horario(j.get('startTimestamp', 0))} (Brasília)</p>", unsafe_allow_html=True)

    # Probabilidades (Simuladas para exemplo, use sua função prever_1x2_avancado aqui)
    st.write("### Probabilidades 1X2")
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div class='res-box' style='background-color:#1f77b4;'>Casa: 65.0%</div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='res-box' style='background-color:#444;'>Empate: 26.0%</div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='res-box' style='background-color:#dc3545;'>Fora: 9.0%</div>", unsafe_allow_html=True)

    st.divider()
    
    # Mercados Secundários
    m1, m2, m3 = st.columns(3)
    
    # Média total fictícia para cálculo (Substitua pela sua lógica l_h + l_a)
    m_total = 2.8 

    with m1:
        st.markdown("### ⚽ GOLS", unsafe_allow_html=True)
        html_gols = formatar_metric("Over 1.5", calcular_poisson(m_total, 1))
        html_gols += formatar_metric("Over 2.5", calcular_poisson(m_total, 2))
        st.markdown(f"<div class='metric-card'>{html_gols}</div>", unsafe_allow_html=True)

    with m2:
        st.markdown("### 🚩 CANTOS", unsafe_allow_html=True)
        html_cantos = formatar_metric("Over 8.5", calcular_poisson(9.5, 8))
        html_cantos += formatar_metric("Over 10.5", calcular_poisson(9.5, 10))
        st.markdown(f"<div class='metric-card'>{html_cantos}</div>", unsafe_allow_html=True)

    with m3:
        st.markdown("### 🟨 CARTÕES", unsafe_allow_html=True)
        html_cards = formatar_metric("Over 3.5", calcular_poisson(4.2, 3))
        html_cards += formatar_metric("Over 4.5", calcular_poisson(4.2, 4))
        st.markdown(f"<div class='metric-card'>{html_cards}</div>", unsafe_allow_html=True)
