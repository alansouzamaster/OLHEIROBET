import streamlit as st
import requests
import math
import random
from datetime import datetime, timezone, timedelta

# --- CONFIGURAÇÃO DA API ---
API_KEY = "a19cf6b5fcmsh62790bdb0d293ddp131982jsn24158e88f703"
HOST = "sportapi7.p.rapidapi.com"
HEADERS = {"X-RapidAPI-Key": API_KEY, "X-RapidAPI-Host": HOST}

# --- FUNÇÕES DE CÁLCULO ---
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

@st.cache_data(ttl=3600)
def buscar_medias_reais(tournament_id, season_id, home_id, away_id):
    try:
        url = f"https://{HOST}/api/v1/tournament/{tournament_id}/season/{season_id}/standings/total"
        response = requests.get(url, headers=HEADERS, timeout=15)
        if response.status_code == 200:
            data = response.json()
            standings = data.get('standings', [])
            if not standings: return 1.5, 1.2
            
            rows = standings[0].get('rows', [])
            m_casa, m_fora = 1.5, 1.2 # Valores padrão caso não encontre o time
            for row in rows:
                t_id = row['team']['id']
                jogos = row.get('matches', 1)
                if jogos == 0: jogos = 1
                gols = row.get('scoresFor', 0)
                if t_id == home_id: m_casa = gols/jogos
                if t_id == away_id: m_fora = gols/jogos
            return round(m_casa, 2), round(m_fora, 2)
    except:
        return 1.6, 1.3
    return 1.6, 1.3

def formatar_hora(timestamp):
    if not timestamp: return "--:--"
    # Ajuste para fuso horário de Brasília (GMT-3)
    dt = datetime.fromtimestamp(timestamp, tz=timezone.utc).astimezone(timezone(timedelta(hours=-3)))
    return dt.strftime('%H:%M')

# --- INTERFACE ---
st.set_page_config(page_title="PROBET ANALISE", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #e0e0e0; }
    .stMetric { background-color: #1c2128; padding: 15px; border-radius: 10px; border: 1px solid #333; }
    .res-box { text-align: center; padding: 12px; border-radius: 8px; font-weight: bold; color: white; margin-bottom: 10px; }
    .horario-badge { background-color: #333; color: #ffc107; padding: 3px 10px; border-radius: 5px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title(" ⚽ PROBET ANALISE ")

# --- FILTROS ---
data_sel = st.date_input("📅 Selecione a Data", value=datetime.now())

@st.cache_data(ttl=600)
def carregar_jogos(data_str):
    url = f"https://{HOST}/api/v1/sport/football/scheduled-events/{data_str}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        if response.status_code == 200:
            return response.json().get('events', [])
        else:
            st.error(f"Erro na API: Status {response.status_code}")
            return []
    except:
        st.error("Falha na conexão com o servidor de dados.")
        return []

eventos = carregar_jogos(data_sel.strftime('%Y-%m-%d'))

# Filtrar jogos para garantir que são do dia selecionado (considerando margem de fuso)
jogos_dia = []
for ev in eventos:
    # Removemos a trava rígida de timestamp para evitar que jogos sumam por causa de 1 ou 2 horas de diferença
    jogos_dia.append(ev)

if jogos_dia:
    todas_ligas = sorted(list(set([j['tournament']['name'] for j in jogos_dia])))
    ligas_sel = st.multiselect("🏆 Selecione as Ligas", todas_ligas)
    
    jogos_f = [j for j in jogos_dia if j['tournament']['name'] in ligas_sel] if ligas_sel else jogos_dia
    
    if jogos_f:
        # Criar dicionário para o Selectbox
        opcoes = {f"[{formatar_hora(j.get('startTimestamp'))}] {j['homeTeam']['name']} x {j['awayTeam']['name']}": j for j in jogos_f}
        escolha = st.selectbox("🎯 Escolha a Partida", list(opcoes.keys()))
        jogo = opcoes[escolha]
        
        # O BOTÃO DEVE EXECUTAR TUDO ABAIXO DELE
        if st.button("🔍 GERAR RELATÓRIO COMPLETO"):
            with st.spinner('Calculando probabilidades...'):
                # Pegar IDs necessários
                t_id = jogo['tournament']['id']
                s_id = jogo['season']['id']
                h_id = jogo['homeTeam']['id']
                a_id = jogo['awayTeam']['id']
                
                # Buscar Médias
                m_h, m_a = buscar_medias_reais(t_id, s_id, h_id, a_id)
                m_total = m_h + m_a
                p_casa, p_empate, p_fora = prever_1x2(m_h, m_a)
                
                # EXIBIÇÃO DO RELATÓRIO
                st.markdown("---")
                st.markdown(f"### 📊 Relatório: {jogo['homeTeam']['name']} vs {jogo['awayTeam']['name']}")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown(f"<div class='res-box' style='background-color:#1f77b4;'>Casa: {p_casa:.1f}%</div>", unsafe_allow_html=True)
                with col2:
                    st.markdown(f"<div class='res-box' style='background-color:#444;'>Empate: {p_empate:.1f}%</div>", unsafe_allow_html=True)
                with col3:
                    st.markdown(f"<div class='res-box' style='background-color:#dc3545;'>Fora: {p_fora:.1f}%</div>", unsafe_allow_html=True)
                
                st.write("#### 📈 Projeções de Mercado")
                m1, m2, m3 = st.columns(3)
                m1.metric("Over 1.5 Gols", f"{calcular_poisson(m_total, 1):.1f}%")
                m1.metric("Over 2.5 Gols", f"{calcular_poisson(m_total, 2):.1f}%")
                
                m2.metric("Over 8.5 Cantos", f"{calcular_poisson(9.5, 8):.1f}%")
                m2.metric("Over 10.5 Cantos", f"{calcular_poisson(9.5, 10):.1f}%")
                
                m3.metric("Over 3.5 Cartões", f"{calcular_poisson(4.2, 3):.1f}%")
                st.info(f"Ref: {jogo.get('referee', {}).get('name', 'Não informado')}")
    else:
        st.warning("Nenhum jogo encontrado para os filtros selecionados.")
else:
    st.info("Aguardando carregamento de jogos...")
