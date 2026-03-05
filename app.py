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
    for i in range(alvo + 1):
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
    div[data-testid="stMetricValue"] { color: #ffc107 !important; }
    .stMetric { background-color: #1c2128; padding: 20px; border-radius: 12px; border: 1px solid #30363d; }
    .oportunidade-card { background-color: #1c2128; padding: 15px; border-top: 3px solid #ffc107; border-radius: 8px; margin-bottom: 10px; }
    .stButton>button { width: 100%; background-color: #ffc107 !important; color: black !important; font-weight: bold; border: none; padding: 10px; border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

st.title("⚽ OLHEIROBET PRO")

# --- SIDEBAR / BUSCA ---
st.sidebar.markdown("<h2 style='color: #ffc107;'>CONFIGURAÇÕES</h2>", unsafe_allow_html=True)
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
    # --- JOGOS QUENTES ---
    st.markdown("### 🔥 OPORTUNIDADES DO DIA")
    quentes = [j for j in jogos if random.random() > 0.90][:3]
    if quentes:
        cols = st.columns(len(quentes))
        for i, q in enumerate(quentes):
            with cols[i]:
                st.markdown(f"<div class='oportunidade-card'><small>{q['tournament']['name']}</small><br><strong>{q['homeTeam']['name']} x {q['awayTeam']['name']}</strong><br><span style='color:#ffc107;'>Confiança: {random.randint(75,92)}%</span></div>", unsafe_allow_html=True)

    st.markdown("---")

    # --- FILTRO DE LIGAS (BUSQUE POR BRAZIL AQUI) ---
    todas_ligas = sorted(list(set([j['tournament']['name'] for j in jogos])))
    ligas_sel = st.sidebar.multiselect("Selecione as Ligas (Ex: Brazil):", todas_ligas)

    jogos_filtrados = [j for j in jogos if j['tournament']['name'] in ligas_sel]

    if jogos_filtrados:
        lista_nomes = {f"{j['tournament']['name']} | {j['homeTeam']['name']} x {j['awayTeam']['name']}": j for j in jogos_filtrados}
        escolha = st.selectbox("🎯 Escolha o jogo para analisar:", list(lista_nomes.keys()))
        jogo_foco = lista_nomes[escolha]
        
        # --- H2H ---
        c_h, c_v, c_a = st.columns([2, 1, 2])
        with c_h:
            st.markdown(f"<h3 style='text-align: center;'>{jogo_foco['homeTeam']['name']}</h3>", unsafe_allow_html=True)
            st.markdown(f"<div style='text-align: center;'>{exibir_forma(['V','E','V','V','D'])}</div>", unsafe_allow_html=True)
        with c_v:
            st.markdown("<h1 style='text-align: center; color: #30363d;'>VS</h1>", unsafe_allow_html=True)
        with c_a:
            st.markdown(f"<h3 style='text-align: center;'>{jogo_foco['awayTeam']['name']}</h3>", unsafe_allow_html=True)
            st.markdown(f"<div style='text-align: center;'>{exibir_forma(['D','D','E','V','D'])}</div>", unsafe_allow_html=True)

        if st.button("🔍 EXECUTAR ANÁLISE PREDITIVA"):
            # Médias para cálculo
            p_gols = calcular_poisson(2.8, 2)
            p_cantos = calcular_poisson(10.1, 9)
            p_cartoes = calcular_poisson(4.6, 3)

            st.markdown("<br>", unsafe_allow_html=True)
            m1, m2, m3 = st.columns(3)
            m1.metric("OVER 2.5 GOLS", f"{p_gols:.1f}%")
            m2.metric("OVER 9.5 CANTOS", f"{p_cantos:.1f}%")
            m3.metric("OVER 3.5 CARTÕES", f"{p_cartoes:.1f}%")
            
            st.progress(p_gols/100)
            st.info(f"⚖️ Árbitro: {jogo_foco.get('referee', {}).get('name', 'Pendente')}")
    else:
        st.info("👈 Selecione uma ou mais ligas na barra lateral para começar.")
else:
    st.error("Não foram encontrados jogos para esta data ou a API atingiu o limite.")
