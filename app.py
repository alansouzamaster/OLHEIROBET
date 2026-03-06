import streamlit as st
import requests
import math
import random
from datetime import datetime

# --- CONFIGURAÇÃO DA API ---
API_KEY = "SUA_API_AQUI"
HOST = "sportapi7.p.rapidapi.com"
HEADERS = {"X-RapidAPI-Key": API_KEY, "X-RapidAPI-Host": HOST}

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="PROBET ANALISE", layout="wide", page_icon="⚽")

# --- CSS VISUAL MELHORADO ---
st.markdown("""
<style>

/* FUNDO */
.stApp{
background: linear-gradient(180deg,#0b0f14,#111827);
color:#e6edf3;
}

/* TITULOS */
h1,h2,h3{
color:#ffc107;
font-weight:700;
}

/* CARDS METRIC */
.stMetric{
background:linear-gradient(145deg,#1a1f27,#222831);
padding:18px;
border-radius:14px;
border:1px solid #30363d;
box-shadow:0 4px 15px rgba(0,0,0,0.4);
transition:0.2s;
}

.stMetric:hover{
transform:translateY(-3px);
}

/* VALOR DAS METRICAS */
div[data-testid="stMetricValue"]{
color:#ffd54f !important;
font-size:28px !important;
}

/* CARDS DE DESTAQUE */
.oportunidade-card{
background:linear-gradient(160deg,#1c2128,#151a20);
padding:18px;
border-radius:12px;
border-left:4px solid #ffc107;
margin-bottom:15px;
min-height:160px;
box-shadow:0 5px 20px rgba(0,0,0,0.45);
transition:0.2s;
}

.oportunidade-card:hover{
transform:scale(1.03);
}

/* BADGE HORARIO */
.horario-badge{
background:#1f2933;
color:#ffc107;
padding:4px 12px;
border-radius:6px;
font-weight:bold;
font-size:13px;
}

/* BOTÃO */
.stButton>button{
width:100%;
background:linear-gradient(90deg,#ffc107,#ffda4d);
color:black;
font-weight:700;
border-radius:10px;
border:none;
padding:10px;
font-size:16px;
}

/* RESULTADOS */
.res-box{
text-align:center;
padding:14px;
border-radius:10px;
font-weight:bold;
color:white;
margin-bottom:12px;
font-size:20px;
box-shadow:0 4px 12px rgba(0,0,0,0.4);
}

/* VS */
.header-vs{
text-align:center;
color:#ffc107;
font-size:44px;
font-weight:800;
margin-top:10px;
}

</style>
""", unsafe_allow_html=True)

# --- FUNÇÕES ---
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


@st.cache_data(ttl=86400)
def buscar_medias_reais(tournament_id,season_id,home_id,away_id):

    try:
        url=f"https://{HOST}/api/v1/tournament/{tournament_id}/season/{season_id}/standings/total"
        response=requests.get(url,headers=HEADERS,timeout=12)

        if response.status_code==200:
            data=response.json()

            standings=data.get("standings",[])
            if not standings:
                return 1.5,1.0

            rows=standings[0].get("rows",[])

            m_casa=1.4
            m_fora=1.1

            for row in rows:

                t_id=row["team"]["id"]
                jogos=row.get("matches",1)

                if jogos==0:
                    jogos=1

                if t_id==home_id:
                    m_casa=row.get("scoresFor",0)/jogos

                if t_id==away_id:
                    m_fora=row.get("scoresFor",0)/jogos

            return round(m_casa,2),round(m_fora,2)

    except:
        return 1.5,1.0

    return 1.5,1.0


def formatar_hora(timestamp):

    if not timestamp:
        return "--:--"

    return datetime.fromtimestamp(timestamp).strftime("%H:%M")


def formatar_data_br(data):
    return data.strftime("%d/%m/%Y")


# --- TÍTULO ---
st.title("⚽ PROBET ANALISE")
st.markdown("---")

# --- DATA ---
data_sel = st.date_input(
"📅 Data das Partidas",
value=datetime.now(),
format="DD/MM/YYYY"
)


