import streamlit as st
import requests
import math
import time
from datetime import datetime, timedelta

# --- CONFIGURAÇÃO DA API ---
API_KEY = "3a5c2b926bmsh18b3c4624ec302bp1911efjsn84e2922978ff"
HOST = "sportapi7.p.rapidapi.com"
HEADERS = {"X-RapidAPI-Key": API_KEY, "X-RapidAPI-Host": HOST}

# --- ESTADO DA SESSÃO ---
if 'analise_pronta' not in st.session_state:
    st.session_state.analise_pronta = False
if 'jogos_cache' not in st.session_state:
    st.session_state.jogos_cache = []

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

def get_color(prob):
    if prob >= 70: return "#28a745"
    if prob >= 50: return "#ffc107"
    return "#dc3545"

# --- INTERFACE ---
st.set_page_config(page_title="PROBET v8.0", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #e0e0e0; }
    .res-box { text-align: center; padding: 15px; border-radius: 8px; font-weight: bold; color: white; margin-bottom: 10px; font-size: 20px; border: 1px solid #30363d; }
    .metric-container { background-color: #1c2128; padding: 15px; border-radius: 10px; border: 1px solid #30363d; margin-top: 5px; }
    .metric-row { display: flex; justify-content: space-between; margin-bottom: 8px; align-items: center; border-bottom: 1px solid #2d333b; padding-bottom: 5px; }
    </style>
    """, unsafe_allow_html=True)

st.title("⚽ PROBET ANALISE")

# --- BARRA LATERAL (FILTROS) ---
st.sidebar.header("📅 FILTRO PRINCIPAL")
data_sel = st.sidebar.date_input("Escolha o Dia", value=datetime.now(), key="data_input")
data_str = data_sel.strftime('%Y-%m-%d')

# RESET DE SEGURANÇA: Se a data mudar, limpa a análise da tela
if 'data_atual' not in st.session_state or st.session_state.data_atual != data_str:
    st.session_state.data_atual = data_str
    st.session_state.analise_pronta = False
    st.session_state.jogos_cache = []

# --- CARREGAMENTO COM BARRA DE PROGRESSO ---
if not st.session_state.jogos_cache:
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        status_text.text(f"Conectando à API para o dia {data_str}...")
        progress_bar.progress(25)
        
        url = f"https://{HOST}/api/v1/sport/football/scheduled-events/{data_str}"
        res = requests.get(url, headers=HEADERS, timeout=12)
        
        progress_bar.progress(75)
        
        if res.status_code == 200:
            st.session_state.jogos_cache = res.json().get('events', [])
            progress_bar.progress(100)
            time.sleep(0.5)
            progress_bar.empty()
            status_text.empty()
        else:
            st.error(f"Erro da API (Status {res.status_code}). Verifique sua chave.")
            progress_bar.empty()
    except Exception as e:
        st.error(f"Erro de conexão: {e}")
        progress_bar.empty()

# --- MENUS ---
jogos = st.session_state.jogos_cache

if jogos:
    ligas = sorted(list(set([j['tournament']['name'] for j in jogos])))
    ligas_sel = st.multiselect("🏆 1. Selecione as Ligas:", ligas)
    
    jogos_f = [j for j in jogos if j['tournament']['name'] in ligas_sel] if ligas_sel else jogos
    
    if jogos_f:
        opcoes = {}
        for j in jogos_f:
            h_br = ajustar_horario(j.get('startTimestamp', 0))
            label = f"[{h_br}] {j['homeTeam']['name']} x {j['awayTeam']['name']}"
            opcoes[label] = j
            
        escolha = st.selectbox("🎯 2. Escolha a Partida:", list(opcoes.keys()))
        
        if st.button("🔍 ANALISAR AGORA"):
            st.session_state.jogo_selecionado = opcoes[escolha]
            st.session_state.analise_pronta = True
    else:
        st.info("💡 Escolha uma liga para ver os jogos.")
else:
    st.warning(f"Nenhum jogo encontrado para {data_str}. Tente uma data futura.")

# --- RESULTADOS ---
if st.session_state.analise_pronta and st.session_state.jogo_selecionado:
    j = st.session_state.jogo_selecionado
    st.divider()
    
    h_jogo = ajustar_horario(j.get('startTimestamp', 0))
    st.markdown(f"<h1 style='text-align:center; color:#ffc107;'>{j['homeTeam']['name']} vs {j['awayTeam']['name']}</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align:center; color:#888;'>{j['tournament']['name']} • {h_jogo} (Horário de Brasília)</p>", unsafe_allow_html=True)

    # Exemplo de Probabilidades
    c1, c2, c3 = st.columns(3)
    c1.markdown("<div class='res-box' style='background-color:#1f77b4;'>Casa: 48.5%</div>", unsafe_allow_html=True)
    c2.markdown("<div class='res-box' style='background-color:#444;'>Empate: 22.1%</div>", unsafe_allow_html=True)
    c3.markdown("<div class='res-box' style='background-color:#dc3545;'>Fora: 29.4%</div>", unsafe_allow_html=True)

    st.divider()
    col_g, col_c, col_k = st.columns(3)

    def render_bloco(titulo, itens):
        html = f"### {titulo}<div class='metric-container'>"
        for label, prob in itens:
            cor = get_color(prob)
            html += f"<div class='metric-row'><span>{label}</span><span style='color:{cor}; font-weight:bold;'>{prob:.1f}%</span></div>"
        html += "</div>"
        return html

    # Usando média padrão 2.5 para o exemplo
    with col_g:
        st.markdown(render_bloco("⚽ GOLS", [("Over 1.5", calcular_poisson(2.5, 1)), ("Over 2.5", calcular_poisson(2.5, 2))]), unsafe_allow_html=True)
    with col_c:
        st.markdown(render_bloco("🚩 CANTOS", [("Over 8.5", calcular_poisson(9.5, 8)), ("Over 10.5", calcular_poisson(9.5, 10))]), unsafe_allow_html=True)
    with col_k:
        st.markdown(render_bloco("🟨 CARTÕES", [("Over 3.5", calcular_poisson(4.2, 3)), ("Over 4.5", calcular_poisson(4.2, 4))]), unsafe_allow_html=True)
