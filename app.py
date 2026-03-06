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

def prever_1x2_avancado(h_atq, h_def, a_atq, a_def):
    lambda_casa = h_atq * a_def * 1.10 
    lambda_fora = a_atq * h_def * 0.90 
    total = lambda_casa + lambda_fora
    p_empate = 31.0 if total < 2.2 else 26.0
    sobra = 100 - p_empate
    p_casa = sobra * (lambda_casa / total) if total > 0 else sobra/2
    p_fora = sobra * (lambda_fora / total) if total > 0 else sobra/2
    return p_casa, p_empate, p_fora, (lambda_casa + lambda_fora)

@st.cache_data(ttl=600)
def carregar_jogos(d):
    try:
        url = f"https://{HOST}/api/v1/sport/football/scheduled-events/{d}"
        res = requests.get(url, headers=HEADERS, timeout=12)
        return res.json().get('events', []) if res.status_code == 200 else []
    except: return []

@st.cache_data(ttl=86400)
def buscar_stats(t_id, s_id, h_id, a_id):
    try:
        url = f"https://{HOST}/api/v1/tournament/{t_id}/season/{s_id}/standings/total"
        res = requests.get(url, headers=HEADERS, timeout=12)
        if res.status_code == 200:
            data = res.json().get('standings', [{}])[0].get('rows', [])
            h_atq = h_def = a_atq = a_def = 1.4
            for row in data:
                tid = row['team']['id']
                m = max(row.get('matches', 1), 1)
                if tid == h_id: h_atq, h_def = row['scoresFor']/m, row['scoresAgainst']/m
                if tid == a_id: a_atq, a_def = row['scoresFor']/m, row['scoresAgainst']/m
            return h_atq, h_def, a_atq, a_def
    except: pass
    return 1.4, 1.2, 1.1, 1.3

def formatar_metric(label, prob):
    """Gera o HTML para as barras com efeito Glow acima de 80%"""
    cor = "#28a745" if prob >= 75 else ("#ffc107" if prob >= 50 else "#dc3545")
    glow = f"box-shadow: 0 0 15px {cor};" if prob >= 80 else ""
    estrela = "⭐" if prob >= 85 else ""
    
    return f"""
    <div style='margin-bottom: 18px;'>
        <div style='display: flex; justify-content: space-between; margin-bottom: 5px;'>
            <span style='color: #bbb; font-size: 13px; font-weight: 500;'>{label}</span>
            <span style='color: {cor}; font-weight: bold; font-size: 15px;'>{prob:.1f}% {estrela}</span>
        </div>
        <div style='background-color: #2d333b; border-radius: 10px; height: 8px; width: 100%;'>
            <div style='background-color: {cor}; width: {prob}%; height: 100%; border-radius: 10px; {glow} transition: width 1s ease-in-out;'></div>
        </div>
    </div>
    """

# --- INTERFACE (CONFIG E CSS) ---
st.set_page_config(page_title="PROBET v5.8", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0b0e11; color: white; }
    
    .res-box { 
        text-align: center; padding: 15px; border-radius: 12px; 
        font-weight: bold; color: white; margin-bottom: 10px; font-size: 20px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
    }

    /* Cards Estilizados com Cores por Mercado */
    .card-gols {
        background: linear-gradient(145deg, #16222e, #0f171f);
        padding: 22px; border-radius: 15px; border: 1px solid #1e3a5f;
    }
    .card-cantos {
        background: linear-gradient(145deg, #162e21, #0f1f16);
        padding: 22px; border-radius: 15px; border: 1px solid #1e5f3a;
    }
    .card-cards {
        background: linear-gradient(145deg, #2e2616, #1f1a0f);
        padding: 22px; border-radius: 15px; border: 1px solid #5f4d1e;
    }

    .section-header {
        font-size: 16px; font-weight: bold; color: #ffc107;
        margin-bottom: 15px; text-align: center; text-transform: uppercase;
        letter-spacing: 1.5px;
    }
    
    h1 { color: #ffc107 !important; text-align: center; font-weight: 800; }
    </style>
    """, unsafe_allow_html=True)

st.title("⚽ PROBET ANALISE")

# --- FILTROS ---
data_sel = st.sidebar.date_input("📅 Data das Partidas", value=datetime.now())
data_str = data_sel.strftime('%Y-%m-%d')

jogos = carregar_jogos(data_str)

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
    
    # Processamento de Dados Reais
    h_atq, h_def, a_atq, a_def = buscar_stats(j['tournament']['id'], j['season']['id'], j['homeTeam']['id'], j['awayTeam']['id'])
    p_c, p_e, p_f, m_total = prever_1x2_avancado(h_atq, h_def, a_atq, a_def)

    # Cabeçalho
    st.markdown(f"<h1>{j['homeTeam']['name']} <span style='color:#444; font-size:25px;'>VS</span> {j['awayTeam']['name']}</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; color: #888;'>{j['tournament']['name']} • {ajustar_horario(j.get('startTimestamp', 0))} (Brasília)</p>", unsafe_allow_html=True)

    # Probabilidades 1X2
    st.write("### 📊 Probabilidades 1X2")
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div class='res-box' style='background: #1f77b4; border-bottom: 4px solid #155a8a;'>CASA: {p_c:.1f}%</div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='res-box' style='background: #30363d; border-bottom: 4px solid #1c2128;'>EMPATE: {p_e:.1f}%</div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='res-box' style='background: #dc3545; border-bottom: 4px solid #a71d2a;'>FORA: {p_f:.1f}%</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    # Cards de Mercados (Métricas Duplas Atualizadas)
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("<div class='section-header'>⚽ Gols</div>", unsafe_allow_html=True)
        html = formatar_metric("OVER 1.5 GOLS", calcular_poisson(m_total, 1))
        html += formatar_metric("OVER 2.5 GOLS", calcular_poisson(m_total, 2))
        st.markdown(f"<div class='card-gols'>{html}</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("<div class='section-header'>🚩 Cantos</div>", unsafe_allow_html=True)
        # Média baseada em tendência de 9.5 cantos p/ jogo
        html = formatar_metric("OVER 5.5 CANTOS", calcular_poisson(9.5, 5))
        html += formatar_metric("OVER 8.5 CANTOS", calcular_poisson(9.5, 8))
        st.markdown(f"<div class='card-cantos'>{html}</div>", unsafe_allow_html=True)

    with col3:
        st.markdown("<div class='section-header'>🟨 Cartões</div>", unsafe_allow_html=True)
        # Média baseada em tendência de 4.2 cartões p/ jogo
        html = formatar_metric("OVER 1.5 CARTÕES", calcular_poisson(4.2, 1))
        html += formatar_metric("OVER 3.5 CARTÕES", calcular_poisson(4.2, 3))
        st.markdown(f"<div class='card-cards'>{html}</div>", unsafe_allow_html=True)

    if st.button("🗑️ LIMPAR ANÁLISE"):
        st.session_state.analise_pronta = False
        st.rerun()

elif not jogos:
    st.info("Aguardando seleção de liga ou nenhum jogo disponível.")
