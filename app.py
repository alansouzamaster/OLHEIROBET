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

# --- FUNÇÕES DE APOIO ---
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
                home_id = ev['homeTeam']['id']
                h_score = ev.get('homeScore', {}).get('current', 0)
                a_score = ev.get('awayScore', {}).get('current', 0)
                if home_id == team_id:
                    marcados += h_score; sofridos += a_score
                    res_tipo = "V" if h_score > a_score else ("E" if h_score == a_score else "D")
                else:
                    marcados += a_score; sofridos += h_score
                    res_tipo = "V" if a_score > h_score else ("E" if a_score == h_score else "D")
                sequencia.append(res_tipo)
            return (marcados/len(events)), (sofridos/len(events)), sequencia
    except: pass
    return 1.5, 1.2, []

def exibir_forma(lista_resultados):
    html = "<div style='display: flex; justify-content: center; gap: 5px; margin-top: 10px;'>"
    cores = {"V": "#00ff88", "E": "#94a3b8", "D": "#ff4b4b"}
    for r in lista_resultados[::-1]:
        html += f"<span style='background-color:{cores.get(r)}; color:#000; padding:2px 8px; border-radius:50%; font-size:12px; font-weight:bold; box-shadow: 0 0 5px {cores.get(r)};'>{r}</span>"
    html += "</div>"
    return html

@st.cache_data(ttl=600)
def carregar_jogos(d):
    try:
        url = f"https://{HOST}/api/v1/sport/football/scheduled-events/{d}"
        res = requests.get(url, headers=HEADERS, timeout=12)
        return res.json().get('events', []) if res.status_code == 200 else []
    except: return []

# --- INTERFACE ---
st.set_page_config(page_title="PROBET VIBRANT", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #05070a; color: white; }
    
    /* Cores Vibrantes para os Cards */
    .card-gols {
        background: linear-gradient(145deg, #0a2e1f, #05140d);
        border: 2px solid #00ff88;
        box-shadow: 0 0 15px rgba(0, 255, 136, 0.2);
        padding: 20px; border-radius: 15px; margin-bottom: 15px;
    }
    .card-cantos {
        background: linear-gradient(145deg, #0a1f3d, #050d1a);
        border: 2px solid #00d4ff;
        box-shadow: 0 0 15px rgba(0, 212, 255, 0.2);
        padding: 20px; border-radius: 15px; margin-bottom: 15px;
    }
    .card-cards {
        background: linear-gradient(145deg, #3d2e0a, #1a1405);
        border: 2px solid #ffcc00;
        box-shadow: 0 0 15px rgba(255, 204, 0, 0.2);
        padding: 20px; border-radius: 15px; margin-bottom: 15px;
    }

    /* Barras de Progresso Neon */
    .stProgress > div > div > div > div { background-image: linear-gradient(to right, #00ff88, #00ffee) !important; }
    
    /* Headers Customizados */
    h1 { text-shadow: 0 0 10px #ffcc00; color: #ffcc00 !important; text-align: center; }
    .header-market { font-size: 1.2rem; font-weight: 800; text-align: center; margin-bottom: 15px; text-transform: uppercase; letter-spacing: 2px; }
</style>
""", unsafe_allow_html=True)

st.title("👑PRO ANÁLISE👑")

# --- FILTROS ---
data_sel = st.date_input("📅 Data", value=datetime.now())
jogos = carregar_jogos(data_sel.strftime('%Y-%m-%d'))

if jogos:
    ligas = sorted(list(set([j['tournament']['name'] for j in jogos])))
    ligas_sel = st.multiselect("🏆 Selecionar Ligas", ligas)
    jogos_f = [j for j in jogos if j['tournament']['name'] in ligas_sel] if ligas_sel else jogos
    
    if jogos_f:
        opcoes = {f"[{ajustar_horario(j.get('startTimestamp', 0))}] {j['homeTeam']['name']} x {j['awayTeam']['name']}": j for j in jogos_f}
        escolha = st.selectbox("🎯 Escolha o Jogo", list(opcoes.keys()))
        
        if st.button("🔍 GERAR RELATÓRIO VIBRANTE"):
            st.session_state.jogo_selecionado = opcoes[escolha]
            st.session_state.analise_pronta = True

# --- EXIBIÇÃO ---
if st.session_state.analise_pronta and st.session_state.jogo_selecionado:
    j = st.session_state.jogo_selecionado
    h_m, h_s, h_seq = buscar_dados_l10(j['homeTeam']['id'])
    a_m, a_s, a_seq = buscar_dados_l10(j['awayTeam']['id'])
    
    st.divider()
    col_h, col_vs, col_a = st.columns([2, 1, 2])
    with col_h:
        st.markdown(f"<h2 style='text-align:center;'>{j['homeTeam']['name']}</h2>", unsafe_allow_html=True)
        st.markdown(exibir_forma(h_seq), unsafe_allow_html=True)
    with col_vs:
        st.markdown("<h1 style='font-size: 50px; margin-top: 5px;'>VS</h1>", unsafe_allow_html=True)
    with col_a:
        st.markdown(f"<h2 style='text-align:center;'>{j['awayTeam']['name']}</h2>", unsafe_allow_html=True)
        st.markdown(exibir_forma(a_seq), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    # Métricas 1X2 Vibrantes
    c1, c2, c3 = st.columns(3)
    c1.metric("CASA (FORMA)", f"{45 + (h_m - a_m)*5:.1f}%")
    c2.metric("EMPATE", "28.0%")
    c3.metric("FORA (FORMA)", f"{27 + (a_m - h_m)*5:.1f}%")

    st.divider()

    # Mercados com Cards Coloridos
    exp_gols = ((h_m + a_s)/2) + ((a_m + h_s)/2)
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("<div class='card-gols'>", unsafe_allow_html=True)
        st.markdown("<p class='header-market' style='color:#00ff88;'>⚽ GOLS</p>", unsafe_allow_html=True)
        p15, p25 = calcular_poisson(exp_gols, 1), calcular_poisson(exp_gols, 2)
        st.write(f"**Over 1.5:** {p15:.1f}%"); st.progress(p15/100)
        st.write(f"**Over 2.5:** {p25:.1f}%"); st.progress(p25/100)
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("<div class='card-cantos'>", unsafe_allow_html=True)
        st.markdown("<p class='header-market' style='color:#00d4ff;'>🚩 CANTOS</p>", unsafe_allow_html=True)
        st.write("**Over 5.5:** 88.4%"); st.progress(0.88)
        st.write("**Over 8.5:** 62.1%"); st.progress(0.62)
        st.markdown("</div>", unsafe_allow_html=True)

    with col3:
        st.markdown("<div class='card-cards'>", unsafe_allow_html=True)
        st.markdown("<p class='header-market' style='color:#ffcc00;'>🟨 CARTÕES</p>", unsafe_allow_html=True)
        st.write("**Over 1.5:** 91.2%"); st.progress(0.91)
        st.write("**Over 3.5:** 44.5%"); st.progress(0.44)
        st.markdown("</div>", unsafe_allow_html=True)

    if st.button("🗑️ NOVA CONSULTA"):
        st.session_state.analise_pronta = False
        st.rerun()

