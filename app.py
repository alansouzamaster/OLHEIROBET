import math

def poisson_prob(media, k):
    return (math.exp(-media) * media**k) / math.factorial(k)

def prob_over(media, linha):

    linha_int = int(linha)

    prob = 0
    for i in range(linha_int + 1):
        prob += poisson_prob(media, i)

    return (1 - prob) * 100


def calcular_btts(lambda_home, lambda_away):

    p_home0 = math.exp(-lambda_home)
    p_away0 = math.exp(-lambda_away)

    prob = (1 - p_home0) * (1 - p_away0)

    return prob * 100


def prever_gols(h_atq, h_def, a_atq, a_def, media_liga=2.6):

    ataque_casa = h_atq / (media_liga / 2)
    defesa_casa = h_def / (media_liga / 2)

    ataque_fora = a_atq / (media_liga / 2)
    defesa_fora = a_def / (media_liga / 2)

    lambda_home = ataque_casa * defesa_fora * (media_liga / 2)
    lambda_away = ataque_fora * defesa_casa * (media_liga / 2)

    return lambda_home, lambda_away


def prever_1x2(lambda_home, lambda_away):

    max_gols = 6

    casa = 0
    empate = 0
    fora = 0

    for i in range(max_gols):
        for j in range(max_gols):

            p = poisson_prob(lambda_home, i) * poisson_prob(lambda_away, j)

            if i > j:
                casa += p
            elif i == j:
                empate += p
            else:
                fora += p

    return casa * 100, empate * 100, fora * 100


def placares_provaveis(lambda_home, lambda_away):

    resultados = {}

    for i in range(6):
        for j in range(6):

            p = poisson_prob(lambda_home, i) * poisson_prob(lambda_away, j)

            resultados[f"{i}-{j}"] = p * 100

    top = sorted(resultados.items(), key=lambda x: x[1], reverse=True)

    return top[:5]
import requests

API_KEY = "e0b5f00182mshfd230164523fd40p120ad6jsn5604e643008f"

HOST = "sportapi7.p.rapidapi.com"

HEADERS = {
"X-RapidAPI-Key": API_KEY,
"X-RapidAPI-Host": HOST
}


def jogos_do_dia(data):

    url = f"https://{HOST}/api/v1/sport/football/scheduled-events/{data}"

    r = requests.get(url, headers=HEADERS)

    if r.status_code != 200:
        return []

    return r.json().get("events", [])


def estatisticas_time(tournament_id, season_id, team_id):

    url = f"https://{HOST}/api/v1/tournament/{tournament_id}/season/{season_id}/standings/total"

    r = requests.get(url, headers=HEADERS)

    if r.status_code != 200:
        return 1.3,1.3

    data = r.json()

    rows = data["standings"][0]["rows"]

    for row in rows:

        if row["team"]["id"] == team_id:

            jogos = max(row["matches"],1)

            gp = row["scoresFor"]
            gs = row["scoresAgainst"]

            return gp/jogos, gs/jogos

    return 1.3,1.3
import streamlit as st
from datetime import datetime

from api_dados import *
from core_modelo import *

st.set_page_config(
page_title="PROBET 4.0",
layout="wide",
page_icon="⚽"
)

st.title("⚽ PROBET 4.0")

data = st.date_input("Data dos jogos", value=datetime.now())

jogos = jogos_do_dia(data.strftime("%Y-%m-%d"))

if not jogos:

    st.warning("Nenhum jogo encontrado")

else:

    nomes = {}

    for j in jogos:

        nome = f"{j['homeTeam']['name']} vs {j['awayTeam']['name']}"

        nomes[nome] = j

    escolha = st.selectbox("Escolha o jogo", list(nomes.keys()))

    if st.button("GERAR ANÁLISE"):

        jogo = nomes[escolha]

        home = jogo["homeTeam"]["name"]
        away = jogo["awayTeam"]["name"]

        h_id = jogo["homeTeam"]["id"]
        a_id = jogo["awayTeam"]["id"]

        tournament = jogo["tournament"]["id"]
        season = jogo["season"]["id"]

        h_atq,h_def = estatisticas_time(tournament,season,h_id)
        a_atq,a_def = estatisticas_time(tournament,season,a_id)

        lambda_home, lambda_away = prever_gols(h_atq,h_def,a_atq,a_def)

        p_casa,p_empate,p_fora = prever_1x2(lambda_home,lambda_away)

        media = lambda_home + lambda_away

        st.header(f"{home} vs {away}")

        c1,c2,c3 = st.columns(3)

        c1.metric("Casa",f"{p_casa:.1f}%")
        c2.metric("Empate",f"{p_empate:.1f}%")
        c3.metric("Fora",f"{p_fora:.1f}%")

        st.subheader("Mercados")

        over15 = prob_over(media,1.5)
        over25 = prob_over(media,2.5)

        btts = calcular_btts(lambda_home,lambda_away)

        m1,m2,m3 = st.columns(3)

        m1.metric("Over 1.5",f"{over15:.1f}%")
        m2.metric("Over 2.5",f"{over25:.1f}%")
        m3.metric("BTTS",f"{btts:.1f}%")

        st.subheader("Placares prováveis")

        placares = placares_provaveis(lambda_home,lambda_away)

        for p in placares:

            st.write(p)
