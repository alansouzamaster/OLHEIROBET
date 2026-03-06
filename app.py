import streamlit as st
import requests
import math
from datetime import datetime

# --- CONFIGURAÇÃO DA API ---
API_KEY = "3a5c2b926bmsh18b3c4624ec302bp1911efjsn84e2922978ff"
HOST = "sportapi7.p.rapidapi.com"
HEADERS = {"X-RapidAPI-Key": API_KEY, "X-RapidAPI-Host": HOST}

# --- ESTADO DA SESSÃO ---
if 'analise_pronta' not in st.session_state:
    st.session_state.analise_pronta = False
    st.session_state.jogo_selecionado = None

# --- FUNÇÕES ---
def calcular_poisson(media, alvo):
    if media <= 0: return 0
    prob_acumulada = 0
    for i in range(int(alvo) + 1):
        prob_i = (math.exp(-media) * (media**i)) / math.factorial(i)
        prob_acumulada += prob_i
    return (1 - prob_acumulada) * 100

def get_color(prob):
    if prob >= 70: return "#28a745"
    if prob >= 50: return "#ffc107"
    return "#dc3545"

def prever_1x2_avancado(h_atq, h_def, a_atq, a_def):
    l_casa = h_atq * a_def * 1.10 
    l_fora = a_atq * h_def * 0.90 
    total = l_casa + l_fora
    p_empate = 31.0 if total < 2.2 else 26.0
    sobra = 100 - p_empate
    p_casa = sobra * (l_casa / total) if total > 0 else sobra / 2
    p_fora = sobra * (l_fora / total) if total > 0 else sobra / 2
    return p_casa, p_empate, p_fora, total

def carregar_jogos_debug(d):
    """Função com relatório de erros para diagnóstico"""
    try:
        url = f"https://{HOST}/api/v1/sport/football/scheduled-events/{d}"
        res = requests.get(url, headers=HEADERS, timeout=15)
        if res.status_code == 200:
            eventos = res.json().get('events', [])
            return eventos, "OK"
        elif res.status_code == 403:
            return [], "Erro 403: Chave API inválida ou limite atingido."
        else:
            return [], f"Erro {res.status_code}: Problema na API."
    except Exception as e:
        return [], f"Erro de Conexão: {str(e)}"

@st.cache_data(ttl=86400)
def buscar_estatisticas(t_id, s_id, h_id, a_id):
    try:
        url = f"https://{HOST}/api/v1/tournament/{t_id}/season/{s_id}/standings/total"
        res = requests.get(url, headers=HEADERS, timeout=12)
        if res.status_code == 200:
            rows = res.json().get('standings', [{}])[0].get('rows', [])
            h_atq, h_def, a_atq, a_def = 1.4, 1.2, 1.1, 1.3
            for r in rows:
                tid = r['team']['id']
                jogos = max(r.get('matches', 1), 1)
                if tid == h_id: h_atq, h_def = r.get('scoresFor', 0)/jogos, r.get('scoresAgainst', 0)/jogos
                if tid == a_id: a_atq, a_def = r.get('scoresFor', 0)/jogos, r.get('scoresAgainst', 0)/jogos
            return h_atq, h_def, a_atq, a_def
    except: pass
    return 1.4, 1.2, 1.1, 1.3

# --- INTERFACE ---
st.set_page_config(page_title="PROBET ANALISE v6.0", layout="wide")

