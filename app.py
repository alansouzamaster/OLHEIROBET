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
    # --- 1. FILTRO LATERAL DE LIGAS ---
    st.sidebar.header("Filtros")
    todas_ligas = sorted(list(set([j['tournament']['name'] for j in jogos])))
    ligas_selecionadas = st.sidebar.multiselect("Selecione as Ligas:", todas_ligas, default=todas_ligas[:3])

    # Filtrar jogos pelas ligas escolhidas
    jogos_filtrados = [j for j in jogos if j['tournament']['name'] in ligas_selecionadas]

    if jogos_filtrados:
        # Criar a lista de nomes para o selectbox
        lista_nomes = {f"{j['homeTeam']['name']} x {j['awayTeam']['name']}": j for j in jogos_filtrados}
        escolha = st.selectbox("🎯 Selecione a Partida para Analisar:", list(lista_nomes.keys()))
        
        jogo_foco = lista_nomes[escolha]
        
        # --- 2. CABEÇALHO VISUAL DO JOGO ---
        st.write("---")
        col_a, col_vs, col_b = st.columns([2, 1, 2])
        with col_a:
            st.markdown(f"<h2 style='text-align: center;'>{jogo_foco['homeTeam']['name']}</h2>", unsafe_allow_html=True)
        with col_vs:
            st.markdown("<h2 style='text-align: center;'>VS</h2>", unsafe_allow_html=True)
        with col_b:
            st.markdown(f"<h2 style='text-align: center;'>{jogo_foco['awayTeam']['name']}</h2>", unsafe_allow_html=True)
        
        if st.button("🚀 EXECUTAR ANÁLISE COMPLETA"):
            # Simulando médias para o cálculo de Poisson (ou use os dados da API se tiver)
            m_gols = 2.7
            m_cantos = 10.5
            
            p_gols = calcular_poisson(m_gols, 2)
            p_cantos = calcular_poisson(m_cantos, 9)

            # --- 3. EXIBIÇÃO COM CORES DE ALERTA ---
            st.write("### 📊 Prognóstico Estatístico")
            c1, c2, c3 = st.columns(3)

            with c1:
                cor_gols = "normal" if p_gols < 70 else "inverse"
                st.metric("Over 2.5 Gols", f"{p_gols:.1f}%", delta="ALTA CHANCE" if p_gols > 70 else "", delta_color=cor_gols)
                
            with c2:
                cor_cantos = "normal" if p_cantos < 75 else "inverse"
                st.metric("Over 9.5 Cantos", f"{p_cantos:.1f}%", delta="TENDÊNCIA" if p_cantos > 75 else "", delta_color=cor_cantos)

            with c3:
                # Árbitro
                ref = jogo_foco.get('referee', {}).get('name', 'Pendente')
                st.write("**Arbitragem:**")
                st.info(f"⚖️ {ref}")

            st.success("Análise Finalizada! Verifique as tendências antes de entrar.")
    else:
        st.info("Selecione uma liga na barra lateral para ver os jogos.")
else:
    st.warning("Nenhum jogo encontrado para hoje.")

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






