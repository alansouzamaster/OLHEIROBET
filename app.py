import streamlit as st
import requests
import math
from datetime import datetime

# --- CONFIGURAÇÃO DA SUA CHAVE ---
# Verifique se esta chave e o Host estão corretos no seu RapidAPI
API_KEY = "a19cf6b5fcmsh62790bdb0d293ddp131982jsn24158e88f703"
HOST = "sportapi7.p.rapidapi.com"

HEADERS = {
    "X-RapidAPI-Key": API_KEY,
    "X-RapidAPI-Host": HOST
}

# --- LÓGICA MATEMÁTICA (DISTRIBUIÇÃO DE POISSON) ---
def calcular_poisson(media, alvo):
    if media <= 0: return 0
    prob_acumulada = 0
    for i in range(alvo + 1):
        prob_i = (math.exp(-media) * (media**i)) / math.factorial(i)
        prob_acumulada += prob_i
    return (1 - prob_acumulada) * 100

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="OLHEIROBET PRO", layout="wide", page_icon="⚽")

# Estilo CSS para melhorar o visual
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; }
    </style>
    """, unsafe_allow_html=True)

st.title("⚽ OlheiroBet PRO")
st.markdown("---")

# --- 1. BUSCAR JOGOS DO DIA ---
@st.cache_data(ttl=3600)
def carregar_jogos():
    try:
        url = f"https://{HOST}/api/v1/sport/football/scheduled-events/{datetime.now().strftime('%Y-%m-%d')}"
        response = requests.get(url, headers=HEADERS)
        if response.status_code == 200:
            return response.json().get('events', [])
        return []
    except:
        return []

jogos = carregar_jogos()

if jogos:
    # --- 2. FILTROS LATERAIS ---
    st.sidebar.header("⚙️ Configurações")
    todas_ligas = sorted(list(set([j['tournament']['name'] for j in jogos])))
    ligas_selecionadas = st.sidebar.multiselect("Filtrar por Liga:", todas_ligas, default=todas_ligas[:5])

    # Filtrar jogos
    jogos_filtrados = [j for j in jogos if j['tournament']['name'] in ligas_selecionadas]

    if jogos_filtrados:
        lista_nomes = {f"{j['tournament']['name']} | {j['homeTeam']['name']} x {j['awayTeam']['name']}": j for j in jogos_filtrados}
        escolha = st.selectbox("🎯 Selecione a Partida para Analisar:", list(lista_nomes.keys()))
        
        jogo_foco = lista_nomes[escolha]
        
        # --- 3. CABEÇALHO DO CONFRONTO ---
        st.write("### Análise de Confronto")
        col_t1, col_vs, col_t2 = st.columns([2, 1, 2])
        
        with col_t1:
            st.markdown(f"<h2 style='text-align: center; color: #1f77b4;'>{jogo_foco['homeTeam']['name']}</h2>", unsafe_allow_html=True)
            st.caption(f"<p style='text-align: center;'>Mandante</p>", unsafe_allow_html=True)
            
        with col_vs:
            st.markdown("<h1 style='text-align: center; color: #888;'>VS</h1>", unsafe_allow_html=True)
            
        with col_t2:
            st.markdown(f"<h2 style='text-align: center; color: #ff4b4b;'>{jogo_foco['awayTeam']['name']}</h2>", unsafe_allow_html=True)
            st.caption(f"<p style='text-align: center;'>Visitante</p>", unsafe_allow_html=True)

        # --- 4. BOTÃO DE EXECUÇÃO ---
        if st.button("🔍 EXECUTAR ANÁLISE COMPLETA"):
            with st.spinner('Processando estatísticas e calculando probabilidades...'):
                
                # Médias dinâmicas (Ajustadas para o exemplo)
                m_gols_esperada = 2.8
                m_cantos_esperada = 10.4
                
                prob_gols = calcular_poisson(m_gols_esperada, 2)
                prob_cantos = calcular_poisson(m_cantos_esperada, 9)

                st.markdown("---")
                st.subheader("📊 Resultados do Modelo Poisson")
                
                # Exibição em Colunas
                c1, c2, c3 = st.columns(3)

                with c1:
                    st.metric("Prob. Over 2.5 Gols", f"{prob_gols:.1f}%")
                    st.progress(min(prob_gols/100, 1.0))
                    if prob_gols > 65: st.success("🔥 Tendência Alta de Gols")

                with c2:
                    st.metric("Prob. Over 9.5 Cantos", f"{prob_cantos:.1f}%")
                    st.progress(min(prob_cantos/100, 1.0))
                    if prob_cantos > 75: st.success("🚩 Tendência Alta de Cantos")

                with c3:
                    # Informações Adicionais
                    juiz = jogo_foco.get('referee', {}).get('name', 'Não informado')
                    st.write("**Extra:**")
                    st.info(f"⚖️ Árbitro: {juiz}")
                    st.info(f"🏆 {jogo_foco['tournament']['name']}")

                st.write("---")
                st.caption("A
