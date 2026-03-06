import streamlit as st
import requests
import math
from datetime import datetime

# =========================
# CONFIGURAÇÃO API
# =========================

# DICA: Certifique-se de que sua API_KEY está correta e ativa no RapidAPI
API_KEY = "3a5c2b926bmsh18b3c4624ec302bp1911efjsn84e2922978ff"
HOST = "sportapi7.p.rapidapi.com"

HEADERS = {
    "X-RapidAPI-Key": API_KEY,
    "X-RapidAPI-Host": HOST
}

# =========================
# MODELO MATEMÁTICO
# =========================

def poisson_prob(media, k):
    if media <= 0: return 0
    return (math.exp(-media) * media**k) / math.factorial(k)

def prob_over(media, linha):
    linha_int = int(linha)
    prob = 0
    for i in range(linha_int + 1):
        prob += poisson_prob(media, i)
    return (1 - prob) * 100

def calcular_btts(lambda_home, lambda_away):
    p_home0 = math.exp(-lambda_home) if lambda_home > 0 else 1
    p_away0 = math.exp(-lambda_away) if lambda_away > 0 else 1
    prob = (1 - p_home0) * (1 - p_away0)
    return prob * 100

def prever_gols(h_atq, h_def, a_atq, a_def, media_liga=2.6):
    ataque_casa = h_atq / (media_liga / 2) if media_liga > 0 else 1
    defesa_casa = h_def / (media_liga / 2) if media_liga > 0 else 1
    ataque_fora = a_atq / (media_liga / 2) if media_liga > 0 else 1
    defesa_fora = a_def / (media_liga / 2) if media_liga > 0 else 1

    lambda_home = ataque_casa * defesa_fora * (media_liga / 2)
    lambda_away = ataque_fora * defesa_casa * (media_liga / 2)
    return lambda_home, lambda_away

def prever_1x2(lambda_home, lambda_away):
    max_gols = 6
    casa, empate, fora = 0, 0, 0
    for i in range(max_gols):
        for j in range(max_gols):
            p = poisson_prob(lambda_home, i) * poisson_prob(lambda_away, j)
            if i > j: casa += p
            elif i == j: empate += p
            else: fora += p
    return casa * 100, empate * 100, fora * 100

def placares_provaveis(lambda_home, lambda_away):
    resultados = {}
    for i in range(6):
        for j in range(6):
            p = poisson_prob(lambda_home, i) * poisson_prob(lambda_away, j)
            resultados[f"{i}-{j}"] = p * 100
    top = sorted(resultados.items(), key=lambda x: x[1], reverse=True)
    return top[:5]

# =========================
# API DE DADOS (CORRIGIDA)
# =========================

@st.cache_data(ttl=600)
def jogos_do_dia(data):
    try:
        # A URL precisa do prefixo https://
        url = f"https://{HOST}/api/v1/sport/football/scheduled-events/{data}"
        r = requests.get(url, headers=HEADERS, timeout=12)
        if r.status_code != 200:
            return []
        return r.json().get("events", [])
    except:
        return []

@st.cache_data(ttl=86400)
def estatisticas_time(tournament_id, season_id, team_id):
    try:
        url = f"https://{HOST}/api/v1/tournament/{tournament_id}/season/{season_id}/standings/total"
        r = requests.get(url, headers=HEADERS, timeout=12)
        if r.status_code != 200: return 1.3, 1.3
        
        data = r.json()
        # Verificação de segurança para estrutura do JSON
        if "standings" not in data or not data["standings"]: return 1.3, 1.3
        
        rows = data["standings"][0]["rows"]
        for row in rows:
            if row["team"]["id"] == team_id:
                jogos = max(row.get("matches", 1), 1)
                gp = row.get("scoresFor", 0)
                gs = row.get("scoresAgainst", 0)
                return gp / jogos, gs / jogos
        return 1.3, 1.3
    except:
        return 1.3, 1.3

# =========================
# INTERFACE STREAMLIT
# =========================

