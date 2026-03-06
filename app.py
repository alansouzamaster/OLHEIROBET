import streamlit as st
import requests
import math
from datetime import datetime

# --- CONFIGURAÇÃO DA API ---
API_KEY = "3a5c2b926bmsh18b3c4624ec302bp1911efjsn84e2922978ff"
HOST = "sportapi7.p.rapidapi.com"
HEADERS = {"X-RapidAPI-Key": API_KEY, "X-RapidAPI-Host": HOST}

# --- INICIALIZAÇÃO DE ESTADO ---
if 'analise_pronta' not in st.session_state:
    st.session_state.analise_pronta = False
    st.session_state.jogo_selecionado = None

# --- FUNÇÕES DE CÁLCULO ---
def calcular_poisson(media, alvo):
    if media <= 0: return 0
    prob_acumulada = 0
    for i in range(int(alvo) + 1):
        prob_i = (math.exp(-media) * (media**i)) / math.factorial(i)
        prob_acumulada += prob_i
    return (1 - prob_acumulada) * 100

def prever_1x2_avancado(h_atq, h_def, a_atq, a_def):
    # Modelo: Ataque Mandante vs Defesa Visitante + Mando de Campo
    lambda_casa = h_atq * a_def * 1.10 
    lambda_fora = a_atq * h_def * 0.90 
    total = lambda_casa + lambda_fora
    
    p_empate = 31.0 if total < 2.2 else 26.0
    sobra = 100 - p_empate
    
    if total > 0:
        p_casa = sobra * (lambda_casa / total)
        p_fora = sobra * (lambda_fora / total)
    else:
        p_casa = p_fora = sobra / 2
    return p_casa, p_empate, p_fora, lambda_casa, lambda_fora

@st.cache_data(ttl=86400)
def buscar_estatisticas_completas(tournament_id, season_id, home_id, away_id):
    try:
        url = f"https://{HOST}/api/v1/tournament/{tournament_id}/season/{season_id}/standings/total"
        res = requests.get(url, headers=HEADERS, timeout=12)
        if res.status_code == 200:
            data = res.json().get('standings', [{}])
            if not data: return 1.4, 1.2, 1.1, 1.3
            rows = data[0].get('rows', [])
            h_atq, h_def, a_atq, a_def = 1.4, 1.2, 1.1, 1.3
            for row in rows:
                t_id = row['team']['id']
                jogos = max(row.get('matches', 1), 1)
                gp, gs = row.get('scoresFor', 0), row.get('scoresAgainst', 0)
                if t_id == home_id: h_atq, h_def = gp/jogos, gs/jogos
                if t_id == away_id: a_atq, a_def = gp/jogos, gs/jogos
            return h_atq, h_def, a_atq, a_def
    except: pass
    return 1.4, 1.2, 1.1, 1.3

def formatar_metric(label, prob):
    """Gera o HTML com cor dinâmica e Estrela de Ouro"""
    cor = "#dc3545" # Vermelho
    if prob >= 70: cor = "#28a745" # Verde
    elif prob >= 50: cor = "#ffc107" # Amarelo
    
    estrela = "⭐" if prob >= 85 else ""
    
    return f"""
    <div style='margin-bottom: 10px;'>
        <span style='color:#bbb;'>{label}:</span> 
        <span style='color:{cor}; font-weight:bold; font-size:18px;'>{prob:.1f}%</span> 
        <span style='font-size:14px;'>{estrela}</span>
    </div>
    """

