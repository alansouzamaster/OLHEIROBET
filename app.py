import streamlit as st
import requests
from datetime import date

# ----------------------------
# CONFIG
# ----------------------------

st.set_page_config(
    page_title="PROBET ANALISE PRO",
    layout="wide"
)

API_KEY = "a19cf6b5fcmsh62790bdb0d293ddp131982jsn24158e88f703"
HOST = "api-football-v1.p.rapidapi.com"

HEADERS = {
    "x-rapidapi-key": API_KEY,
    "x-rapidapi-host": HOST
}

# ----------------------------
# CSS VISUAL
# ----------------------------

st.markdown("""
<style>

body {
    background: linear-gradient(90deg,#020617,#0f172a);
}

.titulo {
    font-size:40px;
    font-weight:700;
    color:white;
}

.card {
    background:#0f172a;
    padding:20px;
    border-radius:12px;
    border:1px solid #1e293b;
    margin-bottom:15px;
}

.time {
    font-size:22px;
    font-weight:600;
}

.liga {
    color:#94a3b8;
}

</style>
""", unsafe_allow_html=True)

# ----------------------------
# TÍTULO
# ----------------------------

st.markdown(
    "<div class='titulo'>⚽ PROBET ANALISE PRO</div>",
    unsafe_allow_html=True
)

st.write("")

# ----------------------------
# DATA
# ----------------------------

data = st.date_input("Data dos Jogos", date.today())

data_api = data.strftime("%Y-%m-%d")

# ----------------------------
# FUNÇÃO API
# ----------------------------

def carregar_jogos(data):

    url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"

    query = {"date": data}

    try:

        response = requests.get(
            url,
            headers=HEADERS,
            params=query,
            timeout=20
        )

        data = response.json()

        return data["response"]

    except:
        return []

# ----------------------------
# BUSCAR JOGOS
# ----------------------------

jogos = carregar_jogos(data_api)

# ----------------------------
# RESULTADO
# ----------------------------

if len(jogos) == 0:

    st.warning("Nenhum jogo encontrado")

else:

    st.success(f"{len(jogos)} jogos encontrados")

    for jogo in jogos:

        liga = jogo["league"]["name"]

        casa = jogo["teams"]["home"]["name"]
        fora = jogo["teams"]["away"]["name"]

        horario = jogo["fixture"]["date"][11:16]

        st.markdown(f"""
        <div class="card">

        <div class="liga">{liga}</div>

        <div class="time">
        {casa}  vs  {fora}
        </div>

        <div>
        🕒 {horario}
        </div>

        </div>
        """, unsafe_allow_html=True)
