import streamlit as st
import requests
import math
from datetime import datetime

# --- CONFIGURAÇÃO DA SUA CHAVE ---
API_KEY = "a19cf6b5fcmsh62790bdb0d293ddp131982jsn24158e88f703"
HOST = "sportapi7.p.rapidapi.com" # Voltei para o Host da SportAPI que combina com o resto do seu código

HEADERS = {
    "X-RapidAPI-Key": API_KEY,
    "X-RapidAPI-Host": HOST
}

# --- LÓGICA MATEMÁTICA ---
def calcular_poisson(media, alvo):
    if media <= 0: return 0
    prob_acumulada = 0
    for i in range(alvo + 1):
        prob_i = (math.exp(-media) * (media**i)) / math.factorial(i)
        prob_acumulada += prob_i
    return (1 - prob_acumulada) * 100

# --- INTERFACE ---
st.set_page_config(page_title="OLHEIROBET PRO", layout="wide")
st.title("⚽ OlheiroBet: Inteligência Esportiva")

# 1. Buscar Jogos do Dia
@st.cache_data(ttl=3600)
def carregar_jogos():
    try:
        # Esta URL abaixo é específica para o HOST "sportapi7.p.rapidapi.com"
        url = f"https://{HOST}/api/v1/sport/football/scheduled-events/{datetime.now().strftime('%Y-%m-%d')}"
        response = requests.get(url, headers=HEADERS)
        if response.status_code == 200:
            return response.json().get('events', [])
        else:
            return []
    except:
        return []

jogos = carregar_jogos()

if jogos:
    st.sidebar.header("⚙️ Configurações")
    todas_ligas = sorted(list(set([j['tournament']['name'] for j in jogos])))
    ligas_selecionadas = st.sidebar.multiselect("Filtrar por Liga:", todas_ligas, default=todas_ligas[:3])

    jogos_filtrados = [j for j in jogos if j['tournament']['name'] in ligas_selecionadas]

    if jogos_filtrados:
        lista_nomes = {f"{j['homeTeam']['name']} x {j['awayTeam']['name']}": j for j in jogos_filtrados}
        escolha = st.selectbox("🎯 Selecione a Partida:", list(lista_nomes.keys()))
        jogo_foco = lista_nomes[escolha]
        
        st.write("---")
        c1, cv, c2 = st.columns([2, 1, 2])
        c1.header(jogo_foco['homeTeam']['name'])
        cv.markdown("<h2 style='text-align: center;'>VS</h2>", unsafe_allow_html=True)
        c2.header(jogo_foco['awayTeam']['name'])

        if st.button("🔍 EXECUTAR ANÁLISE"):
            p_gols = calcular_poisson(2.75, 2)
            p_cantos = calcular_poisson(10.2, 9)

            col_g, col_c = st.columns(2)
            col_g.metric("Prob. Over 2.5 Gols", f"{p_gols:.1f}%")
            col_c.metric("Prob. Over 9.5 Cantos", f"{p_cantos:.1f}%")
    else:
        st.info("Selecione uma liga na barra lateral.")
else:
    st.error("Não foi possível carregar os jogos. Verifique se a API 'SportAPI' está assinada no seu RapidAPI.")









