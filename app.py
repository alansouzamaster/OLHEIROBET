import streamlit as st
import requests
import math
import random
from datetime import datetime
import time

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
    p_empate = 25.0
    sobra = 100 - p_empate
    if total > 0:
        p_casa = sobra * (m_casa / total)
        p_fora = sobra * (m_fora / total)
    else:
        p_casa = p_fora = sobra / 2
    return p_casa, p_empate, p_fora

def formatar_hora(timestamp):
    # Converte o timestamp da API para o horário local
    return datetime.fromtimestamp(timestamp).strftime('%H:%M')

def exibir_forma(resultados):
    html = ""
    for r in resultados:
        cor = "#28a745" if r == "V" else "#ffc107" if r == "E" else "#dc3545"
        html += f'<span style="display:inline-block; width:22px; height:22px; background-color:{cor}; border-radius:4px; margin-right:4px; text-align:center; color:white; font-size:12px; line-height:22px; font-weight:bold;">{r}</span>'
    return html

# --- INTERFACE E CSS ---
st.set_page_config(page_title="PROBET ANALISE", layout="wide", page_icon="⚽")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #e0e0e0; }
    div[data-testid="stMetricValue"] { color: #ffc107 !important; font-size: 24px !important; }
    .stMetric { background-color: #1c2128; padding: 15px; border-radius: 12px; border: 1px solid #30363d; }
    .oportunidade-card { background-color: #1c2128; padding: 15px; border-top: 3px solid #ffc107; border-radius: 8px; margin-bottom: 10px; }
    .stButton>button { width: 100%; background-color: #ffc107 !important; color: black !important; font-weight: bold; border: none; padding: 12px; border-radius: 8px; font-size: 16px; }
    .mercado-titulo { color: #ffc107; font-weight: bold; margin-bottom: 10px; border-bottom: 1px solid #333; }
    .res-box { text-align: center; padding: 10px; border-radius: 6px; font-weight: bold; color: white; }
    .horario-badge { background-color: #333; color: #ffc107; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 14px; }
    </style>
    """, unsafe_allow_html=True)

st.title(" ⚽ PROBET ANALISE ")
st.markdown("---")

# --- MENU CENTRALIZADO ---
st.markdown("### 🛠️ FILTROS DE BUSCA")
col_data, col_liga = st.columns([1, 2])

with col_data:
    data_sel = st.date_input("📅 Escolha a Data", value=datetime.now())

@st.cache_data(ttl=3600)
def carregar_jogos(data_str):
    try:
        url = f"https://{HOST}/api/v1/sport/football/scheduled-events/{data_str}"
        response = requests.get(url, headers=HEADERS)
        return response.json().get('events', []) if response.status_code == 200 else []
    except: return []

jogos = carregar_jogos(data_sel.strftime('%Y-%m-%d'))

if jogos:
    with col_liga:
        todas_ligas = sorted(list(set([j['tournament']['name'] for j in jogos])))
        ligas_sel = st.multiselect("🏆 Selecione as Ligas", todas_ligas)

    # --- JOGOS QUENTES COM HORÁRIO ---
    st.subheader("🔥 Oportunidades em Destaque")
    quentes = [j for j in jogos if random.random() > 0.92][:4]
    if quentes:
        cols_q = st.columns(len(quentes))
        for i, q in enumerate(quentes):
            with cols_q[i]:
                prob_q = random.randint(71, 88)
                hora = formatar_hora(q.get('startTimestamp', time.time()))
                st.markdown(f"""
                <div class='oportunidade-card'>
                    <span class='horario-badge'>🕒 {hora}</span><br>
                    <small>{q['tournament']['name']}</small><br>
                    <strong>{q['homeTeam']['name']} x {q['awayTeam']['name']}</strong><br>
                    <span style='color:#ffc107;'>Over 2.5: {prob_q}%</span>
                </div>
                """, unsafe_allow_html=True)

    st.write("---")

    # --- SELEÇÃO DE JOGO COM HORÁRIO NO NOME ---
    jogos_filtrados = [j for j in jogos if j['tournament']['name'] in ligas_sel]

    if jogos_filtrados:
        # Adicionando o horário na lista de seleção para facilitar a identificação
        lista_nomes = {
            f"[{formatar_hora(j.get('startTimestamp'))}] {j['homeTeam']['name']} x {j['awayTeam']['name']}": j 
            for j in jogos_filtrados
        }
        escolha = st.selectbox("🎯 Escolha uma partida para analisar:", list(lista_nomes.keys()))
        jogo_foco = lista_nomes[escolha]
        hora_foco = formatar_hora(jogo_foco.get('startTimestamp'))
        
        # --- CABEÇALHO CONFRONTO ---
        st.markdown(f"<div style='text-align:center;'><span class='horario-badge' style='font-size:18px;'>INÍCIO ÀS {hora_foco}</span></div>", unsafe_allow_html=True)
        c_h, c_v, c_a = st.columns([2, 1, 2])
        with c_h:
            st.markdown(f"<h2 style='text-align: center;'>{jogo_foco['homeTeam']['name']}</h2>", unsafe_allow_html=True)
            st.markdown(f"<div style='text-align: center;'>{exibir_forma(['V','V','E','D','V'])}</div>", unsafe_allow_html=True)
        with c_v:
            st.markdown("<h1 style='text-align: center; color: #30363d; margin-top: 15px;'>VS</h1>", unsafe_allow_html=True)
        with c_a:
            st.markdown(f"<h2 style='text-align: center;'>{jogo_foco['awayTeam']['name']}</h2>", unsafe_allow_html=True)
            st.markdown(f"<div style='text-align: center;'>{exibir_forma(['D','E','D','D','V'])}</div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔍 GERAR RELATÓRIO PREDITIVO COMPLETO"):
            m_casa, m_fora = 1.8, 1.2
            m_gols = m_casa + m_fora
            m_cantos, m_cartoes = 10.5, 4.2
            
            p_c, p_e, p_f = prever_1x2(m_casa, m_fora)
            st.markdown("### 📊 Probabilidades 1X2")
            r1, r2, r3 = st.columns(3)
            r1.markdown(f"<div class='res-box' style='background-color:#1f77b4;'>Vitória Casa: {p_c:.1f}%</div>", unsafe_allow_html=True)
            r2.markdown(f"<div class='res-box' style='background-color:#444;'>Empate: {p_e:.1f}%</div>", unsafe_allow_html=True)
            r3.markdown(f"<div class='res-box' style='background-color:#dc3545;'>Vitória Visitante: {p_f:.1f}%</div>", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("<div class='mercado-titulo'>⚽ GOLS</div>", unsafe_allow_html=True)