# CSS para esconder mensagens chatas do Streamlit e melhorar visual
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #e0e0e0; }
    .res-box { text-align: center; padding: 15px; border-radius: 8px; font-weight: bold; color: white; margin-bottom: 10px; font-size: 20px; }
    .metric-container { background-color: #1c2128; padding: 15px; border-radius: 10px; border: 1px solid #30363d; margin-top: 5px; }
    .metric-row { display: flex; justify-content: space-between; margin-bottom: 8px; align-items: center; border-bottom: 1px solid #2d333b; padding-bottom: 5px; }
    </style>
    """, unsafe_allow_html=True)

st.title("⚽ PROBET ANALISE")

# --- BARRA LATERAL (CONFIG) ---
st.sidebar.header("📅 FILTRO DE DATA")
data_sel = st.sidebar.date_input("Selecione o Dia", value=datetime.now())
data_str = data_sel.strftime('%Y-%m-%d')

# --- BUSCA DE DADOS ---
jogos, status = carregar_jogos_debug(data_str)

if status != "OK":
    st.error(status)
elif not jogos:
    st.warning(f"⚠️ Nenhum jogo agendado encontrado para {data_str}. Tente selecionar outra data na barra lateral (ex: amanhã).")
else:
    # FILTRO DE LIGAS
    todas_ligas = sorted(list(set([j['tournament']['name'] for j in jogos])))
    ligas_sel = st.multiselect("🏆 1. Escolha as Ligas:", todas_ligas)
    
    # FILTRO DE TIMES
    jogos_f = [j for j in jogos if j['tournament']['name'] in ligas_sel] if ligas_sel else jogos
    
    if ligas_sel:
        lista_partidas = {f"[{datetime.fromtimestamp(j.get('startTimestamp', 0)).strftime('%H:%M')}] {j['homeTeam']['name']} x {j['awayTeam']['name']}": j for j in jogos_f}
        
        escolha = st.selectbox("🎯 2. Escolha o Jogo:", list(lista_partidas.keys()))
        
        if st.button("🔍 ANALISAR PARTIDA"):
            st.session_state.jogo_selecionado = lista_partidas[escolha]
            st.session_state.analise_pronta = True
    else:
        st.info("💡 Por favor, selecione pelo menos uma liga no menu acima para listar os jogos.")

# --- RESULTADOS ---
if st.session_state.analise_pronta and st.session_state.jogo_selecionado:
    # (O restante do código de exibição permanece igual para manter o visual Pro)
    j = st.session_state.jogo_selecionado
    st.divider()
    
    id_h, id_a = j['homeTeam']['id'], j['awayTeam']['id']
    logo_h = f"https://api.sofascore.app/api/v1/team/{id_h}/image"
    logo_a = f"https://api.sofascore.app/api/v1/team/{id_a}/image"

    h_atq, h_def, a_atq, a_def = buscar_estatisticas(j['tournament']['id'], j['season']['id'], id_h, id_a)
    p_c, p_e, p_f, m_t = prever_1x2_avancado(h_atq, h_def, a_atq, a_def)

    col1, col2, col3 = st.columns([1,3,1])
    with col1: st.image(logo_h, width=100)
    with col2: 
        st.markdown(f"<h1 style='text-align:center;'>{j['homeTeam']['name']} x {j['awayTeam']['name']}</h1>", unsafe_allow_html=True)
    with col3: st.image(logo_a, width=100)

    # Vitórias
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div class='res-box' style='background-color:#1f77b4;'>Casa: {p_c:.1f}%</div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='res-box' style='background-color:#444;'>Empate: {p_e:.1f}%</div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='res-box' style='background-color:#dc3545;'>Fora: {p_f:.1f}%</div>", unsafe_allow_html=True)

    # Detalhes
    st.divider()
    m1, m2, m3 = st.columns(3)
    def draw(t, d):
        h = f"### {t}<div class='metric-container'>"
        for l, v in d:
            h += f"<div class='metric-row'><span>{l}</span><span style='color:{get_color(v)};font-weight:bold;'>{v:.1f}%</span></div>"
        return h + "</div>"
    
    with m1: st.markdown(draw("⚽ GOLS", [("Over 1.5", calcular_poisson(m_t, 1)), ("Over 2.5", calcular_poisson(m_t, 2))]), unsafe_allow_html=True)
    with m2: st.markdown(draw("🚩 CANTOS", [("Over 8.5", calcular_poisson(9.5, 8)), ("Over 10.5", calcular_poisson(9.5, 10))]), unsafe_allow_html=True)
    with m3: st.markdown(draw("🟨 CARTÕES", [("Over 3.5", calcular_poisson(4.2, 3)), ("Over 4.5", calcular_poisson(4.2, 4))]), unsafe_allow_html=True)
