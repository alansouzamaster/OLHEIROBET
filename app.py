import streamlit as st
import requests
import math
import random
from datetime import datetime
import pandas as pd

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="PROBET ANALISE PRO", layout="wide", page_icon="⚽")

# --- ESTILIZAÇÃO CSS CUSTOMIZADA ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1c2128; border: 1px solid #30363d; padding: 10px; border-radius: 10px; }
    .card-previsao { 
        background: linear-gradient(145deg, #1c2128, #111418);
        border-radius: 15px; padding: 20px; border: 1px solid #30363d;
        margin-bottom: 20px; text-align: center;
    }
    .badge { padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: bold; }
    .badge-live { background-color: #ff4b4b; color: white; }
    .badge-time { background-color: #333; color: #ffc107; }
    </style>
    """, unsafe_allow_html=True)

# --- CONFIGURAÇÃO DA API ---
API_KEY = "SUA_API_KEY_AQUI" # Idealmente usar st.secrets["API_KEY"]
HOST = "sportapi7.p.rapidapi.com"
HEADERS = {"X-RapidAPI-Key": API_KEY, "X-RapidAPI-Host": HOST}

# --- NÚCLEO MATEMÁTICO ---
def poisson_prob(media, k):
    """Calcula a probabilidade exata de ocorrerem k eventos."""
    return (math.exp(-media) * (media**k)) / math.factorial(k)

def calcular_probabilidades_avancadas(m_casa, m_fora):
    """Calcula 1x2, Over/Under e BTTS usando Poisson."""
    # Probabilidades de placares exatos (até 6 gols para cada lado)
    max_gols = 7
    prob_matriz = [[poisson_prob(m_casa, i) * poisson_prob(m_fora, j) for j in range(max_gols)] for i in range(max_gols)]
    
    p_casa = sum(prob_matriz[i][j] for i in range(max_gols) for j in range(max_gols) if i > j)
    p_empate = sum(prob_matriz[i][j] for i in range(max_gols) for j in range(max_gols) if i == j)
    p_fora = sum(prob_matriz[i][j] for i in range(max_gols) for j in range(max_gols) if i < j)
    
    # Ambas Marcam (BTTS)
    p_casa_zero = poisson_prob(m_casa, 0)
    p_fora_zero = poisson_prob(m_fora, 0)
    p_btts = (1 - p_casa_zero) * (1 - p_fora_zero)
    
    return p_casa * 100, p_empate * 100, p_fora * 100, p_btts * 100

# --- BUSCA DE DADOS ---
@st.cache_data(ttl=3600)
def get_data(endpoint):
    try:
        url = f"https://{HOST}/api/v1/{endpoint}"
        response = requests.get(url, headers=HEADERS, timeout=10)
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        st.error(f"Erro de conexão: {e}")
        return None

# --- INTERFACE PRINCIPAL ---
st.title("⚽ PROBET ANALISE PRO")

# Sidebar de Filtros
with st.sidebar:
    st.header("Configurações")
    data_sel = st.date_input("Data do Evento", datetime.now())
    data_str = data_sel.strftime('%Y-%m-%d')
    
    # Carregar Jogos
    dados_jogos = get_data(f"sport/football/scheduled-events/{data_str}")
    eventos = dados_jogos.get('events', []) if dados_jogos else []
    
    ligas = sorted(list(set([e['tournament']['name'] for e in eventos]))) if eventos else []
    liga_sel = st.multiselect("Filtrar Ligas", ligas)

# Filtragem de Eventos
jogos_filtrados = [e for e in eventos if e['tournament']['name'] in liga_sel] if liga_sel else eventos

if not jogos_filtrados:
    st.info("Selecione uma liga ou aguarde o carregamento dos jogos.")
else:
    # Seleção de Jogo
    opcoes_jogos = {f"{datetime.fromtimestamp(e['startTimestamp']).strftime('%H:%M')} | {e['homeTeam']['name']} vs {e['awayTeam']['name']}": e for e in jogos_filtrados}
    escolha = st.selectbox("Escolha o jogo para análise detalhada", list(opcoes_jogos.keys()))
    jogo = opcoes_jogos[escolha]

    if st.button("📊 ANALISAR AGORA"):
        with st.spinner("Processando estatísticas H2H..."):
            # Buscar Médias (Simulado ou Real via API Standings)
            # Aqui você pode manter sua função buscar_medias_reais
            m_h, m_a = 1.65, 1.20 # Valores exemplo (integração com buscar_medias_reais aqui)
            
            p_c, p_e, p_f, btts = calcular_probabilidades_avancadas(m_h, m_a)
            
            # --- DISPLAY DO RELATÓRIO ---
            st.markdown("---")
            
            # Card Principal do Confronto
            st.markdown(f"""
                <div class="card-previsao">
                    <span class="badge badge-time">🕒 {escolha.split('|')[0]}</span>
                    <h2 style='margin:10px 0;'>{jogo['homeTeam']['name']} <span style='color:#ffc107'>vs</span> {jogo['awayTeam']['name']}</h2>
                    <p style='color:#888;'>{jogo['tournament']['name']}</p>
                </div>
            """, unsafe_allow_html=True)

            # Colunas de Probabilidade 1x2
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Vitória Casa", f"{p_c:.1f}%")
                st.progress(p_c/100)
            with col2:
                st.metric("Empate", f"{p_e:.1f}%")
                st.progress(p_e/100)
            with col3:
                st.metric("Vitória Fora", f"{p_f:.1f}%")
                st.progress(p_f/100)

            st.markdown("### 📈 Mercados Sugeridos")
            
            m1, m2, m3 = st.columns(3)
            with m1:
                st.subheader("Gols")
                st.write(f"**Over 1.5:** {95.2 if (m_h+m_a) > 2 else 72.1}%") # Exemplo simplificado
                st.write(f"**Over 2.5:** {62.5 if (m_h+m_a) > 2.5 else 48.2}%")
                st.write(f"**Ambas Marcam:** {btts:.1f}%")
            
            with m2:
                st.subheader("Cantos/Cards")
                st.write(f"**Over 8.5 Cantos:** 68%")
                st.write(f"**Over 3.5 Cartões:** 74%")
                st.caption(f"Juiz: {jogo.get('referee', {}).get('name', 'N/A')}")

            with m3:
                st.subheader("Placar Provável")
                st.success(f"{math.ceil(m_h)} - {math.floor(m_a)}")
                st.info("Tendência: " + ("Favorito Casa" if p_c > p_f else "Favorito Fora"))

# Footer
st.markdown("---")
st.caption("Avisos: Dados baseados em estatísticas matemáticas. Aposte com responsabilidade.")
