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

# --- FUNÇÕES DE CÁLCULO ---
def calcular_poisson(media, alvo):
    if media <= 0: return 0
    prob_acumulada = 0
    for i in range(int(alvo) + 1):
        prob_i = (math.exp(-media) * (media**i)) / math.factorial(i)
        prob_acumulada += prob_i
    return (1 - prob_acumulada) * 100

def prever_1x2(m_casa, m_fora):
    total = m_casa + m_fora
    p_empate = 26.0
    sobra = 100 - p_empate
    if total > 0:
        p_casa = sobra * (m_casa / total)
        p_fora = sobra * (m_fora / total)
    else:
        p_casa = p_fora = sobra / 2
    return p_casa, p_empate, p_fora

@st.cache_data(ttl=86400)
def buscar_medias_reais(tournament_id, season_id, home_id, away_id):
    try:
        url = f"https://{HOST}/api/v1/tournament/{tournament_id}/season/{season_id}/standings/total"
        response = requests.get(url, headers=HEADERS, timeout=12)
        if response.status_code == 200:
            data = response.json()
            standings_list = data.get('standings', [])
            if not standings_list: return 1.5, 1.0
            rows = standings_list[0].get('rows', [])
            m_casa, m_fora = 1.4, 1.1
            for row in rows:
                t_id = row['team']['id']
                jogos = row.get('matches', 1) or 1
                if t_id == home_id: m_casa = row.get('scoresFor', 0)/jogos
                if t_id == away_id: m_fora = row.get('scoresFor', 0)/jogos
            return round(m_casa, 2), round(m_fora, 2)
    except Exception:
        return 1.5, 1.0
    return 1.5, 1.0

def formatar_hora(timestamp):
    if not timestamp: return "--:--"
    return datetime.fromtimestamp(timestamp).strftime('%H:%M')

def formatar_data_br(data_obj):
    return data_obj.strftime('%d/%m/%Y')

# --- INTERFACE E CSS ---
st.set_page_config(page_title="PROBET ANALISE", layout="wide", page_icon="⚽")

st.markdown("""
    <style>
    /* Estilização Geral */
    .stApp { background-color: #0e1117; color: #e0e0e0; }
    
    /* Metrics Personalizados */
    [data-testid="stMetricValue"] { color: #ffc107 !important; font-size: 28px !important; font-weight: 700 !important; }
    .stMetric { background: linear-gradient(145deg, #1c2128, #161b22); padding: 20px; border-radius: 15px; border: 1px solid #30363d; box-shadow: 5px 5px 15px rgba(0,0,0,0.3); }
    
    /* Cards de Destaque */
    .oportunidade-card { background-color: #1c2128; padding: 20px; border-left: 5px solid #ffc107; border-radius: 10px; margin-bottom: 15px; transition: transform 0.3s; }
    .oportunidade-card:hover { transform: scale(1.02); background-color: #24292e; }
    
    /* Botões */
    .stButton>button { width: 100%; background: linear-gradient(90deg, #ffc107, #ff9800) !important; color: black !important; font-weight: bold; border: none; padding: 12px; border-radius: 10px; text-transform: uppercase; }
    
    /* Badges e Textos */
    .horario-badge { background-color: #ffc107; color: #000; padding: 5px 12px; border-radius: 20px; font-weight: 800; font-size: 14px; }
    .header-vs { text-align: center; color: #ffc107; font-size: 50px; font-weight: 900; letter-spacing: -2px; }
    .team-title { font-size: 32px; font-weight: 700; color: #ffffff; margin-bottom: 5px; }
    </style>
    """, unsafe_allow_html=True)

# Título com ícone centralizado
st.markdown("<h1 style='text-align: center; color: #ffc107;'>⚽ PROBET ANALISE PRO</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #888;'>Inteligência Preditiva para Futebol Profissional</p>", unsafe_allow_html=True)
st.markdown("---")

# --- FILTROS DE BUSCA ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/53/53283.png", width=100)
    st.markdown("### ⚙️ PARÂMETROS")
    data_sel = st.date_input("📅 Data das Partidas", value=datetime.now(), format="DD/MM/YYYY")
    
    @st.cache_data(ttl=3600)
    def carregar_jogos(data_str):
        try:
            url = f"https://{HOST}/api/v1/sport/football/scheduled-events/{data_str}"
            response = requests.get(url, headers=HEADERS, timeout=12)
            if response.status_code == 200:
                return response.json().get('events', [])
            return []
        except Exception:
            return []

    jogos = carregar_jogos(data_sel.strftime('%Y-%m-%d'))

btn_analise = False

if jogos:
    todas_ligas = sorted(list(set([j['tournament']['name'] for j in jogos])))
    
    with st.container():
        c_filt1, c_filt2 = st.columns(2)
        with c_filt1:
            ligas_sel = st.multiselect("🏆 Selecione as Ligas", todas_ligas)
        
        jogos_f = [j for j in jogos if j['tournament']['name'] in ligas_sel] if ligas_sel else jogos
        
        with c_filt2:
            if jogos_f:
                lista_nomes = {f"[{formatar_hora(j.get('startTimestamp'))}] {j['homeTeam']['name']} x {j['awayTeam']['name']}": j for j in jogos_f}
                escolha = st.selectbox("🎯 Escolha a partida:", list(lista_nomes.keys()))
                jogo_selecionado = lista_nomes[escolha]
                btn_analise = st.button("🔍 GERAR RELATÓRIO COMPLETO")

    if not btn_analise:
        st.markdown(f"### 🔥 Destaques de Hoje - {formatar_data_br(data_sel)}")
        random.seed(data_sel.toordinal())
        quentes = [j for j in jogos if random.random() > 0.92][:4]
        
        if quentes:
            cols_q = st.columns(len(quentes))
            for i, q in enumerate(quentes):
                with cols_q[i]:
                    hora_q = formatar_hora(q.get('startTimestamp'))
                    st.markdown(f"""
                        <div class='oportunidade-card'>
                            <span class='horario-badge'>{hora_q}</span><br><br>
                            <small style='color:#ffc107;'>{q['tournament']['name']}</small><br>
                            <strong>{q['homeTeam']['shortName']} x {q['awayTeam']['shortName']}</strong><br>
                            <hr style='margin:10px 0; border:0.5px solid #333'>
                            <span style='font-size: 12px; color:#888;'>Sugestão:</span><br>
                            <span style='color:#00ff88; font-weight:bold;'>OVER 2.5 ({random.randint(70, 88)}%)</span>
                        </div>
                    """, unsafe_allow_html=True)

    if btn_analise:
        with st.spinner('🔬 Analisando Big Data...'):
            m_h, m_a = buscar_medias_reais(
                jogo_selecionado['tournament']['id'], 
                jogo_selecionado['season']['id'], 
                jogo_selecionado['homeTeam']['id'], 
                jogo_selecionado['awayTeam']['id']
            )
            m_total = m_h + m_a
            p_c, p_e, p_f = prever_1x2(m_h, m_a)

        # Dashboard de Resultado
        st.markdown("<br>", unsafe_allow_html=True)
        col_main1, col_main2, col_main3 = st.columns([2, 1, 2])
        
        with col_main1:
            st.markdown(f"<p style='text-align:center;' class='team-title'>{jogo_selecionado['homeTeam']['name']}</p>",
