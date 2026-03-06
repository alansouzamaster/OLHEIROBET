import streamlit as st
import requests
import math
from datetime import datetime

# --- CONFIGURAÇÃO DA API ---
API_KEY = "cd10359c14msheda9060d2cb34cep176fa8jsn3c42386ffb98"


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
    cor = "#dc3545" # Vermelho
    if prob >= 70: cor = "#28a745" # Verde
    elif prob >= 50: cor = "#ffc107" # Amarelo
    estrela = "⭐" if prob >= 85 else ""
    return f"""
    <div style='margin-bottom: 8px;'>
        <span style='color:#bbb; font-size:14px;'>{label}:</span> 
        <span style='color:{cor}; font-weight:bold; font-size:18px;'>{prob:.1f}%</span> 
        <span>{estrela}</span>
    </div>
    """

# --- INTERFACE ---
st.set_page_config(page_title="PROBET ANALISE v3.0", layout="wide", page_icon="⚽")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #e0e0e0; }
    .res-box { text-align: center; padding: 15px; border-radius: 8px; font-weight: bold; color: white; margin-bottom: 10px; font-size: 20px; }
    .metric-card { background-color: #1c2128; padding: 15px; border-radius: 10px; border: 1px solid #30363d; min-height: 100px; }
    h1, h2, h3 { color: #ffc107 !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("⚽ PROBET ANALISE")

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
    
    # IDs e Logos (Caminho alternativo para os escudos)
    id_casa = jogo['homeTeam']['id']
    id_fora = jogo['awayTeam']['id']
    logo_casa = f"https://www.sofascore.com/api/v1/team/{id_casa}/image"
    logo_fora = f"https://www.sofascore.com/api/v1/team/{id_fora}/image"

    h_atq, h_def, a_atq, a_def = buscar_estatisticas_completas(
        jogo['tournament']['id'], jogo['season']['id'], id_casa, id_fora
    )
    p_c, p_e, p_f, l_h, l_a = prever_1x2_avancado(h_atq, h_def, a_atq, a_def)
    m_total = l_h + l_a

    # Cabeçalho Visual com Logos
    col_l, col_m, col_r = st.columns([1, 3, 1])
    with col_l:
        st.image(logo_casa, width=120)
    with col_m:
        st.markdown(f"<h1 style='text-align: center;'>{jogo['homeTeam']['name']} vs {jogo['awayTeam']['name']}</h1>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center; font-size: 18px;'>{jogo['tournament']['name']} • {datetime.fromtimestamp(jogo.get('startTimestamp', 0)).strftime('%H:%M')}</p>", unsafe_allow_html=True)
    with col_r:
        st.image(logo_fora, width=120)
    
    # Vitórias 1X2
    st.write("")
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div class='res-box' style='background-color:#1f77b4;'>Casa: {p_c:.1f}%</div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='res-box' style='background-color:#444;'>Empate: {p_e:.1f}%</div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='res-box' style='background-color:#dc3545;'>Fora: {p_f:.1f}%</div>", unsafe_allow_html=True)

    # Mercados Secundários (Gols, Cantos, Cartões)
    st.divider()
    m1, m2, m3 = st.columns(3)
    
    with m1:
        st.subheader("⚽ GOLS")
        p15 = calcular_poisson(m_total, 1)
        p25 = calcular_poisson(m_total, 2)
        content_gols = formatar_metric('Over 1.5', p15) + formatar_metric('Over 2.5', p25)
        st.markdown(f"<div class='metric-card'>{content_gols}</div>", unsafe_allow_html=True)

    with m2:
        st.subheader("🚩 CANTOS")
        pc8 = calcular_poisson(9.6, 8) # Média padrão dinâmica
        pc10 = calcular_poisson(9.6, 10)
        content_cantos = formatar_metric('Over 8.5', pc8) + formatar_metric('Over 10.5', pc10)
        st.markdown(f"<div class='metric-card'>{content_cantos}</div>", unsafe_allow_html=True)

    with m3:
        st.subheader("🟨 CARTÕES")
        p_card3 = calcular_poisson(4.3, 3)
        p_card4 = calcular_poisson(4.3, 4)
        content_cards = formatar_metric('Over 3.5', p_card3) + formatar_metric('Over 4.5', p_card4)
        st.markdown(f"<div class='metric-card'>{content_cards}</div>", unsafe_allow_html=True)

    st.caption("⭐ = Confiança Técnica Elevada | Baseado em Modelagem de Poisson e Performance Defensiva.")

elif not jogos:
    st.info("Nenhum jogo encontrado para a data selecionada.")


