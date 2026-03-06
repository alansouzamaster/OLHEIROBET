import streamlit as st
import requests
import math
from datetime import datetime, timedelta

# --- CONFIGURAÇÃO DA SUA CHAVE ---
API_KEY = "a19cf6b5fcmsh62790bdb0d293ddp131982jsn24158e88f703"
HOST = "sportapi7.p.rapidapi.com"

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

def prever_resultado(m_casa, m_fora):
    # Simulação simplificada de probabilidades 1X2 baseada em Poisson
    # Chance de vitória baseada na força relativa
    total = m_casa + m_fora
    p_win_home = (m_casa / total) * 100 if total > 0 else 33.3
    p_win_away = (m_fora / total) * 100 if total > 0 else 33.3
    # Empate é inversamente proporcional à média de gols esperada (jogos de poucos gols empatam mais)
    p_draw = 100 - p_win_home - p_win_away
    
    # Ajuste para dar realismo (empate em futebol gira em torno de 25-30%)
    p_draw = 28.0 
    sobra = 100 - p_draw
    p_win_home = sobra * (m_casa / total)
    p_win_away = sobra * (m_fora / total)
    
    return p_win_home, p_draw, p_win_away

# --- INTERFACE ---
st.set_page_config(page_title="OLHEIROBET PRO", layout="wide", page_icon="⚽")

st.markdown("""
    <style>
    .stMetric { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; }
    .resultado-box { text-align: center; padding: 10px; border-radius: 5px; margin: 5px; color: white; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("⚽ OlheiroBet: Inteligência Esportiva")

# --- CALENDÁRIO ---
st.sidebar.header("📅 Calendário")
data_selecionada = st.sidebar.date_input(
    "Escolha a data:",
    value=datetime.now(),
    min_value=datetime.now() - timedelta(days=1),
    max_value=datetime.now() + timedelta(days=7)
)

@st.cache_data(ttl=3600)
def carregar_jogos(data_str):
    try:
        url = f"https://{HOST}/api/v1/sport/football/scheduled-events/{data_str}"
        response = requests.get(url, headers=HEADERS)
        if response.status_code == 200:
            return response.json().get('events', [])
        return []
    except:
        return []

jogos = carregar_jogos(data_selecionada.strftime('%Y-%m-%d'))

if jogos:
    st.sidebar.header("⚙️ Filtros")
    todas_ligas = sorted(list(set([j['tournament']['name'] for j in jogos])))
    ligas_sel = st.sidebar.multiselect("Filtrar por Liga:", todas_ligas, default=todas_ligas[:3])

    jogos_filtrados = [j for j in jogos if j['tournament']['name'] in ligas_sel]

    if jogos_filtrados:
        lista_nomes = {f"{j['tournament']['name']} | {j['homeTeam']['name']} x {j['awayTeam']['name']}": j for j in jogos_filtrados}
        escolha = st.selectbox("🎯 Selecione a Partida:", list(lista_nomes.keys()))
        jogo_foco = lista_nomes[escolha]
        
        st.write("---")
        c1, cv, c2 = st.columns([2, 1, 2])
        c1.markdown(f"<h2 style='text-align: center;'>{jogo_foco['homeTeam']['name']}</h2>", unsafe_allow_html=True)
        cv.markdown("<h2 style='text-align: center; color: gray;'>VS</h2>", unsafe_allow_html=True)
        c2.markdown(f"<h2 style='text-align: center;'>{jogo_foco['awayTeam']['name']}</h2>", unsafe_allow_html=True)

        if st.button("🔍 EXECUTAR ANÁLISE COMPLETA"):
            with st.spinner('Processando probabilidades...'):
                # Médias Base (Ajustadas para demonstrar favoritismo do mandante)
                m_casa_gols = 1.7
                m_fora_gols = 1.1
                m_total_gols = m_casa_gols + m_fora_gols
                
                p_gols = calcular_poisson(m_total_gols, 2)
                p_cantos = calcular_poisson(10.4, 9)
                p_cartoes = calcular_poisson(4.5, 3)
                
                # 1X2 Probabilidades
                p_casa, p_empate, p_fora = prever_resultado(m_casa_gols, m_fora_gols)

                st.markdown("### 📊 Probabilidades de Resultado Final (1X2)")
                res1, resX, res2 = st.columns(3)
                res1.markdown(f"<div class='resultado-box' style='background-color: #1f77b4;'>Vitoria Mandante: {p_casa:.1f}%</div>", unsafe_allow_html=True)
                resX.markdown(f"<div class='resultado-box' style='background-color: #444;'>Empate: {p_empate:.1f}%</div>", unsafe_allow_html=True)
                res2.markdown(f"<div class='resultado-box' style='background-color: #ff4b4b;'>Vitoria Visitante: {p_fora:.1f}%</div>", unsafe_allow_html=True)

                st.markdown("### 📈 Mercados de Gols, Cantos e Cartões")
                col_g, col_c, col_card = st.columns(3)

                with col_g:
                    st.metric("Prob. Over 2.5 Gols", f"{p_gols:.1f}%")
                    st.progress(min(p_gols/100, 1.0))

                with col_c:
                    st.metric("Prob. Over 9.5 Cantos", f"{p_cantos:.1f}%")
                    st.progress(min(p_cantos/100, 1.0))

                with col_card:
                    st.metric("Prob. Over 3.5 Cartões", f"{p_cartoes:.1f}%")
                    st.progress(min(p_cartoes/100, 1.0))

                st.write("---")
                juiz = jogo_foco.get('referee', {}).get('name', 'Pendente')
                st.info(f"⚖️ Árbitro: {juiz} | 📅 Data: {data_selecionada.strftime('%d/%m/%Y')}")
    else:
        st.info("Selecione uma liga na barra lateral.")
else:
    st.error("Nenhum jogo encontrado para esta data.")