st.set_page_config(page_title="PROBET 4.0", layout="wide", page_icon="⚽")
st.title("⚽ PROBET 4.0")

# Sidebar para filtros ajuda a manter os menus visíveis
st.sidebar.header("⚙️ Configurações")
data = st.sidebar.date_input("📅 Data dos jogos", value=datetime.now())
data_str = data.strftime("%Y-%m-%d")

# Busca de jogos
with st.spinner('Buscando partidas...'):
    lista_jogos = jogos_do_dia(data_str)

if not lista_jogos:
    st.error(f"Nenhum jogo encontrado para {data_str}. Tente outra data.")
else:
    # Organizamos as ligas para facilitar a busca
    ligas = sorted(list(set([j['tournament']['name'] for j in lista_jogos])))
    liga_escolhida = st.selectbox("🏆 1. Selecione a Liga", ["Todas"] + ligas)

    # Filtragem dinâmica
    jogos_filtrados = lista_jogos
    if liga_escolhida != "Todas":
        jogos_filtrados = [j for j in lista_jogos if j['tournament']['name'] == liga_escolhida]

    # Dicionário de nomes para o selectbox
    dict_jogos = {}
    for j in jogos_filtrados:
        hora = datetime.fromtimestamp(j.get('startTimestamp', 0)).strftime('%H:%M')
        label = f"[{hora}] {j['homeTeam']['name']} vs {j['awayTeam']['name']}"
        dict_jogos[label] = j

    escolha = st.selectbox("🎯 2. Escolha o jogo", list(dict_jogos.keys()))

    if st.button("🔎 GERAR ANÁLISE"):
        jogo = dict_jogos[escolha]
        
        # Coleta de IDs
        h_id = jogo["homeTeam"]["id"]
        a_id = jogo["awayTeam"]["id"]
        tournament = jogo["tournament"]["id"]
        season = jogo["season"]["id"]

        with st.spinner('Calculando probabilidades...'):
            h_atq, h_def = estatisticas_time(tournament, season, h_id)
            a_atq, a_def = estatisticas_time(tournament, season, a_id)

            l_h, l_a = prever_gols(h_atq, h_def, a_atq, a_def)
            p_casa, p_empate, p_fora = prever_1x2(l_h, l_a)
            media_total = l_h + l_a

            # Exibição dos resultados
            st.divider()
            st.header(f"{jogo['homeTeam']['name']} vs {jogo['awayTeam']['name']}")
            st.caption(f"🏆 {jogo['tournament']['name']} | 🏟️ {jogo.get('venue', {}).get('name', 'Estádio não informado')}")

            c1, c2, c3 = st.columns(3)
            c1.metric("🏠 Vitória Casa", f"{p_casa:.1f}%")
            c2.metric("🤝 Empate", f"{p_empate:.1f}%")
            c3.metric("✈️ Vitória Fora", f"{p_fora:.1f}%")

            st.divider()
            st.subheader("📊 Mercados de Gols")
            m1, m2, m3 = st.columns(3)
            
            m1.metric("Over 1.5", f"{prob_over(media_total, 1.5):.1f}%")
            m2.metric("Over 2.5", f"{prob_over(media_total, 2.5):.1f}%")
            m3.metric("Ambas Marcam (BTTS)", f"{calcular_btts(l_h, l_a):.1f}%")

            st.divider()
            col_placares, col_info = st.columns([1, 1])
            
            with col_placares:
                st.subheader("🎯 Placares Prováveis")
                placares = placares_provaveis(l_h, l_a)
                for placar, prob in placares:
                    st.write(f"**{placar}** — {prob:.2f}%")
            
            with col_info:
                st.subheader("💡 Dica do Modelo")
                if p_casa > 60: st.success("Forte tendência para vitória da Casa.")
                elif p_fora > 60: st.success("Forte tendência para vitória do Visitante.")
                elif prob_over(media_total, 2.5) > 65: st.warning("Jogo com alta expectativa de gols.")
                else: st.info("Jogo equilibrado. Atenção ao mercado de ML ou dupla hipótese.")
