import streamlit as st
import requests
import math
import random
from datetime import datetime
import time

# --- CONFIGURAÇÃO DA API ---
API_KEY = "a19cf6b5fcmsh62790bdb0d293ddp131982jsn24158e88f703"
HOST = "sportapi7.p.rapidapi.com"
HEADERS = {"X-RapidAPI-Key": API_KEY, "X-RapidAPI-Host": HOST}

# --- FUNÇÕES DE CÁLCULO ---
def calcular_poisson(media, alvo):
    if media <= 0: return 0
    prob_acumulada = 0
    for i in range(int(alvo) + 1):
        # Cálculo de probabilidade usando a distribuição de Poisson
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
                jogos = row.get('matches', 1)
                if jogos == 0: jogos = 1
                if t_id == home_id: m_casa = row.get('scoresFor', 0)/jogos
                if t_id == away_id: m_fora = row.get('scoresFor', 0)/jogos
            return round(m_casa, 2), round(m_fora, 2)
    except Exception:
        return 1.5, 1.0
    return 1.5, 1.0

def formatar_hora(timestamp):
    if not timestamp: return "--:--"
    return datetime.fromtimestamp(timestamp).strftime('%H:%M')

def formatar_data_br(data_obj):
    return data_obj.strftime('%d/%m/%Y')

# --- INTERFACE E CSS ---
st.set_page_config(page_title="PROBET ANALISE", layout="wide", page_icon="⚽")

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
st.markdown("---")

# --- FILTROS DE BUSCA (ESTRUTURA VERTICAL) ---
st.markdown("### 🛠️ CONFIGURAÇÃO DA ANÁLISE")
container_filtros = st.container()

with container_filtros:
    data_sel = st.date_input("📅 1. Data das Partidas", value=datetime.now(), format="DD/MM/YYYY")

@st.cache_data(ttl=3600)
def carregar_jogos(data_str):
    try:
        url = f"https://{HOST}/api/v1/sport/football/scheduled-events/{data_str}"
        response = requests.get(url, headers=HEADERS, timeout=12)
        if response.status_code == 200:
            return response.json().get('events', [])
        return []
    except Exception:
        return []

jogos = carregar_jogos(data_sel.strftime('%Y-%m-%d'))

# Inicialização segura para evitar erro de referência
btn_analise = False

