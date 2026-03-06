import streamlit as st
import requests
import math
from datetime import datetime

# --- CONFIGURAÇÃO DA API ---
API_KEY = "a19cf6b5fcmsh62790bdb0d293ddp131982jsn24158e88f703"
HOST = "sportapi7.p.rapidapi.com"
HEADERS = {"X-RapidAPI-Key": API_KEY, "X-RapidAPI-Host": HOST}

# --- FUNÇÕES DE BUSCA ---

@st.cache_data(ttl=600) # Cache curto (10 min) para escalações
def buscar_escalacao_real(event_id):
    """Busca a escalação oficial da partida selecionada."""
    try:
        url = f"https://{HOST}/api/v1/event/{event_id}/lineups"
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            data = response.json()
            # Retorna jogadores titulares do mandante e visitante
            home_players = data.get('home', {}).get('players', [])
            away_players = data.get('away', {}).get('players', [])
            return home_players, away_players
    except:
        return [], []
    return [], []

@st.cache_data(ttl=86400)
def buscar_estatisticas_jogador(player_id, tournament_id, season_id):
    """Busca cartões amarelos do jogador na temporada atual."""
    try:
        # Endpoint de estatísticas sazonais do jogador
        url = f"https://{HOST}/api/v1/player/{player_id}/unique-tournament/{tournament_id}/season/{season_id}/statistics/overall"
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            stats = response.json().get('statistics', {})
            yellow_cards = stats.get('yellowCards', 0)
            matches_played = stats.get('appearances', 1) or 1
            # Cálculo de probabilidade baseada na média da temporada
            prob = (yellow_cards / matches_played) * 100
            return yellow_cards, matches_played, round(min(prob, 99), 1)
    except:
        return 0, 0, 0
    return 0, 0, 0

# --- INTERFACE ---

# ... (Manter o restante do seu código de filtros e cálculo de Poisson) ...

if btn_analise:
    st.write("---")
    # ... (Seu código existente de médias e 1X2) ...

    st.markdown("### 🟨 RADAR DE CARTÕES: JOGADORES ATUAIS")
    
    h_players, a_players = buscar_escalacao_real(jogo_selecionado['id'])
    
    if not h_players:
        st.warning("⏳ Escalação oficial ainda não disponível. Tente novamente 1h antes do início.")
    else:
        st.info("Probabilidade calculada com base nos cartões recebidos/jogos na temporada atual.")
        
        # Mostrar os 3 jogadores mais propensos de cada time
        c1, c2 = st.columns(2)
        
        with c1:
            st.markdown(f"**{jogo_selecionado['homeTeam']['name']}**")
            for p in h_players[:5]: # Analisa os 5 primeiros da lista
                p_obj = p.get('player', {})
                cards, games, prob = buscar_estatisticas_jogador(
                    p_obj.get('id'), 
                    jogo_selecionado['tournament']['id'], 
                    jogo_selecionado['season']['id']
                )
                if prob > 0:
                    st.markdown(f"""
                    <div style='background:#161b22; padding:10px; border-radius:5px; margin-bottom:5px; border-left:4px solid #ffc107;'>
                        <b>{p_obj.get('name')}</b><br>
                        <small>Temporada: {cards} 🟨 em {games} jogos</small><br>
                        <span style='color:#ffc107; font-weight:bold;'>Probabilidade: {prob}%</span>
                    </div>
                    """, unsafe_allow_html=True)

        with c2:
            st.markdown(f"**{jogo_selecionado['awayTeam']['name']}**")
            for p in a_players[:5]:
                p_obj = p.get('player', {})
                cards, games, prob = buscar_estatisticas_jogador(
                    p_obj.get('id'), 
                    jogo_selecionado['tournament']['id'], 
                    jogo_selecionado['season']['id']
                )
                if prob > 0:
                    st.markdown(f"""
                    <div style='background:#161b22; padding:10px; border-radius:5px; margin-bottom:5px; border-left:4px solid #ffc107;'>
                        <b>{p_obj.get('name')}</b><br>
                        <small>Temporada: {cards} 🟨 em {games} jogos</small><br>
                        <span style='color:#ffc107; font-weight:bold;'>Probabilidade: {prob}%</span>
                    </div>
                    """, unsafe_allow_html=True)
