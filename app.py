import streamlit as st
import requests
import math
from datetime import datetime

# --- CONFIGURAÇÃO DA API ---
API_KEY = "3a5c2b926bmsh18b3c4624ec302bp1911efjsn84e2922978ff"
HOST = "sportapi7.p.rapidapi.com"
HEADERS = {"X-RapidAPI-Key": API_KEY, "X-RapidAPI-Host": HOST}

# --- 1. INICIALIZAÇÃO ---
btn_analise = False
jogo_selecionado = None

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
    p_casa = sobra * (lambda_casa / total) if total > 0 else sobra / 2
    p_fora = sobra * (lambda_fora / total) if total > 0 else sobra / 2
    return p_casa, p_empate, p_fora, lambda_casa, lambda_fora

@st.cache_data(ttl=86400)
def buscar_estatisticas_completas(tournament_id, season_id, home_id, away_id):
    try:
        url = f"https://{HOST}/api/v1/tournament/{tournament_id}/season/{season_id}/standings/total"
        res = requests.get(url, headers=HEADERS, timeout=12)
        if res.status_code == 200:
            rows = res.json().get('standings', [{}])[0].get('rows', [])
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

@st.cache_data(ttl=3600)
def buscar_cartoes_elenco(team_id, tournament_id, season_id):
    try:
        url_squad = f"https://{HOST}/api/v1/team/{team_id}/players"
        res = requests.get(url_squad, headers=HEADERS, timeout=10)
        if res.status_code != 200: return []
        players = res.json().get('players', [])
        dados = []
        for p in players[:15]: # Limitado para performance
            p_id = p['player']['id']
            url_s = f"https://{HOST}/api/v1/player/{p_id}/unique-tournament/{tournament_id}/season/{season_id}/statistics/overall"
            res_s = requests.get(url_s, headers=HEADERS, timeout=5)
            if res_s.status_code == 200:
                s = res_s.json().get('statistics', {})
                if s.get('appearances', 0) > 0 and s.get('yellowCards', 0) > 0:
                    prob = (s['yellowCards'] / s['appearances']) * 100
                    dados.append({"nome": p['player']['name'], "prob": round(min(prob, 99), 1)})
        return sorted(dados, key=lambda x: x['prob'], reverse=True)
    except: return []

# --- INTERFACE ---
st.set_page_config(page_title="PROBET ANALISE", layout="wide")
st.title("⚽ PROBET ANALISE")

data_sel = st.date_input("Data", value=datetime.now())
data_str = data_sel.strftime('%Y-%m-%d')

@st.cache_data(ttl=3600)
def carregar_jogos(d):
    url = f"https://{HOST}/api/v1/sport/football/scheduled-events/{d}"
    res = requests.get(url, headers=HEADERS)
    return res.json().get('events', []) if res.status_code == 200 else []

jogos = carregar_jogos(data_str)

if jogos:
    todas_ligas = sorted(list(set([j['tournament']['name'] for j in jogos])))
    ligas_sel = st.multiselect("Ligas", todas_ligas)
    jogos_f = [j for j in jogos if j['tournament']['name'] in ligas_sel] if ligas_sel else jogos
    
    if jogos_f:
        lista_nomes = {f"{j['homeTeam']['name']} x {j['awayTeam']['name']}": j for j in jogos_f}
        escolha = st.selectbox("Escolha a partida", list(lista_nomes.keys()))
        jogo_selecionado = lista_nomes[escolha]
        btn_analise = st.button("ANALISAR")

# --- BLOCO DE ANÁLISE COMPLETO ---
if btn_analise and jogo_selecionado:
    st.divider()
    h_atq, h_def, a_atq, a_def = buscar_estatisticas_completas(
        jogo_selecionado['tournament']['id'], 
        jogo_selecionado['season']['id'], 
        jogo_selecionado['homeTeam']['id'], 
        jogo_selecionado['awayTeam']['id']
    )
    p_c, p_e, p_f, lamb_h, lamb_a = prever_1x2_avancado(h_atq, h_def, a_atq, a_def)
    m_total = lamb_h + lamb_a

    # 1. Probabilidades 1X2
    st.subheader(f"📊 Probabilidades: {p_c:.1f}% | {p_e:.1f}% | {p_f:.1f}%")
    
    # 2. Cards de Métricas
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("#### ⚽ GOLS")
        st.metric("Over 1.5", f"{calcular_poisson(m_total, 1):.1f}%")
        st.metric("Over 2.5", f"{calcular_poisson(m_total, 2):.1f}%")
    with col2:
        st.markdown("#### 🚩 CANTOS")
        st.metric("Over 8.5", f"{calcular_poisson(9.5, 8):.1f}%") # Média base
        st.metric("Over 10.5", f"{calcular_poisson(9.5, 10):.1f}%")
    with col3:
        st.markdown("#### 🟨 CARTÕES")
        st.metric("Over 3.5", f"{calcular_poisson(4.2, 3):.1f}%")
        st.info(f"⚖️ Juiz: {jogo_selecionado.get('referee', {}).get('name', 'N/A')}")

    # 3. Análise de Elenco (Indisciplina)
    st.divider()
    st.subheader("🟨 Jogadores com Maior Tendência a Cartão")
    t_casa, t_fora = st.tabs([jogo_selecionado['homeTeam']['name'], jogo_selecionado['awayTeam']['name']])
    
    with t_casa:
        elenco_h = buscar_cartoes_elenco(jogo_selecionado['homeTeam']['id'], jogo_selecionado['tournament']['id'], jogo_selecionado['season']['id'])
        for p in elenco_h:
            st.write(f"**{p['prob']}%** - {p['nome']}")
            st.progress(p['prob']/100)
            
    with t_fora:
        elenco_a = buscar_cartoes_elenco(jogo_selecionado['awayTeam']['id'], jogo_selecionado['tournament']['id'], jogo_selecionado['season']['id'])
        for p in elenco_a:
            st.write(f"**{p['prob']}%** - {p['nome']}")
            st.progress(p['prob']/100)
