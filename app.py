# --- FILTROS COM DIAGNÓSTICO ---
st.sidebar.header("⚙️ CONFIGURAÇÕES")
data_sel = st.sidebar.date_input("📅 Data das Partidas", value=datetime.now())
data_str = data_sel.strftime('%Y-%m-%d')

@st.cache_data(ttl=300)
def carregar_jogos_debug(d):
    try:
        url = f"https://{HOST}/api/v1/sport/football/scheduled-events/{d}"
        res = requests.get(url, headers=HEADERS, timeout=12)
        
        # LOG DE ERRO PARA O USUÁRIO
        if res.status_code == 403:
            st.error("🚫 Erro 403: Sua chave da API foi negada ou o limite expirou.")
            return []
        elif res.status_code == 429:
            st.error("⏳ Erro 429: Você atingiu o limite de requisições por minuto.")
            return []
        elif res.status_code != 200:
            st.error(f"⚠️ Erro inesperado: Código {res.status_code}")
            return []
            
        dados = res.json().get('events', [])
        return dados
    except Exception as e:
        st.error(f"❌ Erro de Conexão: {e}")
        return []

jogos = carregar_jogos_debug(data_str)

if jogos:
    # Se encontrou jogos, monta os menus
    todas_ligas = sorted(list(set([j['tournament']['name'] for j in jogos])))
    ligas_sel = st.multiselect("🏆 Selecione as Ligas", todas_ligas)
    
    jogos_f = [j for j in jogos if j['tournament']['name'] in ligas_sel] if ligas_sel else jogos
    
    if jogos_f:
        lista_nomes = {f"[{ajustar_horario(j.get('startTimestamp', 0))}] {j['homeTeam']['name']} x {j['awayTeam']['name']}": j for j in jogos_f}
        escolha = st.selectbox("🎯 Escolha uma partida:", list(lista_nomes.keys()))
        
        if st.button("🔍 GERAR RELATÓRIO PREDITIVO"):
            st.session_state.jogo_selecionado = lista_nomes[escolha]
            st.session_state.analise_pronta = True
    else:
        st.info("👆 Selecione pelo menos uma liga acima para ver os jogos.")
else:
    # Se a lista veio vazia mas não deu erro de conexão
    st.warning(f"Nenhum jogo agendado encontrado na API para {data_str}. Tente mudar a data para amanhã.")