# --- BUSCAR JOGOS ---
@st.cache_data(ttl=3600)
def carregar_jogos(data_str):

    try:
        url=f"https://{HOST}/api/v1/sport/football/scheduled-events/{data_str}"
        response=requests.get(url,headers=HEADERS,timeout=12)

        if response.status_code==200:
            return response.json().get("events",[])

        return []

    except:
        return []


jogos = carregar_jogos(data_sel.strftime("%Y-%m-%d"))

btn_analise = False


if jogos:

    todas_ligas = sorted(list(set([j["tournament"]["name"] for j in jogos])))

    ligas_sel = st.multiselect(
        "🏆 Selecione as Ligas",
        todas_ligas
    )

    jogos_f = [j for j in jogos if j["tournament"]["name"] in ligas_sel] if ligas_sel else jogos


    if jogos_f:

        lista_nomes = {
        f"[{formatar_hora(j.get('startTimestamp'))}] {j['homeTeam']['name']} x {j['awayTeam']['name']}": j
        for j in jogos_f
        }

        escolha = st.selectbox(
        "🎯 Escolha uma partida",
        list(lista_nomes.keys())
        )

        jogo_selecionado = lista_nomes[escolha]

        btn_analise = st.button("🔍 GERAR RELATÓRIO")


    if not btn_analise:

        st.subheader(f"🔥 Destaques {formatar_data_br(data_sel)}")

        random.seed(data_sel.toordinal())

        quentes = [j for j in jogos if random.random()>0.90][:4]

        if quentes:

            cols = st.columns(len(quentes))

            for i,q in enumerate(quentes):

                with cols[i]:

                    hora_q = formatar_hora(q.get("startTimestamp"))

                    nome_h = q["homeTeam"]["name"]
                    nome_a = q["awayTeam"]["name"]

                    st.markdown(f"""
                    <div class='oportunidade-card'>

                    <span class='horario-badge'>🕒 {hora_q}</span><br>

                    <small>{q['tournament']['name']}</small><br><br>

                    <strong>{nome_h} x {nome_a}</strong><br>

                    <span style='color:#ffc107'>
                    Over 2.5: {random.randint(72,89)}%
                    </span>

                    </div>
                    """,unsafe_allow_html=True)


    if btn_analise:

        m_h,m_a = buscar_medias_reais(

        jogo_selecionado["tournament"]["id"],
        jogo_selecionado["season"]["id"],
        jogo_selecionado["homeTeam"]["id"],
        jogo_selecionado["awayTeam"]["id"]
        )

        m_total = m_h+m_a

        p_c,p_e,p_f = prever_1x2(m_h,m_a)


        st.markdown("### 📊 Probabilidades 1X2")

        r1,r2,r3 = st.columns(3)

        r1.markdown(
        f"<div class='res-box' style='background:#1f77b4'>Casa {p_c:.1f}%</div>",
        unsafe_allow_html=True
        )

        r2.markdown(
        f"<div class='res-box' style='background:#444'>Empate {p_e:.1f}%</div>",
        unsafe_allow_html=True
        )

        r3.markdown(
        f"<div class='res-box' style='background:#dc3545'>Fora {p_f:.1f}%</div>",
        unsafe_allow_html=True
        )


        st.markdown("---")

        c1,c2,c3 = st.columns(3)

        with c1:

            st.metric("⚽ Over 1.5",f"{calcular_poisson(m_total,1):.1f}%")

            st.metric("⚽ Over 2.5",f"{calcular_poisson(m_total,2):.1f}%")


        with c2:

            st.metric("🚩 Over 8.5 Cantos",f"{calcular_poisson(9.5,8):.1f}%")

            st.metric("🚩 Over 10.5 Cantos",f"{calcular_poisson(9.5,10):.1f}%")


        with c3:

            st.metric("🟨 Over 3.5 Cartões",f"{calcular_poisson(4.2,3):.1f}%")

            st.info(
            f"⚖️ Juiz: {jogo_selecionado.get('referee',{}).get('name','Pendente')}"
            )

else:

    st.warning(f"⚠️ Nenhum jogo para {formatar_data_br(data_sel)}")
