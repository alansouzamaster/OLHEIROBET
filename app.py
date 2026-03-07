import streamlit as st
import requests
import math
from datetime import datetime, timedelta

# --- CONFIGURAÇÃO DA API ---
API_KEY = "3a5c2b926bmsh18b3c4624ec302bp1911efjsn84e2922978ff"

HOST = "sportapi7.p.rapidapi.com"
HEADERS = {"X-RapidAPI-Key": API_KEY, "X-RapidAPI-Host": HOST}

# --- ESTADO DO APP ---
if 'analise_pronta' not in st.session_state:
    st.session_state.analise_pronta = False
    st.session_state.jogo_selecionado = None

# --- FUNÇÕES DE CÁLCULO ---
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

@st.cache_data(ttl=3600)
def buscar_dados_l10(team_id):
    try:
        url = f"https://{HOST}/api/v1/team/{team_id}/events/last/0"
        res = requests.get(url, headers=HEADERS, timeout=12)
        if res.status_code == 200:
            events = res.json().get('events', [])[:10]
            if not events: return 1.5, 1.2, []
            marcados = sofridos = 0
            sequencia = []
            for ev in events:
                h_score = ev.get('homeScore', {}).get('current', 0)
                a_score = ev.get('awayScore', {}).get('current', 0)
                if ev['homeTeam']['id'] == team_id:
                    marcados += h_score; sofridos += a_score
                    res_tipo = "V" if h_score > a_score else ("E" if h_score == a_score else "D")
                else:
                    marcados += a_score; sofridos += h_score
                    res_tipo = "V" if a_score > h_score else ("E" if a_score == h_score else "D")
                sequencia.append(res_tipo)
            return (marcados/len(events)), (sofridos/len(events)), sequencia
    except: pass
    return 1.5, 1.2, []

def calcular_probabilidades_1x2(h_m, h_s, a_m, a_s):
    forca_casa = (h_m + a_s) / 2
    forca_fora = (a_m + h_s) / 2
    total = forca_casa + forca_fora + 0.6
    p_casa = (forca_casa / total) * 100
    p_fora = (forca_fora / total) * 100
    p_empate = 100 - p_casa - p_fora
    return max(min(p_casa, 75), 15), max(min(p_empate, 40), 10), max(min(p_fora, 75), 15)

def exibir_forma(lista_resultados):
    html = "<div style='display: flex; justify-content: center; gap: 5px; margin-top: 10px;'>"
    cores = {"V": "#00ff88", "E": "#94a3b8", "D": "#ff4b4b"}
    for r in lista_resultados[::-1]:
        html += f"<span style='background-color:{cores.get(r)}; color:#000; padding:2px 8px; border-radius:50%; font-size:11px; font-weight:bold;'>{r}</span>"
    html += "</div>"
    return html

def barra_dinamica(label, prob, color_mode="normal"):
    cor = "#ffcc00" if color_mode == "1x2" else ("#ff4b4b" if prob < 50 else ("#ffcc00" if prob < 75 else "#00ff88"))
    st.write(f"**{label}:** {prob:.1f}%")
    st.markdown(f"""
        <div style="background-color: #1e252e; border-radius: 10px; height: 8px; width: 100%; margin-bottom: 12px;">
            <div style="background-color: {cor}; width: {prob}%; height: 100%; border-radius: 10px; box-shadow: 0 0 8px {cor}aa;"></div>
        </div>
    """, unsafe_allow_html=True)
    return prob

@st.cache_data(ttl=600)
def carregar_jogos(d):
    try:
        url = f"https://{HOST}/api/v1/sport/football/scheduled-events/{d}"
        res = requests.get(url, headers=HEADERS, timeout=12)
        return res.json().get('events', []) if res.status_code == 200 else []
    except: return []

