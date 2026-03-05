import streamlit as st
import requests
import math
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÃO DA SUA CHAVE ---
# Lembre-se de manter as aspas e não deixar espaços extras
API_KEY ="a19cf6b5fcmsh62790bdb0d293ddp131982jsn24158e88f703"


HOST = "sportspage-feeds.p.rapidapi.com"


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
st.title("⚽ OlheiroBet:")

# 1. Buscar Jogos do Dia
@st.cache_data(ttl=3600)
def carregar_jogos():
    try:
        url = f"https://{HOST}/api/v1/sport/football/scheduled-events/{datetime.now().strftime('%Y-%m-%d')}"
        response = requests.get(url, headers=HEADERS).json()
        return response.get('events', [])
    except:
        return []

jogos = carregar_jogos()

if jogos:
    # --- FILTRO LATERAL DE LIGAS ---
    st.sidebar.header("⚙️ Configurações")
    todas_ligas = sorted(list(set([j['tournament']['name'] for j in jogos])))
    ligas_selecionadas = st.sidebar.multiselect("Filtrar por Liga:", todas_ligas, default=todas_ligas[:3])

    # Filtrar jogos pelas ligas escolhidas
    jogos_filtrados = [j for j in jogos if j['tournament']['name'] in ligas_selecionadas]

    if jogos_filtrados:
        lista_nomes = {f"{j['homeTeam']['name']} x {j['awayTeam']['name']}": j for j in jogos_filtrados}
        escolha = st.selectbox("🎯 Selecione a Partida:", list(lista_nomes.keys()))
        
        jogo_foco = lista_nomes[escolha]
        
        st.write("---")
        
        # --- CABEÇALHO DOS TIMES ---
        c_time1, c_vs, c_time2 = st.columns([2, 1, 2])
        with c_time1:
            st.markdown(f"<h2 style='text-align: center;'>{jogo_foco['homeTeam']['name']}</h2>", unsafe_allow_html=True)
        with c_vs:
            st.markdown("<h2 style='text-align: center; color: gray;'>VS</h2>", unsafe_allow_html=True)
        with c_time2:
            st.markdown(f"<h2 style='text-align: center;'>{jogo_foco['awayTeam']['name']}</h2>", unsafe_allow_html=True)

        if st.button("🔍 EXECUTAR ANÁLISE"):
            # Médias baseadas na força dos times (Simulado)
            m_gols = 2.75
            m_cantos = 10.2
            
            p_gols = calcular_poisson(m_gols, 2)
            p_cantos = calcular_poisson(m_cantos, 9)

            st.write("### 📊 Resultado da Análise")
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Prob. Over 2.5 Gols", f"{p_gols:.1f}%")
                if p_gols > 70: st.success("🔥 Forte tendência de Gols")
                
            with col2:
                st.metric("Prob. Over 9.5 Cantos", f"{p_cantos:.1f}%")
                if p_cantos > 75: st.success("🚩 Muita chance de Cantos")

            with col3:
                juiz = jogo_foco.get('referee', {}).get('name', 'Pendente')
                st.write("**Árbitro da Partida:**")
                st.info(f"⚖️ {juiz}")
                
            st.write("---")
            st.caption("Aviso: As probabilidades são baseadas em modelos matemáticos. Jogue com responsabilidade.")
    else:
        st.info("Selecione uma ou mais ligas na barra lateral para listar os jogos.")
else:
    st.error("Não foi possível carregar os jogos. Verifique sua chave API ou o limite de créditos.")









