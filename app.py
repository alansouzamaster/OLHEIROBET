import streamlit as st
import requests
import math
from datetime import datetime, timedelta

# --- CONFIGURAÇÃO DA API ---
API_KEY = "3a5c2b926bmsh18b3c4624ec302bp1911efjsn84e2922978ff"
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

def get_color(prob):
    if prob >= 70: return "#28a745"
    if prob >= 50: return "#ffc107"
    return "#dc3545"

# --- INTERFACE ---
st.set_page_config(page_title="PROBET ANALISE v6.0", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #e0e0e0; }
    .res-box { text-align: center; padding: 15px; border-radius: 8px; font-weight: bold; color: white; margin-bottom: 10px; font-size: 20px; border: 1px solid #30363d; }
    .metric-container { background-color: #1c2128; padding: 15px; border-radius: 10px; border: 1px solid #30363d; margin-top: 5px; }
    .metric-row { display: flex; justify-content: space-between; margin-bottom: 8px; align-items: center; border-bottom: 1px solid #2d333b; padding-bottom: 5px; }
    .metric-row:last-child { border-bottom: none; }
    .main-title { text-align: center; color: #ffc107; margin-bottom: 0; }
    .sub-title { text-align: center; color: #888; margin-bottom: 20px; }
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
        opcoes = {}
        for j in jogos_f:
            h_br = ajustar_horario(j.get('startTimestamp', 0))
            label = f"[{h_br}] {j['homeTeam']['name']} x {j['awayTeam']['name']}"
            opcoes[label] = j
            
        escolha = st.selectbox("🎯 Escolha uma partida:", list(opcoes.keys()))
        
        if st.button("🔍 GERAR RELATÓRIO PREDITIVO"):
            st.session_state.jogo_selecionado = opcoes[escolha]
            st.session_state.analise_pronta = True

# --- EXIBIÇÃO (SEM ESCUDOS) ---
if st.session_state.analise_pronta and st.session_state.jogo_selecionado:
    j = st.session_state.jogo_selecionado
    st.divider()
    
    hora_jogo = ajustar_horario(j.get('startTimestamp', 0))
    
    # Cabeçalho Centralizado
    st.markdown(f"<h1 class='main-title'>{j['homeTeam']['name']} vs {j['awayTeam']['name']}</h1>", unsafe_allow_html=True)
    st.markdown(f"<p class='sub-title'>{j['tournament']['name']} • {hora_jogo} (Horário de Brasília)</p>", unsafe_allow_html=True)

    # Probabilidades Principais
    # (Nota: aqui você pode inserir sua lógica de buscar_estatisticas se desejar dados reais)
    p_casa, p_empate, p_fora = 45.0, 25.0, 30.0 # Valores exemplo
    m_t = 2.4 # Média exemplo
    
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div class='res-box' style='background-color:#1f77b4;'>Casa: {p_casa:.1f}%</div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='res-box' style='background-color:#444;'>Empate: {p_empate:.1f}%</div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='res-box' style='background-color:#dc3545;'>Fora: {p_fora:.1f}%</div>", unsafe_allow_html=True)

    # Mercados Secundários
    st.divider()
    col_g, col_c, col_k = st.columns(3)

    def render_bloco(titulo, itens):
        html = f"### {titulo}<div class='metric-container'>"
        for label, prob in itens:
            cor = get_color(prob)
            estrela = "⭐" if prob >= 85 else ""
            html += f"<div class='metric-row'><span>{label}</span><span style='color:{cor}; font-weight:bold;'>{prob:.1f}% {estrela}</span></div>"
        html += "</div>"
        return html

    with col_g:
        st.markdown(render_bloco("⚽ GOLS", [("Over 1.5", calcular_poisson(m_t, 1)), ("Over 2.5", calcular_poisson(m_t, 2))]), unsafe_allow_html=True)
    with col_c:
        st.markdown(render_bloco("🚩 CANTOS", [("Over 8.5", calcular_poisson(9.5, 8)), ("Over 10.5", calcular_poisson(9.5, 10))]), unsafe_allow_html=True)
    with col_k:
        st.markdown(render_bloco("🟨 CARTÕES", [("Over 3.5", calcular_poisson(4.2, 3)), ("Over 4.5", calcular_poisson(4.2, 4))]), unsafe_allow_html=True)
