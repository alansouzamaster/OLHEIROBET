st.markdown("""
<style>

/* FUNDO GERAL */
.stApp {
    background: linear-gradient(180deg,#0b0f14,#111827);
    color: #e6edf3;
}

/* TITULOS */
h1, h2, h3 {
    color:#ffc107;
    font-weight:700;
}

/* CARDS METRIC */
.stMetric {
    background: linear-gradient(145deg,#1a1f27,#222831);
    padding:18px;
    border-radius:14px;
    border:1px solid #30363d;
    box-shadow:0 4px 15px rgba(0,0,0,0.4);
    transition:0.2s;
}

.stMetric:hover{
    transform:translateY(-3px);
    box-shadow:0 8px 20px rgba(0,0,0,0.6);
}

/* VALORES METRIC */
div[data-testid="stMetricValue"]{
    color:#ffd54f !important;
    font-size:28px !important;
}

/* CARDS DE DESTAQUE */
.oportunidade-card{
    background:linear-gradient(160deg,#1c2128,#151a20);
    padding:18px;
    border-radius:12px;
    border-left:4px solid #ffc107;
    margin-bottom:15px;
    min-height:160px;
    box-shadow:0 5px 20px rgba(0,0,0,0.45);
    transition:0.2s;
}

.oportunidade-card:hover{
    transform:scale(1.02);
}

/* BADGE HORARIO */
.horario-badge{
    background:#1f2933;
    color:#ffc107;
    padding:4px 12px;
    border-radius:6px;
    font-weight:bold;
    font-size:13px;
}

/* BOTÕES */
.stButton>button{
    width:100%;
    background:linear-gradient(90deg,#ffc107,#ffda4d);
    color:black;
    font-weight:700;
    border-radius:10px;
    border:none;
    padding:10px;
    font-size:16px;
    box-shadow:0 4px 12px rgba(255,193,7,0.3);
}

.stButton>button:hover{
    transform:scale(1.02);
}

/* BOX RESULTADOS */
.res-box{
    text-align:center;
    padding:14px;
    border-radius:10px;
    font-weight:bold;
    color:white;
    margin-bottom:12px;
    font-size:20px;
    box-shadow:0 4px 12px rgba(0,0,0,0.4);
}

/* VS CENTRAL */
.header-vs{
    text-align:center;
    color:#ffc107;
    font-size:44px;
    font-weight:800;
    margin-top:10px;
}

/* DIVISOR */
hr{
    border:1px solid #2c3440;
}

</style>
""", unsafe_allow_html=True)