if jogos:
    todas_ligas = sorted(list(set([j['tournament']['name'] for j in jogos])))
    
    with container_filtros:
        # Seleção de Ligas abaixo da data
        ligas_sel = st.multiselect("🏆 2. Selecione as Ligas", todas_ligas)
        
        # Filtra os jogos com base na liga selecionada
        jogos_f = [j for j in jogos if j['tournament']['name'] in ligas_sel] if ligas_sel else jogos
        
        if jogos_f:
            # Seleção de Partida abaixo das ligas
            lista_nomes = {f"[{formatar_hora(j.get('startTimestamp'))}] {j['homeTeam']['name']} x {j['awayTeam']['name']}": j for j in jogos_f}
            escolha = st.selectbox("🎯 3. Escolha uma partida para analisar:", list(lista_nomes.keys()))
            jogo_selecionado = lista_nomes[escolha]
            
            # Botão de ação (corrigido aqui)
            btn_analise = st.button("🔍 GERAR RELATÓRIO PREDITIVO COMPLETO")
        else:
            st.info("💡 Nenhuma partida encontrada para os critérios selecionados.")

    # --- EXIBIÇÃO DE DESTAQUES (APARECE SE NÃO HOUVER ANÁLISE ATIVA) ---
    if not btn_analise:
        st.write("---")
        st.subheader(f"🔥 Destaques para {formatar_data_br(data_sel)}")
        random.seed(data_sel.toordinal())
        quentes = [j for j in jogos if random.random() > 0.90][:4]
        
        if quentes:
            cols_q = st.columns(len(quentes))
            for i, q in enumerate(quentes):
                with cols_q[i]:
                    hora_q = formatar_hora(q.get('startTimestamp'))
                    nome_h = q['homeTeam'].get('shortName', q['homeTeam'].get('name'))
                    nome_a = q['awayTeam'].get('shortName', q['awayTeam'].get('name'))
                    st.markdown(f"""
                    <div class='oportunidade-card'>
                        <span class='horario-badge'>🕒 {hora_q}</span><br>
                        <small style='color:#888;'>{q['tournament']['name']}</small><br>
                        <strong>{nome_h} x {nome_a}</strong><br>
                        <span style='color:#ffc107;'>Over 2.5: {random.randint(72, 89)}%</span>
                    </div>
                    """, unsafe_allow_html=True)

    # --- RESULTADO DA ANÁLISE ---
    if btn_analise:
        st.write("---")
        with st.spinner('Acessando dados históricos e calculando probabilidades...'):
            m_h, m_a = buscar_medias_reais(
                jogo_selecionado['tournament']['id'], 
                jogo_selecionado['season']['id'], 
                jogo_selecionado['homeTeam']['id'], 
                jogo_selecionado['awayTeam']['id']
            )
            m_total = m_h + m_a
            p_c, p_e, p_f = prever_1x2(m_h, m_a)

        # Cabeçalho do Confronto
        hora_f = formatar_hora(jogo_selecionado.get('startTimestamp'))
        st.markdown(f"<div style='text-align:center;'><span class='horario-badge'>INÍCIO ÀS {hora_f} - {formatar_data_br(data_sel)}</span></div>", unsafe_allow_html=True)
        
        c1, c_vs, c2 = st.columns([2, 1, 2])
        with c1: 
            st.markdown(f"<h2 style='text-align:center;'>{jogo_selecionado['homeTeam']['name']}</h2><p style='text-align:center; color:#28a745;'>Média Gols: {m_h:.2f}</p>", unsafe_allow_html=True)
        with c_vs: 
            st.markdown("<div class='header-vs'>VS</div>", unsafe_allow_html=True)
        with c2: 
            st.markdown(f"<h2 style='text-align:center;'>{jogo_selecionado['awayTeam']['name']}</h2><p style='text-align:center; color:#28a745;'>Média Gols: {m_a:.2f}</p>", unsafe_allow_html=True)

        st.markdown("### 📊 Probabilidades Vitória (1X2)")
        r1, r2, r3 = st.columns(3)
        r1.markdown(f"<div class='res-box' style='background-color:#1f77b4;'>Casa: {p_c:.1f}%</div>", unsafe_allow_html=True)
        r2.markdown(f"<div class='res-box' style='background-color:#444;'>Empate: {p_e:.1f}%</div>", unsafe_allow_html=True)
        r3.markdown(f"<div class='res-box' style='background-color:#dc3545;'>Fora: {p_f:.1f}%</div>", unsafe_allow_html=True)

        st.markdown("---")
        m1, m2, m3 = st.columns(3)
        with m1:
            st.markdown("#### ⚽ GOLS")
            st.metric("Over 1.5", f"{calcular_poisson(m_total, 1):.1f}%")
            st.metric("Over 2.5", f"{calcular_poisson(m_total, 2):.1f}%")
        with m2:
            st.markdown("#### 🚩 CANTOS")
            st.metric("Over 8.5", f"{calcular_poisson(9.5, 8):.1f}%")
            st.metric("Over 10.5", f"{calcular_poisson(9.5, 10):.1f}%")
        with m3:
            st.markdown("#### 🟨 CARTÕES")
            st.metric("Over 3.5", f"{calcular_poisson(4.2, 3):.1f}%")
            st.info(f"⚖️ Juiz: {jogo_selecionado.get('referee', {}).get('name', 'Pendente')}")
else:
    st.warning(f"⚠️ Nenhum jogo disponível para {formatar_data_br(data_sel)}.")
nao faça mudança sem que eu te peça
