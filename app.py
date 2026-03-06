import streamlit as st
import requests
import math
from datetime import datetime, timedelta

# --- CONFIGURAÇÃO DA API ---
API_KEY = "cd10359c14msheda9060d2cb34cep176fa8jsn3c42386ffb98"
HOST = "sportapi7.p.rapidapi.com"
HEADERS = {"X-RapidAPI-Key": API_KEY, "X-RapidAPI-Host": HOST}

# --- INICIALIZAÇÃO DE ESTADO ---
if 'analise_pronta' not in st.session_state:
    st.session_state.analise_pronta = False
    st.session_state.jogo_selecionado = None

# --- FUNÇÕES DE CÁLCULO ---
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

@st.cache_data(ttl=600)
def carregar_jogos(d):
    try:
        url = f"https://{HOST}/api/v1/sport/football/scheduled-events/{d}"
        res = requests.get(url, headers=HEADERS, timeout=12)
        return res.json().get('events', []) if res.status_code == 200 else []
    except: return []

# --- INTERFACE ---
st.set_page_config(page_title="PROBET v7.0", layout="wide")

# CSS para melhorar o visual dos containers nativos
st.markdown("""
<style>
    .stApp { background-color: #0b0e11; color: white; }
    div[data-testid="stVerticalBlock"] > div {
        background-color: #161b22;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #30363d;
    }
    h1, h2, h3 { color: #ffc107 !important; text-align: center; }
    .stProgress > div > div > div > div { background-color: #28a745; }
</style>
""", unsafe_allow_html=True)

st.title("⚽ PROBET ANALISE")

# --- FILTROS ---
data_sel = st.date_input("📅 Data das Partidas", value=datetime.now())
jogos = carregar_jogos(data_sel.strftime('%Y-%m-%d'))

if jogos:
    ligas = sorted(list(set([j['tournament']['name'] for j in jogos])))
    ligas_sel = st.multiselect("🏆 Selecione as Ligas", ligas)
    jogos_f = [j for j in jogos if j['tournament']['name'] in ligas_sel] if ligas_sel else jogos
    
    if jogos_f:
        opcoes = {f"[{ajustar_horario(j.get('startTimestamp', 0))}] {j['homeTeam']['name']} x {j['awayTeam']['name']}": j for j in jogos_f}
        escolha = st.selectbox("🎯 Escolha uma partida:", list(opcoes.keys()))
        
        if st.button("🔍 GERAR RELATÓRIO PREDITIVO"):
            st.session_state.jogo_selecionado = opcoes[escolha]
            st.session_state.analise_pronta = True

# --- EXIBIÇÃO ---
if st.session_state.analise_pronta and st.session_state.jogo_selecionado:
    j = st.session_state.jogo_selecionado
    st.divider()
    
    st.header(f"{j['homeTeam']['name']} vs {j['awayTeam']['name']}")
    st.write(f"**Competição:** {j['tournament']['name']} | **Horário:** {ajustar_horario(j.get('startTimestamp', 0))} (Brasília)")

    # 1X2 Probabilidades com st.columns
    st.subheader("📊 Probabilidades 1X2")
    c1, c2, c3 = st.columns(3)
    c1.metric("Casa", "65.0%")
    c2.metric("Empate", "26.0%")
    c3.metric("Fora", "9.0%")

    st.divider()

    # Mercados com Componentes Nativos (Sem risco de mostrar código)
    m_total = 2.8 # Média base para cálculos
    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("⚽ GOLS")
        
        # Over 1.5
        p15 = calcular_poisson(m_total, 1)
        st.write(f"**Over 1.5 Gols:** {p15:.1f}%")
        st.progress(p15/100)
        
        # Over 2.5
        p25 = calcular_poisson(m_total, 2)
        st.write(f"**Over 2.5 Gols:** {p25:.1f}%")
        st.progress(p25/100)

    with col2:
        st.subheader("🚩 CANTOS")
        
        # Over 5.5
        c55 = calcular_poisson(9.5, 5)
        st.write(f"**Over 5.5 Cantos:** {c55:.1f}%")
        st.progress(c55/100)
        
        # Over 8.5
        c85 = calcular_poisson(9.5, 8)
        st.write(f"**Over 8.5 Cantos:** {c85:.1f}%")
        st.progress(c85/100)

    with col3:
        st.subheader("🟨 CARTÕES")
        
        # Over 1.5
        ct15 = calcular_poisson(4.2, 1)
        st.write(f"**Over 1.5 Cartões:** {ct15:.1f}%")
        st.progress(ct15/100)
        
        # Over 3.5
        ct35 = calcular_poisson(4.2, 3)
        st.write(f"**Over 3.5 Cartões:** {ct35:.1f}%")
        st.progress(ct35/100)

    if st.button("🗑️ LIMPAR ANÁLISE"):
        st.session_state.analise_pronta = False
        st.rerun()

elif not jogos:
    st.info("Nenhum jogo encontrado para esta data.")
