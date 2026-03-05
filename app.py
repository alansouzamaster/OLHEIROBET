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
    for i in range(int(alvo) + 1):
        prob_i = (math.exp(-media) * (media**i)) / math.factorial(i)
        prob_acumulada += prob_i
    return (1 - prob_acumulada) * 100

def prever_1x2(m_casa, m_fora):
    total = m_casa + m_fora
    p_draw = 26.0 # Média estatística de empate no futebol
    sobra = 100 - p_draw
    p_home = sobra * (m_casa / total) if total > 0 else 37.0
    p_away = sobra * (m_fora / total) if total > 0 else 37.0
    return p_home, p_draw, p_away

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
    .1x2-box { text-align: center; padding: 10px; border-radius: 5px; font-weight: bold; margin: 2px; }
    </style>
    """, unsafe_allow_html=True)

st.title("OLHEIRO PRO")

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
    # --- 1. FILTRO JOGOS QUENTES (AUTO-SCANNER) ---
    st.subheader("🔥 Melhores Oportunidades do Dia (+2.5 Gols)")
    quentes = []
    for j in jogos:
        m_simulada = random.uniform(2.2, 3.4)
        prob = calcular_poisson(m_simulada, 2)
        if prob > 72:
            quentes.append({"obj": j, "prob": prob})
    
    if quentes:
        cols_q = st.columns(len(quentes[:4]))
        for i, q in enumerate(quentes[:4]):
            with cols_q[i]:
                st.markdown(f"""
                <div class='oportunidade-card'>
                    <small>{q['obj']['tournament']['name']}</small><br>
                    <strong>{q['obj']['homeTeam']['name']} x {q['obj']['awayTeam']['name']}</strong><br>
                    <span style='color: #ffc107;'>Prob. Gols: {q['prob']:.1f}%</span>
                </div>
                """, unsafe_allow_html=True)
    
    st.write("---")

    # --- 2. SELEÇÃO DE JOGO ---
    todas_ligas = sorted(list(set([j['tournament']['name'] for j in jogos])))
    ligas_sel = st.sidebar.multiselect("Filtre as Ligas (Ex: Brazil):", todas_ligas)
    jogos_filtrados = [j for j in jogos if j['tournament']['name'] in ligas_sel]

    if jogos_filtrados:
        lista_nomes = {f"{j['tournament']['name']} | {j['homeTeam']['name']} x {j['awayTeam']['name']}": j for j in jogos_filtrados}
        escolha = st.selectbox("🎯 Selecione a partida para análise detalhada:", list(lista_nomes.keys()))
        jogo_foco = lista_nomes[escolha]
        
        # --- CABEÇALHO H2H ---
        c_h, c_v, c_a = st.columns([2, 1, 2])
        with c_h:
            st.markdown(f"<h3 style='text-align: center;'>{jogo_foco['homeTeam']['name']}</h3>", unsafe_allow_html=True)
            st.markdown(f"<div style='text-align: center;'>{exibir_forma(['V','V','E','D','V'])}</div>", unsafe_allow_html=True)
        with c_v:
            st.markdown("<h2 style='text-align: center; color: #30363d;'>VS</h2>", unsafe_allow_html=True)
        with c_a:
            st.markdown(f"<h3 style='text-align: center;'>{jogo_foco['awayTeam']['name']}</h3>", unsafe_allow_html=True)
            st.markdown(f"<div style='text-align: center;'>{exibir_forma(['D','E','D','D','V'])}</div>", unsafe_allow_html=True)

        if st.button("🔍 EXECUTAR ANÁLISE COMPLETA"):
            m_casa, m_fora = 1.8, 1.2
            m_gols, m_cantos, m_cartoes = (m_casa + m_fora), 10.4, 4.8
            p_h, p_e, p_a = prever_1x2(m_casa, m_fora)

            # --- RESULTADO 1X2 ---
            st.markdown("### 📊 Probabilidades Resultado Final (1X2)")
            r1, rX, r2 = st.columns(3)
            r1.markdown(f"<div class='1x2-box' style='background-color: #1f77b4;'>Casa: {p_h:.1f}%</div>", unsafe_allow_html=True)
            rX.markdown(f"<div class='1x2-box' style='background-color: #444;'>Empate: {p_e:.1f}%</div>", unsafe_allow_html=True)
            r2.markdown(f"<div class='1x2-box' style='background-color: #dc3545;'>Visitante: {p_a:.1f}%</div>", unsafe_allow_html=True)

            # --- MULTI-MERCADOS ---
            st.markdown("<br>", unsafe_allow_html=True)
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("<div class='mercado-titulo'>⚽ GOLS</div>", unsafe_allow_html=True)
                st.metric("Over 0.5", f"{calcular_poisson(m_gols, 0):.1f}%")
                st.metric("Over 1.5", f"{calcular_poisson(m_gols,
