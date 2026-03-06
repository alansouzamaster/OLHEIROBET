import streamlit as st
import requests
import math
import random
from datetime import datetime, timedelta
import time

# --- CONFIGURAÇÃO DA API ---
# Nota: Verifique se sua chave API ainda tem créditos para chamadas diárias
API_KEY = "3a5c2b926bmsh18b3c4624ec302bp1911efjsn84e2922978ff"
HOST = "sportapi7.p.rapidapi.com"
HEADERS = {"X-RapidAPI-Key": API_KEY, "X-RapidAPI-Host": HOST}

# --- FUNÇÕES DE CÁLCULO (Mantidas) ---
def calcular_poisson(media, alvo):
    if media <= 0: return 0
    prob_acumulada = 0
    for i in range(int(alvo) + 1):
        prob_i = (math.exp(-media) * (media**i)) / math.factorial(i)
        prob_acumulada += prob_i
    return (1 - prob_acumulada) * 100

def prever_1x2(m_casa, m_fora):
    total = m_casa + m_fora
    p_empate = 26.0
    sobra = 100 - p_empate
    if total > 0:
        p_casa = sobra * (m_casa / total)
        p_fora = sobra * (m_fora / total)
    else:
        p_casa = p_fora = sobra / 2
    return p_casa, p_empate, p_fora

@st.cache_data(ttl=3600) # Reduzi o cache para 1 hora para evitar dados antigos
def carregar_jogos(data_str):
    try:
        # Forçamos a URL a usar a data selecionada
        url = f"https://{HOST}/api/v1/sport/football/scheduled-events/{data_str}"
        response = requests.get(url, headers=HEADERS, timeout=15)
        if response.status_code == 200:
            events = response.json().get('events', [])
            return events
        elif response.status_code == 429:
            st.error("🛑 Limite de requisições da API atingido.")
            return []
        return []
    except Exception as e:
        st.error(f"Erro na conexão: {e}")
        return []

@st.cache_data(ttl=86400)
def buscar_medias_reais(tournament_id, season_id, home_id, away_id):
    try:
        url = f"https://{HOST}/api/v1/tournament/{tournament_id}/season/{season_id}/standings/total"
        response = requests.get(url, headers=HEADERS, timeout=12)
        if response.status_code == 200:
            data = response.json()
            standings_list = data.get('standings', [])
            if not standings_list: return 1.5, 1.0
            rows = standings_list[0].get('rows', [])
            m_casa, m_fora = 1.4, 1.1
            for row in rows:
                t_id = row['team']['id']
                jogos = row.get('matches', 1) or 1
                if t_id == home_id: m_casa = row.get('scoresFor', 0)/jogos
                if t_id == away_id: m_fora = row.get('scoresFor', 0)/jogos
            return round(m_casa, 2), round(m_fora, 2)
    except:
        return 1.5, 1.0
    return 1.5, 1.0

def formatar_hora(timestamp):
    if not timestamp: return "--:--"
    return datetime.fromtimestamp(timestamp).strftime('%H:%M')

def formatar_data_br(data_obj):
    return data_obj.strftime('%d/%m/%Y')

# --- INTERFACE ---
st.set_page_config(page_title="PROBET ANALISE", layout="wide", page_icon="⚽")

# CSS (Mantido seu estilo original)
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #e0e0e0; }
    div[data-testid="stMetricValue"] { color: #ffc107 !important; font-size: 24px !important; }
    .stMetric { background-color: #1c2128; padding: 15px; border-radius: 12px; border: 1px solid #30363d; }
    .oportunidade-card { background-color: #1c2128; padding: 15px; border-top: 3px solid #ffc107; border-radius: 8px; margin-bottom: 10px; min-height: 160px; }
    .stButton>button { width: 100%; background-color: #ffc107 !important; color: black !important; font-weight: bold; border-radius: 8px; }
    .res-box { text-align: center; padding: 12px; border-radius: 8px; font-weight: bold; color: white; margin-bottom: 10px; font-size: 18px; }
    .horario-badge { background-color: #333; color: #ffc107; padding: 3px 10px; border-radius: 5px; font-weight: bold; }
    .header-vs { text-align: center; color: #ffc107; font-size: 40px; font-weight: bold; margin-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title(" ⚽ PROBET ANALISE ")

# Filtros
container_filtros = st.container()
with container_filtros:
    # Adicionado um botão para limpar cache manualmente se necessário
    col_data, col_refresh = st.columns([3, 1])
    with col_data:
        data_sel = st.date_input("📅 1. Data das Partidas", value=datetime.now(), format="DD/MM/YYYY")
    with col_refresh:
        if st.button("🔄 Atualizar Dados"):
            st.cache_data.clear()
            st.rerun()

# Chamada da função com a data formatada
jogos = carregar_jogos(data_sel.strftime('%Y-%m-%d'))

btn_analise = False

if jogos:
    todas_ligas = sorted(list(set([j['tournament']['name'] for j in jogos])))
    with container_filtros:
        ligas_sel = st.multiselect("🏆 2. Selecione as Ligas", todas_ligas)
        jogos_f = [j for j in jogos if j['tournament']['name'] in ligas_sel] if ligas_sel else jogos
        
        if jogos_f:
            lista_nomes = {f"[{formatar_hora(j.get('startTimestamp'))}] {j['homeTeam']['name']} x {j['awayTeam']['name']}": j for j in jogos_f}
            escolha = st.selectbox("🎯 3. Escolha uma partida:", list(lista_nomes.keys()))
            jogo_selecionado = lista_nomes[escolha]
            btn_analise = st.button("🔍 GERAR RELATÓRIO PREDITIVO COMPLETO")
        else:
            st.info("💡 Selecione uma liga para listar as partidas.")

    if not btn_analise:
        st.write("---")
        st.subheader(f"🔥 Destaques para {formatar_data_br(data_sel)}")
        # Logica de destaques mantida...
        random.seed(data_sel.toordinal())
        quentes = [j for j in jogos if random.random() > 0.90][:4]
        if quentes:
            cols_q = st.columns(len(quentes))
            for i, q in enumerate(quentes):
                with cols_q[i]:
                    st.markdown(f"<div class='oportunidade-card'>🕒 {formatar_hora(q.get('startTimestamp'))}<br><strong>{q['homeTeam']['name']} x {q['awayTeam']['name']}</strong><br><span style='color:#ffc107;'>Análise Disponível</span></div>", unsafe_allow_html=True)

    if btn_analise:
        # (O resto do seu código de análise de 1X2, Gols e Cantos permanece igual)
        st.success(f"Analisando: {jogo_selecionado['homeTeam']['name']} x {jogo_selecionado['awayTeam']['name']}")
        # ... inserir aqui o bloco de 'RESULTADO DA ANÁLISE' que você já possui ...
else:
    st.warning(f"⚠️ Nenhum jogo encontrado na API para o dia {formatar_data_br(data_sel)}. Tente outra data ou clique em Atualizar.")
