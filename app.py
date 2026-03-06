import streamlit as st
import requests
import math
import random
import numpy as np
from datetime import datetime

# ---------------- CONFIG ----------------

API_KEY = "SUA_API_AQUI"
HOST = "sportapi7.p.rapidapi.com"

HEADERS = {
"X-RapidAPI-Key": API_KEY,
"X-RapidAPI-Host": HOST
}

st.set_page_config(
page_title="PROBET ANALISE PRO",
layout="wide",
page_icon="⚽"
)

# ---------------- CSS ----------------

st.markdown("""
<style>

.stApp{
background:linear-gradient(180deg,#0b0f14,#111827);
color:#e6edf3;
}

h1,h2,h3{
color:#ffc107;
}

.card{
background:#1c2128;
padding:20px;
border-radius:12px;
border:1px solid #30363d;
box-shadow:0 6px 18px rgba(0,0,0,0.5);
}

.res-box{
text-align:center;
padding:14px;
border-radius:10px;
font-weight:bold;
color:white;
margin-bottom:10px;
font-size:20px;
}

.header-vs{
text-align:center;
color:#ffc107;
font-size:40px;
font-weight:800;
margin-top:20px;
}

.stMetric{
background:#161b22;
padding:15px;
border-radius:12px;
border:1px solid #30363d;
}

</style>
""", unsafe_allow_html=True)

# ---------------- FUNÇÕES ----------------

def calcular_poisson(media, alvo):

    if media <= 0:
        return 0

    prob_acumulada = 0

    for i in range(int(alvo)+1):

        prob_i = (math.exp(-media)*(media**i))/math.factorial(i)

        prob_acumulada += prob_i

    return (1-prob_acumulada)*100


def prever_1x2(m_casa,m_fora):

    total = m_casa+m_fora

    p_empate = 26

    sobra = 100-p_empate

    if total>0:

        p_casa = sobra*(m_casa/total)

        p_fora = sobra*(m_fora/total)

    else:

        p_casa = p_fora = sobra/2

    return p_casa,p_empate,p_fora


def simulacao_montecarlo(media_casa,media_fora,simulacoes=5000):

    resultados={}

    for _ in range(simulacoes):

        g_casa = np.random.poisson(media_casa)

        g_fora = np.random.poisson(media_fora)

        placar = f"{g_casa}x{g_fora}"

        resultados[placar]=resultados.get(placar,0)+1

    top = sorted(resultados.items(),key=lambda x:x[1],reverse=True)[:5]

    return top


def calcular_btts(m_casa,m_fora):

    prob_casa_0 = math.exp(-m_casa)

    prob_fora_0 = math.exp(-m_fora)

    prob_ambos = 1 - (prob_casa_0 + prob_fora_0 - (prob_casa_0*prob_fora_0))

    return prob_ambos*100


def formatar_hora(ts):

    if not ts:
        return "--:--"

    return datetime.fromtimestamp(ts).strftime("%H:%M")


# ---------------- API ----------------

@st.cache_data(ttl=3600)
def carregar_jogos(data_str):

    try:

        url=f"https://{HOST}/api/v1/sport/football/scheduled-events/{data_str}"

        r=requests.get(url,headers=HEADERS)

        if r.status_code==200:

            return r.json().get("events",[])

        return []

    except:

        return []


@st.cache_data(ttl=86400)
def buscar_medias_reais(tournament_id,season_id,home_id,away_id):

    try:

        url=f"https://{HOST}/api/v1/tournament/{tournament_id}/season/{season_id}/standings/total"

        r=requests.get(url,headers=HEADERS)

        if r.status_code==200:

            data=r.json()

            rows=data["standings"][0]["rows"]

            m_casa=1.4

            m_fora=1.1

            for row in rows:

                jogos=row.get("matches",1)

                if jogos==0:
                    jogos=1

                if row["team"]["id"]==home_id:
                    m_casa=row.get("scoresFor",0)/jogos

                if row["team"]["id"]==away_id:
                    m_fora=row.get("scoresFor",0)/jogos

            return round(m_casa,2),round(m_fora,2)

    except:

        return 1.5,1.0

    return 1.5,1.0


# ---------------- INTERFACE ----------------

st.title("⚽ PROBET ANALISE PRO")

data_sel = st.date_input(
"Data dos Jogos",
value=datetime.now()
)

jogos = carregar_jogos(data_sel.strftime("%Y-%m-%d"))

if jogos:

    ligas = sorted(list(set([j["tournament"]["name"] for j in jogos])))

    liga_sel = st.multiselect("Ligas",ligas)

    jogos_filtrados = [j for j in jogos if j["tournament"]["name"] in liga_sel] if liga_sel else jogos

    lista = {
    f"[{formatar_hora(j.get('startTimestamp'))}] {j['homeTeam']['name']} x {j['awayTeam']['name']}":j
    for j in jogos_filtrados
    }

    escolha = st.selectbox("Escolha o jogo",list(lista.keys()))

    jogo = lista[escolha]

    if st.button("GERAR ANÁLISE"):

        m_h,m_a = buscar_medias_reais(

        jogo["tournament"]["id"],
        jogo["season"]["id"],
        jogo["homeTeam"]["id"],
        jogo["awayTeam"]["id"]
        )

        st.markdown("---")

        col1,col2,col3 = st.columns([2,1,2])

        with col1:

            st.image(jogo["homeTeam"]["logo"],width=80)

            st.subheader(jogo["homeTeam"]["name"])

            st.write("Média gols:",m_h)

        with col2:

            st.markdown("<div class='header-vs'>VS</div>",unsafe_allow_html=True)

        with col3:

            st.image(jogo["awayTeam"]["logo"],width=80)

            st.subheader(jogo["awayTeam"]["name"])

            st.write("Média gols:",m_a)

        m_total = m_h+m_a

        p_c,p_e,p_f = prever_1x2(m_h,m_a)

        st.markdown("### Probabilidade Resultado")

        st.bar_chart({
        "Casa":[p_c],
        "Empate":[p_e],
        "Fora":[p_f]
        })

        st.markdown("### Mercados")

        c1,c2,c3 = st.columns(3)

        with c1:

            st.metric("Over 1.5",f"{calcular_poisson(m_total,1):.1f}%")

            st.metric("Over 2.5",f"{calcular_poisson(m_total,2):.1f}%")

        with c2:

            st.metric("BTTS SIM",f"{calcular_btts(m_h,m_a):.1f}%")

        with c3:

            st.metric("Cartões Over 3.5","62%")

        st.markdown("### Placares Mais Prováveis")

        placares = simulacao_montecarlo(m_h,m_a)

        for p,q in placares:

            prob = q/5000*100

            st.write(f"{p} → {prob:.1f}%")

        st.markdown("### Calculadora EV")

        odd = st.number_input("Odd",1.01,10.0,1.90)

        prob = calcular_poisson(m_total,2)/100

        ev = (prob*(odd-1))-(1-prob)

        st.metric("Valor Esperado",f"{ev*100:.2f}%")

else:

    st.warning("Nenhum jogo encontrado")
