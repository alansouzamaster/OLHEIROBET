import streamlit as st
import requests
import math
from datetime import datetime

# --- CONFIGURAÇÃO DA API ---
API_KEY = "3a5c2b926bmsh18b3c4624ec302bp1911efjsn84e2922978ff"
HOST = "sportapi7.p.rapidapi.com"
HEADERS = {"X-RapidAPI-Key": API_KEY, "X-RapidAPI-Host": HOST}

# --- FUNÇÕES DE CÁLCULO AVANÇADO ---

def calcular_poisson(media, alvo):
    if media <= 0: return 0
    prob_acumulada = 0
    for i in range(int(alvo) + 1):
        prob_i = (math.exp(-media) * (media**i)) / math.factorial(i)
        prob_acumulada += prob_i
    return (1 - prob_acumulada) * 100

def prever_1x2_avancado(h_atq, h_def, a_atq, a_def):
    # Fator de Mando de Campo (Mandante produz mais, Visitante sofre mais)
    # Cruzamos o Ataque de um com a Defesa do outro
    lambda_casa = h_atq * a_def * 1.10  # 10% de bônus por jogar em casa
    lambda_fora = a_atq * h_def * 0.90  # Redução para o visitante
    
    total_esperado = lambda_casa + lambda_fora
    
    # Cálculo dinâmico de empate (jogos com menos gols esperados tendem mais ao empate)
    if total_esperado < 2.2:
        p_empate = 31.0
    elif total_esperado < 3.0:
        p_empate = 26.0
    else:
        p_empate = 21.0
        
    sobra = 100 - p_empate
    
    if total_esperado > 0:
        p_casa = sobra * (lambda_casa / total_esperado)
        p_fora = sobra * (lambda_fora / total_esperado)
    else:
        p_casa = p_fora = sobra / 2
        
    return round(p_casa, 1), round(p_empate, 1), round(p_fora, 1), lambda_casa, lambda_fora

@st.cache_data(ttl=86400)
def buscar_estatisticas_completas(tournament_id, season_id, home_id, away_id):
    """Busca gols marcados E sofridos para calcular força de ataque e defesa."""
    try:
        url = f"https://{HOST}/api/v1/tournament/{tournament_id}/season/{season_id}/standings/total"
        response = requests.get(url, headers=HEADERS, timeout=12)
        if response.status_code == 200:
            data = response.json()
            rows = data.get('standings', [{}])[0].get('rows', [])
            
            # Valores padrão (médias mundiais)
            h_atq, h_def = 1.4, 1.2
            a_atq, a_def = 1.1, 1.3
            
            for row in rows:
                t_id = row['team']['id']
                jogos = row.get('matches', 1) or 1
                gp = row.get('scoresFor', 0)
                gs = row.get('scoresAgainst', 0)
                
                if t_id == home_id:
                    h_atq = gp / jogos
                    h_def = gs / jogos
                if t_id == away_id:
                    a_atq = gp / jogos
                    a_def = gs / jogos
            
            return h_atq, h_def, a_atq, a_def
    except:
        return 1.4, 1.2, 1.1, 1.3
    return 1.4, 1.2, 1.1, 1.3

# --- INTERFACE (PARTE DA ANÁLISE) ---

# ... (Manter código de filtros e seleção de jogos que você já tem) ...

if btn_analise and jogo_selecionado:
    st.write("---")
    with st.spinner('Executando Modelo de Ataque vs Defesa...'):
        # 1. Busca dados reais de gols pró e contra
        h_atq, h_def, a_atq, a_def = buscar_estatisticas_completas(
            jogo_selecionado['tournament']['id'], 
            jogo_selecionado['season']['id'], 
            jogo_selecionado['homeTeam']['id'], 
            jogo_selecionado['awayTeam']['id']
        )
        
        # 2. Calcula probabilidades avançadas
        p_c, p_e, p_f, lamb_h, lamb_a = prever_1x2_avancado(h_atq, h_def, a_atq, a_def)
        m_total = lamb_h + lamb_a

    # Exibição dos Resultados
    st.markdown(f"### 🏟️ Análise: {jogo_selecionado['homeTeam']['name']} vs {jogo_selecionado['awayTeam']['name']}")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Vitória Casa", f"{p_c}%")
    col2.metric("Empate", f"{p_e}%")
    col3.metric("Vitória Fora", f"{p_f}%")

    st.markdown("#### ⚽ Projeção de Gols (Ajustada)")
    g1, g2 = st.columns(2)
    with g1:
        st.metric("Over 1.5 Gols", f"{calcular_poisson(m_total, 1):.1f}%")
        st.caption(f"Expectativa de Gols Mandante: {lamb_h:.2f}")
    with g2:
        st.metric("Over 2.5 Gols", f"{calcular_poisson(m_total, 2):.1f}%")
        st.caption(f"Expectativa de Gols Visitante: {lamb_a:.2f}")
