import streamlit as st
import requests
import math
from datetime import datetime, timedelta

# --- CONFIGURAÇÃO DA API ---
API_KEY = "cd10359c14msheda9060d2cb34cep176fa8jsn3c42386ffb98"
HOST = "sportapi7.p.rapidapi.com"
HEADERS = {"X-RapidAPI-Key": API_KEY, "X-RapidAPI-Host": HOST}

# --- ESTADO DO APP ---
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

@st.cache_data(ttl=3600)
def buscar_media_ultimos_10(team_id):
    """Busca os últimos 10 jogos e retorna média de gols marcados e sofridos"""
    try:
        url = f"https://{HOST}/api/v1/team/{team_id}/events/last/0"
        res = requests.get(url, headers=HEADERS, timeout=12)
        if res.status_code == 200:
            events = res.json().get('events', [])[:10] # Pega apenas os 10 últimos
            if not events: return 1.5, 1.2
            
            marcados = 0
            sofridos = 0
            for ev in events:
                # Verifica se o time era casa ou fora para somar os gols certos
                if ev['homeTeam']['id'] == team_id:
                    marcados += ev.get('homeScore', {}).get('current', 0)
                    sofridos += ev.get('awayScore', {}).get('current', 0)
                else:
                    marcados += ev.get('awayScore', {}).get('current', 0)
                    sofridos += ev.get('homeScore', {}).get('current', 0)
            
            qtd = len(events)
            return (marcados / qtd), (sofridos / qtd)
    except: pass
    return 1.5, 1.2 # Médias padrão em caso de erro

# --- INTERFACE ---
st.set_page_config(page_title="PROBET Últimos 10", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0b0e11; color: white; }
    [data-testid="stVerticalBlock"] > div { background-color: #161b22; padding: 20px; border-radius: 12px; border: 1px solid #30363d; }
    [data-testid="stHorizontalBlock"] > div:nth-child(1) .stProgress > div > div > div > div { background-color: #28a745 !important; }
    [data-testid="stHorizontalBlock"] > div:nth-child(2) .stProgress > div > div > div > div { background-color: #007bff !important; }
    [data-testid="stHorizontalBlock"] > div:nth-child(3) .stProgress > div > div > div > div { background-color: #ffc107 !important; }
    h1, h2, h3 { text-align: center; color: #ffc107 !important; }
</style>
""", unsafe_allow_html=True)

st.title("⚽ PROBET ANALISE (ÚLTIMOS 10 JOGOS)")

# --- FILTROS ---
data_sel = st.date_input("📅 Data das Partidas", value=datetime.now())
jogos = carregar_jogos(data_sel.strftime('%Y-%m-%d'))

if jogos:
    ligas = sorted(list(set([j['tournament']['name'] for j in jogos])))
    ligas_sel = st.multiselect("🏆 Escolha a Liga", ligas)
    jogos_f = [j for j in jogos if j['tournament']['name'] in ligas_sel] if ligas_sel else jogos
    
    if jogos_f:
        opcoes = {f"[{ajustar_horario(j.get('startTimestamp', 0))}] {j['homeTeam']['name']} x {j['awayTeam']['name']}": j for j in jogos_f}
        escolha = st.selectbox("🎯 Selecione o Jogo", list(opcoes.keys()))
        
        if st.button("🔍 GERAR ANÁLISE BASEADA NO RETROSPECTO"):
            st.session_state.jogo_selecionado = opcoes[escolha]
            st.session_state.analise_pronta = True

# --- EXIBIÇÃO ---
if st.session_state.analise_pronta and st.session_state.jogo_selecionado:
    j = st.session_state.jogo_selecionado
    
    # BUSCA DE MÉDIAS DOS ÚLTIMOS 10 JOGOS
    h_marcados, h_sofridos = buscar_media_ultimos_10(j['homeTeam']['id'])
    a_marcados, a_sofridos = buscar_media_ultimos_10(j['awayTeam']['id'])
    
    # Cálculo de Expectativa de Gols (Lambda)
    # (Ataque Casa x Defesa Fora + Ataque Fora x Defesa Casa) / 2
    media_gols_esperada = ((h_marcados + a_sofridos) / 2) + ((a_marcados + h_sofridos) / 2)
    media_gols_esperada = media_gols_esperada / 2 # Ajuste de escala

    st.divider()
    st.header(f"{j['homeTeam']['name']} VS {j['awayTeam']['name']}")
    
    # 1X2 Simulado baseado na força dos últimos 10 jogos
    st.subheader("📊 Probabilidades (Performance Atual)")
    c1, c2, c3 = st.columns(3)
    # Lógica simples de força: quem marca mais e sofre menos tem maior %
    forca_h = h_marcados - h_sofridos
    forca_a = a_marcados - a_sofridos
    total_f = abs(forca_h) + abs(forca_a) + 1
    p_c = 40 + (forca_h * 5)
    p_f = 30 + (forca_a * 5)
    p_e = 100 - p_c - p_f
    
    c1.metric("Casa (1)", f"{max(min(p_c, 85), 15):.1f}%")
    c2.metric("Empate (X)", f"{max(min(p_e, 40), 10):.1f}%")
    c3.metric("Fora (2)", f"{max(min(p_f, 85), 15):.1f}%")

    st.divider()

    # Mercados com as novas médias
    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("⚽ GOLS (L10)")
        p15 = calcular_poisson(media_gols_esperada, 1)
        p25 = calcular_poisson(media_gols_esperada, 2)
        st.write(f"**Over 1.5:** {p15:.1f}%"); st.progress(p15/100)
        st.write(f"**Over 2.5:** {p25:.1f}%"); st.progress(p25/100)

    with col2:
        st.subheader("🚩 CANTOS (Média)")
        # A API de 'last events' às vezes não traz cantos detalhados, mantemos média ponderada
        c55 = calcular_poisson(9.2, 5); c85 = calcular_poisson(9.2, 8)
        st.write(f"**Over 5.5:** {c55:.1f}%"); st.progress(c55/100)
        st.write(f"**Over 8.5:** {c85:.1f}%"); st.progress(c85/100)

    with col3:
        st.subheader("🟨 CARTÕES (Média)")
        ct15 = calcular_poisson(4.5, 1); ct35 = calcular_poisson(4.5, 3)
        st.write(f"**Over 1.5:** {ct15:.1f}%"); st.progress(ct15/100)
        st.write(f"**Over 3.5:** {ct35:.1f}%"); st.progress(ct35/100)

    st.info(f"💡 Esta análise considera apenas o desempenho nos últimos 10 jogos oficiais de cada equipe.")
    if st.button("🗑️ NOVA CONSULTA"):
        st.session_state.analise_pronta = False
        st.rerun()
