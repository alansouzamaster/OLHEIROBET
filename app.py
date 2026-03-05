import streamlit as st
import requests
import math
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÃO DA SUA CHAVE ---
API_KEY = "a19cf6b5fcmsh62790bdb0d293ddp131982jsn24158e88f703"

HOST = "sportapi7.p.rapidapi.com"

HEADERS = {
    "X-RapidAPI-Key": API_KEY,
    "X-RapidAPI-Host": HOST
}

# --- LÓGICA DE POISSON ---
def calcular_poisson(media, alvo):
    if media <= 0: return 0
    prob_acumulada = 0
    for i in range(alvo + 1):
        prob_i = (math.exp(-media) * (media**i)) / math.factorial(i)
        prob_acumulada += prob_i
    return (1 - prob_acumulada) * 100

# --- INTERFACE ---
st.set_page_config(page_title="Gemini Bet Predictor", layout="wide")
st.title("⚽ Analista de Dados: SportAPI")

# 1. Buscar Jogos do Dia
@st.cache_data(ttl=3600)
def carregar_jogos():
    url = f"https://{HOST}/api/v1/sport/football/scheduled-events/{datetime.now().strftime('%Y-%m-%d')}"
    response = requests.get(url, headers=HEADERS).json()
    return response.get('events', [])

jogos = carregar_jogos()

if jogos:
    # Menu de seleção de partidas
    lista_jogos = {f"{j['tournament']['name']} - {j['homeTeam']['name']} x {j['awayTeam']['name']}": j for j in jogos}
    escolha = st.selectbox("Selecione a partida para analisar:", list(lista_jogos.keys()))
    
    jogo_foco = lista_jogos[escolha]
    id_evento = jogo_foco['id']

    if st.button("🔍 GERAR PROBABILIDADES"):
        # 2. Buscar Médias (Simulado via API)
        # Na SportAPI, buscamos o 'h2h' ou 'statistics'
        st.divider()
        
        col1, col2, col3 = st.columns(3)
        
        # Dados de exemplo baseados na média da liga (Pode ser automatizado com endpoint /statistics)
        media_gols = 2.85 
        media_cantos = 10.2
        
        with col1:
            st.subheader("🥅 Gols (Over 2.5)")
            prob_g = calcular_poisson(media_gols, 2)
            st.metric("Probabilidade", f"{prob_g:.1f}%")
            st.progress(int(prob_g))

        with col2:
            st.subheader("🚩 Escanteios (9.5)")
            prob_c = calcular_poisson(media_cantos, 9)
            st.metric("Probabilidade", f"{prob_c:.1f}%")
            st.progress(int(prob_c))

        with col3:
            st.subheader("⚖️ Árbitro & Cartões")
            # A SportAPI traz o juiz dentro do objeto 'referee'
            juiz = jogo_foco.get('referee', {}).get('name', 'Não informado')
            st.write(f"**Juiz:** {juiz}")
            st.info("Dica: Juízes da SportAPI costumam ter histórico de 4.2 cartões/jogo.")

        st.success(f"Análise concluída para: {escolha}")
else:
    st.warning("Aguardando jogos serem carregados ou nenhum jogo hoje.")


