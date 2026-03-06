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
    # Cruzamento de dados com fator mando de campo
    lambda_casa = h_atq * a_def * 1.10 
    lambda_fora = a_atq * h_def * 0.90 
    total = lambda_casa + lambda_fora
    
    # Empate dinâmico baseado na expectativa de gols
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

# --- INTERFACE ---
st.set_page_config(page_title="PROBET ANALISE", layout="wide")
st.title("⚽ PROBET ANALISE")

# Seleção de Data
data_sel = st.date_input("Selecione a Data", value=datetime.now())
data_str = data_sel.strftime('%Y-%m-%d')

@st.cache_data(ttl=3600)
def carregar_jogos(d):
    try:
        url = f"https://{HOST}/api/v1/sport/football/scheduled-events/{d}"
        res = requests.get(url, headers=HEADERS)
        return res.json().get('events', []) if res.status_code == 200 else []
    except: return []

jogos = carregar_jogos(data_str)

if jogos:
    todas_ligas = sorted(list(set([j['tournament']['name'] for j in jogos])))
    ligas_sel = st.multiselect("Filtrar Ligas", todas_ligas)
    
    jogos_f = [j for j in jogos if j['tournament']['name'] in ligas_sel] if ligas_sel else jogos
    
    if jogos_f:
        lista_nomes = {f"{j['homeTeam']['name']} x {j['awayTeam']['name']}": j for j in jogos_f}
        escolha = st.selectbox("Escolha a partida", list(lista_nomes.keys()))
        jogo_selecionado = lista_nomes[escolha]
        btn_analise = st.button("ANALISAR PARTIDA")

# --- BLOCO DE RESULTADOS ---
if btn_analise and jogo_selecionado:
    st.divider()
    
    # Cálculo das estatísticas
    h_atq, h_def, a_atq, a_def = buscar_estatisticas_completas(
        jogo_selecionado['tournament']['id'], 
        jogo_selecionado['season']['id'], 
        jogo_selecionado['homeTeam']['id'], 
        jogo_selecionado['awayTeam']['id']
    )
    
    p_c, p_e, p_f, lamb_h, lamb_a = prever_1x2_avancado(h_atq, h_def, a_atq, a_def)
    m_total = lamb_h + lamb_a

    # Exibição de Probabilidades Principais
    st.subheader(f"📊 Probabilidades: {p_c:.1f}% (Casa) | {p_e:.1f}% (Empate) | {p_f:.1f}% (Fora)")
    
    # Colunas de Métricas
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### ⚽ GOLS")
        st.metric("Over 1.5", f"{calcular_poisson(m_total, 1):.1f}%")
        st.metric("Over 2.5", f"{calcular_poisson(m_total, 2):.1f}%")
        
    with col2:
        st.markdown("#### 🚩 CANTOS (Escanteios)")
        st.metric("Over 8.5", f"{calcular_poisson(9.5, 8):.1f}%")
        st.metric("Over 10.5", f"{calcular_poisson(9.5, 10):.1f}%")
        
    with col3:
        st.markdown("#### 🟨 CARTÕES")
        st.metric("Over 3.5", f"{calcular_poisson(4.2, 3):.1f}%")
        st.metric("Over 4.5", f"{calcular_poisson(4.2, 4):.1f}%")

    st.divider()
    st.caption(f"Análise baseada no desempenho histórico de ataque ({h_atq:.2f} vs {a_atq:.2f}) e defesa ({h_def:.2f} vs {a_def:.2f}) das equipes.")
else:
    if not jogos:
        st.info("Nenhum jogo encontrado para a data selecionada.")
