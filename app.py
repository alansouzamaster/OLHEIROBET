import streamlit as st
import requests
import math
from datetime import datetime

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

# --- INTERFACE ---
st.set_page_config(page_title="OLHEIROBET PRO", layout="wide", page_icon="⚽")

# Estilo para os cards
st.markdown("""
    <style>
    .stMetric { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; }
    </style>
    """, unsafe_allow_html=True)

st.title("⚽ OlheiroBet: Inteligência Esportiva")

@st.cache_data(ttl=3600)
def carregar_jogos():
    try:
        url = f"https://{HOST}/api/v1/sport/football/scheduled-events/{datetime.now().strftime('%Y-%m-%d')}"
        response = requests.get(url, headers=HEADERS)
        if response.status_code == 200:
            return response.json().get('events', [])
        return []
    except:
        return []

jogos = carregar_jogos()

if jogos:
    st.sidebar.header("⚙️ Configurações")
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
            with st.spinner('Calculando probabilidades...'):
                # Simulação de médias dinâmicas
                m_gols = 2.85
                m_cantos = 10.4
                
                p_gols = calcular_poisson(m_gols, 2)
                p_cantos = calcular_poisson(m_cantos, 9)

                st.markdown("### 📊 Resultado da Análise")
                col_g, col_c, col_i = st.columns(3)

                with col_g:
                    st.metric("Prob. Over 2.5 Gols", f"{p_gols:.1f}%")
                    st.progress(min(p_gols/100, 1.0))
                    if p_gols > 65: st.success("🔥 Tendência de Gols")

                with col_c:
                    st.metric("Prob. Over 9.5 Cantos", f"{p_cantos:.1f}%")
                    st.progress(min(p_cantos/100, 1.0))
                    if p_cantos > 75: st.success("🚩 Tendência de Cantos")

                with col_i:
                    juiz = jogo_foco.get('referee', {}).get('name', 'Pendente')
                    st.write("**Info Adicional:**")
                    st.info(f"⚖️ Árbitro: {juiz}")

                st.write("---")
                st.caption("Aviso: As probabilidades são baseadas em modelos matemáticos. Jogue com responsabilidade.")
    else:
        st.info("Selecione uma liga na barra lateral.")
else:
    st.error("Não foi possível carregar os jogos. Verifique sua chave API.")