# --- INTERFACE ---
st.set_page_config(page_title="PROBET EXPERT v12", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #05070a; color: white; }
    .card-1x2 { background: linear-gradient(145deg, #1a1a2e, #0f0f1a); border: 2px solid #ffcc00; padding: 20px; border-radius: 15px; margin-bottom: 20px; }
    .card-gols { background: linear-gradient(145deg, #0a2e1f, #05140d); border: 2px solid #00ff88; padding: 20px; border-radius: 15px; }
    .stat-box { background: rgba(255,255,255,0.05); padding: 10px; border-radius: 8px; text-align: center; margin-top: 10px; }
    .card-palpite { background: linear-gradient(145deg, #2e0a2e, #140514); border: 2px dashed #ff00ff; padding: 25px; border-radius: 15px; text-align: center; margin-top: 25px; }
    h1 { text-shadow: 0 0 15px #ffcc00; color: #ffcc00 !important; text-align: center; }
</style>
""", unsafe_allow_html=True)

st.title("PRO ANÁLISE ESPORTIVA")

data_sel = st.date_input("📅 Data das Partidas", value=datetime.now())
jogos = carregar_jogos(data_sel.strftime('%Y-%m-%d'))

if jogos:
    ligas = sorted(list(set([j['tournament']['name'] for j in jogos])))
    ligas_sel = st.multiselect("🏆 Filtrar Ligas", ligas)
    jogos_f = [j for j in jogos if j['tournament']['name'] in ligas_sel] if ligas_sel else jogos
    
    if jogos_f:
        opcoes = {f"[{ajustar_horario(j.get('startTimestamp', 0))}] {j['homeTeam']['name']} x {j['awayTeam']['name']}": j for j in jogos_f}
        escolha = st.selectbox("🎯 Selecione o Jogo", list(opcoes.keys()))
        
        if st.button("🔍 ANALISAR MÉDIAS E PERFORMANCE (L10)"):
            st.session_state.jogo_selecionado = opcoes[escolha]
            st.session_state.analise_pronta = True

if st.session_state.analise_pronta and st.session_state.jogo_selecionado:
    j = st.session_state.jogo_selecionado
    h_m, h_s, h_seq = buscar_dados_l10(j['homeTeam']['id'])
    a_m, a_s, a_seq = buscar_dados_l10(j['awayTeam']['id'])
    p_v_casa, p_e, p_v_fora = calcular_probabilidades_1x2(h_m, h_s, a_m, a_s)
    exp_gols = ((h_m + a_s)/2) + ((a_m + h_s)/2)

    st.divider()
    # Cabeçalho com Médias de Gols
    col_h, col_vs, col_a = st.columns([2, 1, 2])
    with col_h:
        st.markdown(f"<h2 style='text-align:center;'>{j['homeTeam']['name']}</h2>", unsafe_allow_html=True)
        st.markdown(exibir_forma(h_seq), unsafe_allow_html=True)
        st.markdown(f"""<div class='stat-box'>⚽ Marcados: <b>{h_m:.1f}</b> | 🛡️ Sofridos: <b>{h_s:.1f}</b></div>""", unsafe_allow_html=True)
    with col_vs:
        st.markdown("<h1 style='font-size: 45px; margin-top: 20px;'>VS</h1>", unsafe_allow_html=True)
    with col_a:
        st.markdown(f"<h2 style='text-align:center;'>{j['awayTeam']['name']}</h2>", unsafe_allow_html=True)
        st.markdown(exibir_forma(a_seq), unsafe_allow_html=True)
        st.markdown(f"""<div class='stat-box'>⚽ Marcados: <b>{a_m:.1f}</b> | 🛡️ Sofridos: <b>{a_s:.1f}</b></div>""", unsafe_allow_html=True)

    # Probabilidades 1X2
    st.markdown("<div class='card-1x2'>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; font-weight:800; color:#ffcc00;'>ESTIMATIVA DE RESULTADO FINAL (L10)</p>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1: barra_dinamica(f"Vitória {j['homeTeam']['name']}", p_v_casa, "1x2")
    with c2: barra_dinamica("Empate", p_e, "1x2")
    with c3: barra_dinamica(f"Vitória {j['awayTeam']['name']}", p_v_fora, "1x2")
    st.markdown("</div>", unsafe_allow_html=True)

    # Mercados Gols, Cantos e Cartões
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("<div class='card-gols'>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; color:#00ff88; font-weight:800;'>⚽ GOLS</p>", unsafe_allow_html=True)
        p15 = barra_dinamica("Over 1.5", calcular_poisson(exp_gols, 1))
        p25 = barra_dinamica("Over 2.5", calcular_poisson(exp_gols, 2))
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("<div style='background: linear-gradient(145deg, #0a1f3d, #050d1a); border: 2px solid #00d4ff; padding: 20px; border-radius: 15px;'>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; color:#00d4ff; font-weight:800;'>🚩 CANTOS</p>", unsafe_allow_html=True)
        barra_dinamica("Over 5.5", 87.2)
        barra_dinamica("Over 8.5", 61.5)
        st.markdown("</div>", unsafe_allow_html=True)

    with col3:
        st.markdown("<div style='background: linear-gradient(145deg, #3d0a0a, #1a0505); border: 2px solid #ff4b4b; padding: 20px; border-radius: 15px;'>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; color:#ff4b4b; font-weight:800;'>🟨 CARTÕES</p>", unsafe_allow_html=True)
        barra_dinamica("Over 1.5", 93.1)
        barra_dinamica("Over 3.5", 46.8)
        st.markdown("</div>", unsafe_allow_html=True)

    # Palpite Sugerido
    sugestoes = []
    if p_v_casa > 65: sugestoes.append(f"🏠 Mandante para Vencer")
    elif p_v_fora > 65: sugestoes.append(f"🚀 Visitante para Vencer")
    if p15 > 82: sugestoes.append("🔥 Over 1.5 Gols")
    if p25 > 68: sugestoes.append("⚽ Over 2.5 Gols")
    
    palpite_txt = " / ".join(sugestoes) if sugestoes else "⚖️ Mercado Equilibrado - Aguardar Live"

    st.markdown(f"""
        <div class='card-palpite'>
            <p style='color:#ff00ff; font-weight:800; font-size:1.3rem;'>🎯 SUGESTÃO DE ENTRADA</p>
            <p style='color:white; font-size:1.4rem; font-weight:bold;'>{palpite_txt}</p>
        </div>
    """, unsafe_allow_html=True)

    if st.button("🗑️ REINICIAR"):
        st.session_state.analise_pronta = False
        st.rerun()





