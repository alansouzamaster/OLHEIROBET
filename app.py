import streamlit as st
import requests
import math
from datetime import datetime, timedelta

# --- CONFIGURAÇÃO DA API ---
# Verifique se o HOST é exatamente este no seu painel RapidAPI
API_KEY = "cd10359c14msheda9060d2cb34cep176fa8jsn3c42386ffb98"
HOST = "sportapi7.p.rapidapi.com"
HEADERS = {"X-RapidAPI-Key": API_KEY, "X-RapidAPI-Host": HOST}

# --- INICIALIZAÇÃO DE ESTADO ---
if 'analise_pronta' not in st.session_state:
    st.session_state.analise_pronta = False
if 'jogo_selecionado' not in st.session_state:
    st.session_state.jogo_selecionado = None

# --- FUNÇÕES ---
def ajustar_horario(timestamp):
    try:
        dt_utc = datetime.fromtimestamp(timestamp)
        dt_br = dt_utc - timedelta(hours=3)
        return dt_br.strftime('%H:%M')
    except:
        return "00:00"

def calcular_poisson(media, alvo):
    if media <= 0: return 0
    prob_acumulada = 0
    for i in range(int(alvo) + 1):
        prob_i = (math.exp(-media) * (media**i)) / math.factorial(i)
        prob_acumulada += prob_i
    return (1 - prob_acumulada) * 100

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

# --- INTERFACE ---
st.set_page_config(page_title="PROBET ANALISE", layout="wide")

st.title("⚽ PROBET ANALISE")

# --- BARRA LATERAL (FILTROS) ---
st.sidebar.header("⚙️ CONFIGURAÇÕES")
data_sel = st.sidebar.date_input("📅 Data das Partidas", value=datetime.now())
data_str = data_sel.strftime('%Y-%m-%d')

# --- BUSCA DE DADOS ---
with st.spinner(f'Buscando jogos para {data_str}...'):
    jogos = carregar_jogos(data_str)

if not jogos:
    st.warning(f"Nenhum jogo encontrado para {data_str}. Tente uma data futura ou verifique sua chave API.")
else:
    # 1. Extrair Ligas
    ligas = sorted(list(set([j['tournament']['name'] for j in jogos])))
    
    # 2. Menu de Ligas
    ligas_sel = st.multiselect("🏆 Selecione as Ligas", ligas)
    
    # 3. Filtrar Jogos
    jogos_f = [j for j in jogos if j['tournament']['name'] in ligas_sel] if ligas_sel else jogos
    
    if jogos_f:
        # 4. Criar dicionário para o Selectbox
        opcoes = {}
        for j in jogos_f:
            h_br = ajustar_horario(j.get('startTimestamp', 0))
            label = f"[{h_br}] {j['homeTeam']['name']} x {j['awayTeam']['name']}"
            opcoes[label] = j
            
        escolha = st.selectbox("🎯 Escolha uma partida:", list(opcoes.keys()))
        
        if st.button("🔍 GERAR RELATÓRIO PREDITIVO"):
            st.session_state.jogo_selecionado = opcoes[escolha]
            st.session_state.analise_pronta = True
    else:
        st.info("Escolha uma liga acima para listar os jogos.")

# --- EXIBIÇÃO DOS RESULTADOS ---
if st.session_state.analise_pronta and st.session_state.jogo_selecionado:
    j = st.session_state.jogo_selecionado
    st.divider()
    
    st.markdown(f"<h1 style='text-align: center; color:#ffc107;'>{j['homeTeam']['name']} vs {j['awayTeam']['name']}</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center;'>{j['tournament']['name']} • {ajustar_horario(j.get('startTimestamp', 0))} (Brasília)</p>", unsafe_allow_html=True)

    # Gráfico simples de probabilidades (Exemplo)
    c1, c2, c3 = st.columns(3)
    with c1: st.metric("Vitória Casa", "45%")
    with c2: st.metric("Empate", "25%")
    with c3: st.metric("Vitória Fora", "30%")
