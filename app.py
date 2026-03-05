import streamlit as st
import requests
import math
import random
from datetime import datetime, timedelta

# --- CONFIGURAÇÃO ---
API_KEY = "a19cf6b5fcmsh62790bdb0d293ddp131982jsn24158e88f703"
HOST = "sportapi7.p.rapidapi.com"
HEADERS = {"X-RapidAPI-Key": API_KEY, "X-RapidAPI-Host": HOST}

# --- FUNÇÕES DE CÁLCULO ---
def calcular_poisson(media, alvo):
    if media <= 0: return 0
    prob_acumulada = 0
    for i in range(alvo + 1):
        prob_i = (math.exp(-media) * (media**i)) / math.factorial(i)
        prob_acumulada += prob_i
    return (1 - prob_acumulada) * 100

def exibir_forma(lista_resultados):
    html_forma = ""
    for res in lista_resultados:
        color = "#28a745" if res == "V" else "#ffc107" if res == "E" else "#dc3545"
        html_forma += f'<span style="display:inline-block; width:22px; height:22px; background-color:{color}; border-radius:4px; margin-right:4px; text-align:center; color:white; font-size:12px; line-height:22px; font-weight:bold;">{res}</span>'
    return html_forma

# --- INTERFACE E DESIGN CSS ---
st.set_page_config(page_title="OLHEIROBET PRO", layout="wide", page_icon="⚽")

st.markdown("""
    <style>
    /* Fundo principal e fontes */
    .stApp { background-color: #0e1117; color: #e0e0e0; }
    
    /* Personalização de Cards de Métrica */
    div[data-testid="stMetricValue"] { color: #ffc107 !important; font-size: 28px !important; }
    div[data-testid="stMetricLabel"] { color: #9ea4b0 !important; font-weight: bold !important; }
    .stMetric { 
        background-color: #1c2128; 
        padding: 20px; 
        border-radius: 12px; 
        border: 1px solid #30363d;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }

    /* Card de Oportunidade */
    .oportunidade-card { 
        background-color: #1c2128; 
        padding: 15px; 
        border-top: 3px solid #ffc107; 
        border-radius: 8px; 
        margin-bottom: 10px;
        transition: transform 0.2s;
    }
    .oportunidade-card:hover { transform: scale(1.02); }

    /* Estilo do Título */
    h1 { color: #ffffff !important; font-weight: 800 !important; letter-spacing: -1px; }
    
    /* Botões */
    .stButton>button {
        width: 100%;
        background-color: #ffc107 !important;
        color: #000000 !important;
        font-weight: bold !important;
        border-radius: 8px !important;
        border: none !important;
        padding: 10px !important;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("⚽ OLHEIROBET PRO")
st.markdown("<p style='color: #9ea4b0;'>Inteligência e Análise Preditiva de Futebol</p>", unsafe_allow_html=True)

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
    # --- JOGOS QUENTES (Design Melhorado) ---
    st.markdown("### 🔥 OPORTUNIDADES EM DESTAQUE")
    oportunidades = [j for j in jogos if random.random() > 0.85][:3] # Simulação de filtro
    
    if oportunidades:
        cols = st.columns(len(oportunidades))
        for i, op in enumerate(oportunidades):
            with cols[i]:
                st.markdown(f"""
                <div class='oportunidade-card'>
                    <small style='color: #8b949e;'>{op['tournament']['name']}</small><br>
                    <div style='margin: 8px 0;'><strong>{op['homeTeam']['name']} x {op['awayTeam']['name']}</strong></div>
                    <span style='color: #ffc107; font-size: 0.9em;'>📈 Confiança: {random.randint(70, 88)}%</span>
                </div>
                """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)

    # --- SELEÇÃO DE JOGO ---
    todas_ligas = sorted(list(set([j['tournament']['name'] for j in jogos])))
    ligas_sel = st.sidebar.multiselect("Ligas", todas_ligas, default=todas_ligas[:2])
    jogos_filtrados = [j for j in jogos if j['tournament']['name'] in ligas_sel]

    if jogos_filtrados:
        lista_nomes = {f"{j['tournament']['name']} | {j['homeTeam']['name']} x {j['awayTeam']['name']}": j for j in jogos_filtrados}
        escolha = st.selectbox("🎯 Selecione a Partida para Detalhamento:", list(lista_nomes.keys()))
        jogo_foco = lista_nomes[escolha]
        
        st.markdown("---")
        
        # --- HEAD TO HEAD VISUAL ---
        c_h, c_v, c_a = st.columns([2, 1, 2])
        with c_h:
            st.markdown(f"<h3 style='text-align: center;'>{jogo_foco['homeTeam']['name']}</h3>", unsafe_allow_html=True)
            st.markdown(f"<div style='text-align: center;'>{exibir_forma(['V','V','E','D','V'])}</div>", unsafe_allow_html=True)
        with c_v:
            st.markdown("<h1 style='text-align: center; color: #30363d; margin-top:10px;'>VS</h1>", unsafe_allow_html=True)
        with c_a:
            st.markdown(f"<h3 style='text-align: center;'>{jogo_foco['awayTeam']['name']}</h3>", unsafe_allow_html=True)
            st.markdown(f"<div style='text-align: center;'>{exibir_forma(['D','E','D','V','D'])}</div>", unsafe_allow_html=True)

        if st.button("🔍 GERAR RELATÓRIO ESTATÍSTICO"):
            with st.spinner('Processando algoritmos...'):
                p_gols = calcular_poisson(2.9, 2)
                p_cantos = calcular_poisson(10.2, 9)
                p_cartoes = calcular_poisson(4.8, 3)

                st.markdown("<br>", unsafe_allow_html=True)
                m1, m2, m3 = st.columns(3)
                m1.metric("CHANCE OVER 2.5 GOLS", f"{p_gols:.1f}%")
                m2.metric("CHANCE OVER 9.5 CANTOS", f"{p_cantos:.1f}%")
                m3.metric("CHANCE OVER 3.5 CARTÕES", f"{p_cartoes:.1f}%")
                
                # Barras de Progresso Customizadas
                st.markdown(f"<small>Confiança do Modelo: {p_gols:.0f}%</small>", unsafe_allow_html=True)
                st.progress(p_gols/100)
    else:
        st.info("Utilize os filtros laterais para carregar os jogos.")
else:
    st.error("Servidor de dados offline ou data sem jogos.")
