import streamlit as st
import requests
import math
from datetime import datetime, timedelta

# --- CONFIGURAÇÃO DA API ---
API_KEY = "f156796042mshc79c7a43c6d7ac5p1d957fjsn2d444cafcca1"
HOST = "sportapi7.p.rapidapi.com"
HEADERS = {"X-RapidAPI-Key": API_KEY, "X-RapidAPI-Host": HOST}

# --- FUNÇÕES TÉCNICAS (POISSON E API) ---
def ajustar_horario(timestamp):
    dt_utc = datetime.fromtimestamp(timestamp)
    dt_br = dt_utc - timedelta(hours=3)
    return dt_br.strftime('%H:%M')

def calcular_poisson(media, alvo):
    if media <= 0: return 0
    prob_acumulada = 0
    for i in range(int(alvo) + 1):
        prob_i = (math.exp(-media) * (media**i)) / math.factorial(i)
        prob_acumulada += prob_i
    return (1 - prob_acumulada) * 100

@st.cache_data(ttl=3600)
def buscar_dados_l10(team_id):
    try:
        url = f"https://{HOST}/api/v1/team/{team_id}/events/last/0"
        res = requests.get(url, headers=HEADERS, timeout=12)
        if res.status_code == 200:
            events = res.json().get('events', [])[:10]
            if not events: return 1.5, 1.2, []
            marcados = sofridos = 0
            sequencia = []
            for ev in events:
                h_score = ev.get('homeScore', {}).get('current', 0)
                a_score = ev.get('awayScore', {}).get('current', 0)
                if ev['homeTeam']['id'] == team_id:
                    marcados += h_score; sofridos += a_score
                    res_tipo = "V" if h_score > a_score else ("E" if h_score == a_score else "D")
                else:
                    marcados += a_score; sofridos += h_score
                    res_tipo = "V" if a_score > h_score else ("E" if a_score == h_score else "D")
                sequencia.append(res_tipo)
            return (marcados/len(events)), (sofridos/len(events)), sequencia
    except: pass
    return 1.5, 1.2, []

def calcular_placar_exato(media_h, media_a):
    placar_prob = []
    for h in range(4):
        for a in range(4):
            prob = (math.exp(-media_h) * (media_h**h) / math.factorial(h)) * \
                   (math.exp(-media_a) * (media_a**a) / math.factorial(a))
            placar_prob.append((h, a, prob * 100))
    return sorted(placar_prob, key=lambda x: x[2], reverse=True)[:3]

# --- DESIGN SYSTEM R20 ---
st.set_page_config(page_title="PROBET R20 EDITION", layout="wide")

st.markdown("""
<style>
    /* Fundo Escuro R20 */
    .stApp { background-color: #0d1117; color: #e6edf3; }
    
    /* Fontes e Cabeçalhos */
    h1, h2, h3 { font-family: 'Inter', sans-serif; font-weight: 800; letter-spacing: -1px; }
    .main-title { color: #58a6ff; text-align: center; font-size: 2.5rem; margin-bottom: 20px; text-shadow: 0 0 20px rgba(88, 166, 255, 0.4); }

    /* Cards R20 Score Style */
    .r20-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 4px 24px rgba(0,0,0,0.5);
    }
    
    /* Barra de Progresso Customizada */
    .progress-container { width: 100%; background-color: #30363d; border-radius: 10px; height: 8px; margin: 10px 0 20px 0; }
    .progress-bar { height: 100%; border-radius: 10px; transition: width 0.5s ease-in-out; }
    
    /* Badges de Resultado (V-E-D) */
    .badge { padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: bold; margin-right: 4px; }
    .win { background: #238636; color: white; }
    .draw { background: #6e7681; color: white; }
    .loss { background: #da3633; color: white; }

    /* Palpite Sugerido Neon */
    .r20-prediction {
        background: linear-gradient(90deg, #1f1b2e 0%, #2d1b4d 100%);
        border-left: 5px solid #bf7af0;
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        margin-top: 30px;
    }
</style>
""", unsafe_allow_html=True)

# --- APP LOGIC ---
st.markdown("<h1 class='main-title'>PROBET <span style='color:white'>R20 SCORE</span></h1>", unsafe_allow_html=True)

data_sel = st.date_input("📅 Selecione a Data", value=datetime.now())
res_jogos = requests.get(f"https://{HOST}/api/v1/sport/football/scheduled-events/{data_sel.strftime('%Y-%m-%d')}", headers=HEADERS).json()
jogos = res_jogos.get('events', [])