# --- INTERFACE ---
st.set_page_config(page_title="PROBET ANALISE v2.0", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #e0e0e0; }
    .res-box { text-align: center; padding: 15px; border-radius: 8px; font-weight: bold; color: white; margin-bottom: 10px; font-size: 20px; }
    .metric-card { background-color: #1c2128; padding: 15px; border-radius: 10px; border: 1px solid #30363d; }
    </style>
    """, unsafe_allow_html=True)

st.title(" ⚽ PROBET ANALISE ")

# --- FILTROS ---
data_sel = st.date_input("📅 Data das Partidas", value=datetime.now())
data_str = data_sel.strftime('%Y-%m-%d')

@st.cache_data(ttl=600)
def carregar_jogos(d):
    try:
        url = f"https://{HOST}/api/v1/sport/football/scheduled-events/{d}"
        res = requests.get(url, headers=HEADERS, timeout=10)
        return res.json().get('events', []) if res.status_code == 200 else []
    except: return []

jogos = carregar_jogos(data_str)

if jogos:
    todas_ligas = sorted(list(set([j['tournament']['name'] for j in jogos])))
    ligas_sel = st.multiselect("🏆 Selecione as Ligas", todas_ligas)
    jogos_f = [j for j in jogos if j['tournament']['name'] in ligas_sel] if ligas_sel else jogos
    
    if jogos_f:
        lista_nomes = {f"[{datetime.fromtimestamp(j.get('startTimestamp', 0)).strftime('%H:%M')}] {j['homeTeam']['name']} x {j['awayTeam']['name']}": j for j in jogos_f}
        escolha = st.selectbox("🎯 Escolha uma partida:", list(lista_nomes.keys()))
        
        if st.button("🔍 GERAR RELATÓRIO PREDITIVO"):
            st.session_state.jogo_selecionado = lista_nomes[escolha]
            st.session_state.analise_pronta = True

# --- RESULTADOS ---
if st.session_state.analise_pronta and st.session_state.jogo_selecionado:
    jogo = st.session_state.jogo_selecionado
    st.divider()
    
    h_atq, h_def, a_atq, a_def = buscar_estatisticas_completas(
        jogo['tournament']['id'], jogo['season']['id'], 
        jogo['homeTeam']['id'], jogo['awayTeam']['id']
    )
    p_c, p_e, p_f, l_h, l_a = prever_1x2_avancado(h_atq, h_def, a_atq, a_def)
    m_total = l_h + l_a

    st.subheader(f"📊 Análise: {jogo['homeTeam']['name']} vs {jogo['awayTeam']['name']}")
    
    # 1. Vitórias
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div class='res-box' style='background-color:#1f77b4;'>Casa: {p_c:.1f}%</div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='res-box' style='background-color:#444;'>Empate: {p_e:.1f}%</div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='res-box' style='background-color:#dc3545;'>Fora: {p_f:.1f}%</div>", unsafe_allow_html=True)

    # 2. Mercados Secundários
    st.write("---")
    m1, m2, m3 = st.columns(3)
    
    with m1:
        st.info("⚽ GOLS")
        p15 = calcular_poisson(m_total, 1)
        p25 = calcular_poisson(m_total, 2)
        st.markdown(f"<div class='metric-card'>{formatar_metric('Over 1.5', p15)}{formatar_metric('Over 2.5', p25)}</div>", unsafe_allow_html=True)

    with m2:
        st.info("🚩 CANTOS")
        pc8 = calcular_poisson(9.5, 8)
        pc10 = calcular_poisson(9.5, 10)
        st.markdown(f"<div class='metric-card'>{formatar_metric('Over 8.5', pc8)}{formatar_metric('Over 10.5', pc10)}</div>", unsafe_allow_html=True)

    with m3:
        st.info("🟨 CARTÕES")
        p_card3 = calcular_poisson(4.2, 3)
        p_card4 = calcular_poisson(4.2, 4)
        st.markdown(f"<div class='metric-card'>{formatar_metric('Over 3.5', p_card3)}{formatar_metric('Over 4.5', p_card4)}</div>", unsafe_allow_html=True)

    st.caption(f"Legenda: ⭐ = Alta Confiança (+85%) | Cores baseadas em probabilidade técnica.")

elif not jogos:
    st.warning("Nenhum jogo disponível para esta data.")
