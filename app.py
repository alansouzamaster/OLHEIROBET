import streamlit as st
import requests
import math
from datetime import datetime

# --- CONFIGURAÇÃO DA API ---
API_KEY = "a19cf6b5fcmsh62790bdb0d293ddp131982jsn24158e88f703"
HOST = "sportapi7.p.rapidapi.com"
HEADERS = {"X-RapidAPI-Key": API_KEY, "X-RapidAPI-Host": HOST}

@st.cache_data(ttl=86400)
def buscar_elenco_e_cartoes(team_id, tournament_id, season_id):
    """Busca TODOS os jogadores do elenco e suas estatísticas de cartões."""
    try:
        # Busca a lista de jogadores do time na temporada
        url_team = f"https://{HOST}/api/v1/team/{team_id}/unique-tournament/{tournament_id}/season/{season_id}/statistics/overall"
        # Nota: Algumas APIs exigem buscar os jogadores individualmente ou via endpoint de 'players'
        # Usaremos a lógica de busca por elenco (Squad)
        url_squad = f"https://{HOST}/api/v1/team/{team_id}/players"
        res = requests.get(url_squad, headers=HEADERS, timeout=10)
        
        if res.status_code != 200: return []
        
        players_data = res.json().get('players', [])
        lista_completa = []

        # Para cada jogador do elenco, buscamos a métrica de cartões
        for p in players_data:
            p_obj = p.get('player', {})
            p_id = p_obj.get('id')
            
            # Busca estatística individual
            url_stats = f"https://{HOST}/api/v1/player/{p_id}/unique-tournament/{tournament_id}/season/{season_id}/statistics/overall"
            res_s = requests.get(url_stats, headers=HEADERS, timeout=10)
            
            if res_s.status_code == 200:
                s = res_s.json().get('statistics', {})
                amarelos = s.get('yellowCards', 0)
                partidas = s.get('appearances', 1) or 1
                if amarelos > 0: # Filtramos apenas quem já tomou cartão para dar relevância
                    prob = (amarelos / partidas) * 100
                    lista_completa.append({
                        "nome": p_obj.get('name'),
                        "posicao": p_obj.get('position', 'N/A'),
                        "amarelos": amarelos,
                        "jogos": partidas,
                        "prob": round(min(prob, 99), 1)
                    })
        
        # Ordena pelos jogadores mais "faltosos"
        return sorted(lista_completa, key=lambda x: x['prob'], reverse=True)
    except:
        return []

# --- NA PARTE DO RESULTADO DA ANÁLISE (DENTRO DO if btn_analise) ---

if btn_analise and jogo_selecionado:
    # ... (Seu código anterior de médias e 1X2) ...

    st.markdown("### 📋 ANÁLISE COMPLETA DO ELENCO (CARTÕES)")
    
    tab_casa, tab_fora = st.tabs([jogo_selecionado['homeTeam']['name'], jogo_selecionado['awayTeam']['name']])
    
    with tab_casa:
        st.write("🔎 Jogadores do elenco com maior tendência a cartão:")
        elenco_h = buscar_elenco_e_cartoes(
            jogo_selecionado['homeTeam']['id'], 
            jogo_selecionado['tournament']['id'], 
            jogo_selecionado['season']['id']
        )
        if elenco_h:
            for p in elenco_h:
                with st.expander(f"🟨 {p['prob']}% - {p['nome']} ({p['posicao']})"):
                    st.write(f"O jogador recebeu **{p['amarelos']} cartões amarelos** em **{p['jogos']} jogos** nesta competição.")
                    st.progress(p['prob'] / 100)
        else:
            st.info("Sem dados de cartões para este elenco no momento.")

    with tab_fora:
        st.write("🔎 Jogadores do elenco com maior tendência a cartão:")
        elenco_a = buscar_elenco_e_cartoes(
            jogo_selecionado['awayTeam']['id'], 
            jogo_selecionado['tournament']['id'], 
            jogo_selecionado['season']['id']
        )
        if elenco_a:
            for p in elenco_a:
                with st.expander(f"🟨 {p['prob']}% - {p['nome']} ({p['posicao']})"):
                    st.write(f"O jogador recebeu **{p['amarelos']} cartões amarelos** em **{p['jogos']} jogos** nesta competição.")
                    st.progress(p['prob'] / 100)
        else:
            st.info("Sem dados de cartões para este elenco no momento.")

    # ... (Restante do seu código de Gols e Cantos) ...