if jogos:
    opcoes = {f"[{ajustar_horario(j.get('startTimestamp', 0))}] {j['homeTeam']['name']} x {j['awayTeam']['name']}": j for j in jogos}
    escolha = st.selectbox("🎯 Escolha a Partida", list(opcoes.keys()))
    
    if st.button("GERAR ANÁLISE R20"):
        j = opcoes[escolha]
        h_m, h_s, h_seq = buscar_dados_l10(j['homeTeam']['id'])
        a_m, a_s, a_seq = buscar_dados_l10(j['awayTeam']['id'])
        
        # --- HEADER R20 ---
        st.markdown("<div class='r20-card'>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([2, 1, 2])
        
        with col1:
            st.markdown(f"<h3 style='text-align:right'>{j['homeTeam']['name']}</h3>", unsafe_allow_html=True)
            forma_h = "".join([f"<span class='badge {'win' if r=='V' else 'draw' if r=='E' else 'loss'}'>{r}</span>" for r in h_seq[::-1]])
            st.markdown(f"<div style='text-align:right'>{forma_h}</div>", unsafe_allow_html=True)
            st.markdown(f"<p style='text-align:right; color:#8b949e'>Média Gols: {h_m:.1f}</p>", unsafe_allow_html=True)

        with col2:
            st.markdown("<h1 style='text-align:center; color:#58a6ff'>VS</h1>", unsafe_allow_html=True)
            st.markdown(f"<p style='text-align:center; font-weight:bold'>{ajustar_horario(j.get('startTimestamp', 0))}</p>", unsafe_allow_html=True)

        with col3:
            st.markdown(f"<h3>{j['awayTeam']['name']}</h3>", unsafe_allow_html=True)
            forma_a = "".join([f"<span class='badge {'win' if r=='V' else 'draw' if r=='E' else 'loss'}'>{r}</span>" for r in a_seq[::-1]])
            st.markdown(f"<div>{forma_a}</div>", unsafe_allow_html=True)
            st.markdown(f"<p style='color:#8b949e'>Média Gols: {a_m:.1f}</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # --- PROBABILIDADES 1X2 ---
        st.markdown("### 📊 Probabilidades de Resultado")
        p_c = 45 + (h_m - a_m)*10; p_f = 25 + (a_m - h_m)*10; p_e = 100 - p_c - p_f
        
        c1, c2, c3 = st.columns(3)
        for label, prob, cor in zip([j['homeTeam']['shortName'], "Empate", j['awayTeam']['shortName']], [p_c, p_e, p_f], ["#58a6ff", "#6e7681", "#ff7b72"]):
            with c1 if label == j['homeTeam']['shortName'] else c2 if label == "Empate" else c3:
                st.markdown(f"**{label}** <span style='float:right; color:{cor}'>{prob:.1f}%</span>", unsafe_allow_html=True)
                st.markdown(f"<div class='progress-container'><div class='progress-bar' style='width:{prob}%; background-color:{cor}'></div></div>", unsafe_allow_html=True)

        # --- PLACAR EXATO ---
        st.markdown("<div class='r20-card'>", unsafe_allow_html=True)
        st.markdown("<h4>🏆 Top Placares Prováveis</h4>", unsafe_allow_html=True)
        placares = calcular_placar_exato(h_m, a_m)
        pc1, pc2, pc3 = st.columns(3)
        for i, p in enumerate(placares):
            with [pc1, pc2, pc3][i]:
                st.markdown(f"<div style='background:#0d1117; padding:15px; border-radius:12px; text-align:center; border:1px solid #30363d'><b>{p[0]} - {p[1]}</b><br><span style='color:#58a6ff'>{p[2]:.1f}%</span></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # --- MERCADOS ---
        m1, m2, m3 = st.columns(3)
        with m1:
            st.markdown("<div class='r20-card'>", unsafe_allow_html=True)
            st.markdown("**⚽ Over 1.5 Gols**", unsafe_allow_html=True)
            p15 = calcular_poisson(h_m + a_m, 1)
            st.markdown(f"<div class='progress-container'><div class='progress-bar' style='width:{p15}%; background-color:#238636'></div></div>", unsafe_allow_html=True)
            st.write(f"Chance: {p15:.1f}%")
            st.markdown("</div>", unsafe_allow_html=True)

        # --- PALPITE R20 ---
        st.markdown(f"""
            <div class='r20-prediction'>
                <p style='color:#bf7af0; font-weight:bold; text-transform:uppercase; margin:0'>Palpite Recomendado</p>
                <h2 style='margin:10px 0; color:white'>{'Over 1.5 Gols' if p15 > 75 else 'Vitória ' + j['homeTeam']['name'] if p_c > 55 else 'Aguardar Live'}</h2>
                <p style='color:#8b949e; font-size:12px'>Análise baseada no algoritmo R20 Score V13</p>
            </div>
        """, unsafe_allow_html=True)

else:
    st.info("Nenhum jogo encontrado para esta data.")

