import streamlit as st
import requests
import math
import random
from datetime import datetime, timedelta

# --- CONFIGURAÇÃO DA API ---
API_KEY = "a19cf6b5fcmsh62790bdb0d293ddp131982jsn24158e88f703"
HOST = "sportapi7.p.rapidapi.com"
HEADERS = {"X-RapidAPI-Key": API_KEY, "X-RapidAPI-Host": HOST}

# --- FUNÇÕES MATEMÁTICAS ---
def calcular_poisson(media, alvo):
    if media <= 0: return 0
    prob_acumulada = 0
    # O alvo aqui é o número de eventos (ex: 2 gols). 
    # Para "Over X", calculamos a probabilidade de ocorrer X ou menos e subtraímos de 100%.
    for i in range(int(alvo) + 1):
        prob_i = (math.exp(-media) * (media**i)) / math.factorial(i)
        prob_acumulada += prob_i
    return (1 - prob_acumulada) * 100

def exibir_forma(resultados):
    html = ""
    for r in resultados:
        cor = "#28a745" if r == "V" else "#ffc107" if r == "E" else "#dc3545"
        html += f'<span style="display:inline-block; width:22px; height:22px; background-color:{cor}; border-radius:4px; margin-right:4px; text-align:center; color:white; font-size:12px; line-height:22px; font-weight:bold;">{r}</span>'
    return html

# --- INTERFACE E CSS ---
st.set_page_config(page_title="OLHEIROBET PRO", layout="wide", page_icon="⚽")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #e0e0e0; }
    div[data-testid="stMetricValue"] { color: #ffc107 !important; font-size: 24px !important; }
    .stMetric { background-color: #1c2128; padding: 15px; border-radius: 12px; border: 1px solid #30363d; }
    .oportunidade-card { background-color: #1c2128; padding: 15px; border-top: 3px solid #ffc107; border-radius: 8px; margin-bottom: 10px; }
    .stButton>button { width: 100%; background-color: #ffc107 !important; color: black !important; font-weight: bold; border: none; padding: 10px; border-radius: 8px; }
    .mercado-titulo { color: #ffc107; font-weight: bold; margin-bottom: 10px; border-bottom: 1px solid #333; }
    </style>
    """, unsafe_allow_html=True)

st.title("⚽ OLHEIROBET PRO")

# --- SIDEBAR ---
st.sidebar.markdown("<h2 style='color: #ffc107;'>MENU</h2>", unsafe_allow_html=True)
data_sel = st.sidebar.date_input("Escolha a Data", value=datetime.now())

@st.cache_data(ttl=3600)
def carregar_jogos(data_str):
    try:
        url = f"https://{HOST}/api/v1/sport/football/scheduled-events/{data_str}"
        response = requests.get(url, headers=HEADERS)
        return response.json().get('events', []) if response.status_code == 200 else []
    except: return []

jogos = carregar_jogos(data_sel.strftime('%Y-%m-%d'))

if jogos:
    # --- FILTRO DE LIGAS ---
    todas_ligas = sorted(list(set([j['tournament']['name'] for j in jogos])))
    ligas_sel = st.sidebar.multiselect("Selecione as Ligas (Ex: Brazil):", todas_ligas)

    jogos_filtrados = [j for j in jogos if j['tournament']['name'] in ligas_sel]

    if jogos_filtrados:
        lista_nomes = {f"{j['tournament']['name']} | {j['homeTeam']['name']} x {j['awayTeam']['name']}": j for j in jogos_filtrados}
        escolha = st.selectbox("🎯 Selecione a partida para análise detalhada:", list(lista_nomes.keys()))
        jogo_foco = lista_nomes[escolha]
        
        st.markdown("---")
        
        # --- CABEÇALHO ---
        c_h, c_v, c_a = st.columns([2, 1, 2])
        with c_h:
            st.markdown(f"<h3 style='text-align: center;'>{jogo_foco['homeTeam']['name']}</h3>", unsafe_allow_html=True)
            st.markdown(f"<div style='text-align: center;'>{exibir_forma(['V','V','E','D','V'])}</div>", unsafe_allow_html=True)
        with c_v:
            st.markdown("<h1 style='text-align: center; color: #30363d;'>VS</h1>", unsafe_allow_html=True)
        with c_a:
            st.markdown(f"<h3 style='text-align: center;'>{jogo_foco['awayTeam']['name']}</h3>", unsafe_allow_html=True)
            st.markdown(f"<div style='text-align: center;'>{exibir_forma(['D','E','D','D','V'])}</div>", unsafe_allow_html=True)

        if st.button("🔍 EXECUTAR ANÁLISE MULTI-MERCADOS"):
            # Definição de Médias (Simuladas para o exemplo)
            m_gols = 2.8
            m_cantos = 10.2
            m_cartoes = 4.5

            st.markdown("<br>", unsafe_allow_html=True)
            
            # --- COLUNA GOLS ---
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("<div class='mercado-titulo'>⚽ MERCADO DE GOLS</div>", unsafe_allow_html=True)
                st.metric("Over 0.5 Gols", f"{calcular_poisson(m_gols, 0):.1f}%")
                st.metric("Over 1.5 Gols", f"{calcular_poisson(m_gols, 1):.1f}%")
                st.metric("Over 2.5 Gols", f"{calcular_poisson(m_gols, 2):.1f}%")
            
            # --- COLUNA ESCANTEIOS ---
            with col2:
                st.markdown("<div class='mercado-titulo'>🚩 ESCANTEIOS</div>", unsafe_allow_html=True)
                st.metric("Over 4.5 Cantos", f"{calcular_poisson(m_cantos, 4):.1f}%")
                st.metric("Over 7.5 Cantos", f"{calcular_poisson(m_cantos, 7):.1f}%")
                st.metric("Over 9.5 Cantos", f"{calcular_poisson(m_cantos, 9):.1f}%")

            # --- COLUNA CARTÕES ---
            with col3:
                st.markdown("<div class='mercado-titulo'>🟨 CARTÕES</div>", unsafe_allow_html=True)
                st.metric("Over 1.5 Cartões", f"{calcular_poisson(m_cartoes, 1):.1f}%")
                st.metric("Over 3.5 Cartões", f"{calcular_poisson(m_cartoes, 3):.1f}%")
                st.write("")
                st.info(f"⚖️ Juiz: {jogo_foco.get('referee', {}).get('name', 'Pendente')}")

            st.markdown("---")
            st.caption("As probabilidades são calculadas via Distribuição de Poisson baseada em médias projetadas.")
            
    else:
        st.info("👈 Selecione uma liga brasileira ou internacional na barra lateral.")
else:
    st.error("Sem jogos disponíveis para esta data.")
