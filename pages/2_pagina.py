import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
from time import sleep



# --- CONSTANTES E CONFIGURAÇÕES ---
COLUNAS_METRICAS = {
    'valor': [
        'valor efetivo de repasse', 'implantação', 'componente fixo esf',
        'vínculo e acompanhamento territorial esf', 'qualidade esf',
        'valor custeio emulti', 'valor componente qualidade',
        'valor custeio esb 40h', 'ceo municipal', 'lrpd municipal',
        'valor', 'total', 'valor eapp municipal'
    ],
    'credenciadas': [
        'qtde. esf credenciadas', 'qtde. emulti credenciadas',
        'qtde. eap credenciadas', 'qtde. esb ch diferenciada credenciada',
        'qt. uom credenciada', 'qtde. ecr credenciadas',
        'qtde. esfrb credenciado', 'qt. acs credenciado',
        'qtde. ubsf credenciado', 'qtde. microscopista credenciado',
        'qtde. eapp municipal credenciada'
    ],
    'incompletas': [
        'qtde. esf incompletas - 75%',
        'qtde. esf incompletas - 50%',
        'qtde. esf incompletas - 25%'
    ]
}

if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.warning("⚠️ Você precisa fazer login primeiro")
    st.switch_page("pages/Login.py")
    st.stop()
# --- FUNÇÕES AUXILIARES ---
@st.cache_data
def load_data():
    try:
        with pd.ExcelFile("documentos/download.xlsx") as xls:
            return {sheet: xls.parse(sheet) for sheet in xls.sheet_names}
    except Exception as e:
        st.error(f"Erro ao carregar o arquivo: {str(e)}")
        st.stop()

def create_metric_box(col, title, value, color="#03FF25", border_color="#ddd"):
    col.markdown(
        f"""
        <div style=
        ">
            <div style="font-size: 0.9em; color: {color}; margin-bottom: 10px;">{title}</div>
            <div style="font-size: 1.7em; font-weight: bold;">{value}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(layout="wide", page_title="Dashboard Financeiro de Saúde")
st.title("📊 Atenção Primária à Saúde Relatório de Pagamento")

# Esconder navegação padrão
st.markdown("""
    <style>
        [data-testid="stSidebarNav"] { display: none; }
        .metric-box { transition: all 0.3s ease; }
        .metric-box:hover { transform: scale(1.02); }
    </style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("#### **Menu Principal**")
    
    # Botão de Logout com cor vermelha e ícone
    for _ in range(39):  # Ajuste o número de linhas vazias
        st.write("")
    
    if st.session_state.get('is_admin'):
    # Mostrar funcionalidades exclusivas para admin
        if st.button(
            "Admin",
            type="secondary",
            help="Clique para acessar a página de administração",
            use_container_width=True,
            ):
            st.session_state.logged_in = True
            st.session_state.is_admin = True
            st.switch_page("pages/pagina_admin.py")
    if st.button("Logout",
                 use_container_width=True,
                help="Clique para sair do sistema",
                type="primary",
                 ):
        st.session_state.logged_in = False
        st.session_state.is_admin = False
        st.success("Você foi desconectado com sucesso!")
        sleep(1)
        st.switch_page("app.py")
    
if st.session_state.get('is_admin'):
    # Mostrar funcionalidades exclusivas para admin
    st.write("Você tem privilégios de administrador!")
    # Exemplo: botão para adicionar novo admin
else:
    st.write("Bem-vindo usuário padrão")   

# --- CONTEÚDO PRINCIPAL ---
st.header("🔍 Análise Detalhada dos Dados")
sheets = load_data()
selected_sheet = st.selectbox("Selecione a planilha para análise", list(sheets.keys()))
df = sheets[selected_sheet].dropna(how='all')

# --- SEÇÃO DE MÉTRICAS ---
st.subheader("📊 Métricas Financeiras")

# Linha 1 de métricas
col1, col2, col3, col4 = st.columns(4)

# Métricas financeiras principais
value_columns = [col for col in df.columns 
                if str(col).lower() in [word.lower() for word in COLUNAS_METRICAS['valor']]]
value_integral = [col for col in df.columns 
                if str(col).lower() in ['valor integral', 'implantação']]
if value_integral:
    col1.metric("Valor Integral", f"R$ {df[value_integral].sum().sum():,.2f}")
if 'Desconto' in df.columns:
    col2.metric("Total Descontos", f"R$ {df['Desconto'].sum():,.2f}")
if value_columns:
    col3.metric("Valor Repasse", f"R$ {df[value_columns].sum().sum():,.2f}")

col4.metric("Registros", len(df))

# Linha 2 de métricas
cols = st.columns(8)
metric_cols = {
    'credenciadas': (cols[0], COLUNAS_METRICAS['credenciadas'], "#03FF25"),
    'com portaria': (cols[1], ['qtde. esf com portaria de homologação'], "#03FF25"),
    'pagas': (cols[2], ['qtde. esf pagas'], "#03FF25"),
    'completas': (cols[3], ['qtde. esf completas'], "#03FF25"),
    'incom 75%': (cols[4], ['qtde. esf incompletas - 75%'], "#FF0000"),
    'incom 50%': (cols[5], ['qtde. esf incompletas - 50%'], "#FF0000"),
    'incom 25%': (cols[6], ['qtde. esf incompletas - 25%'], "#FF0000")
}

for name, (col, terms, color) in metric_cols.items():
    matching_cols = [c for c in df.columns if any(t in str(c).lower() for t in terms)]
    if matching_cols:
        total = df[matching_cols].sum().sum()
        title = matching_cols[0] if name not in ['incom 75%', 'incom 50%', 'incom 25%'] else name.replace('incom', 'Incompletas')
        create_metric_box(col, title, total, color)
    else:
        col.empty()

# --- VISUALIZAÇÃO DOS DADOS ---
st.subheader("📈 Visualização dos Dados")

tab1, tab2 = st.tabs(["Tabela", "Gráficos"])

with tab1:
    st.dataframe(df, height=400, use_container_width=True)
    
with tab2:
    if value_columns:
        chart_type = st.selectbox("Tipo de gráfico", ["Barras", "Pizza", "Linhas"])
        x_axis = st.selectbox("Eixo X", [col for col in df.columns if col not in value_columns])
        
        if chart_type == "Barras":
            fig = px.bar(df, x=x_axis, y=value_columns[0], 
                        color='UF' if 'UF' in df.columns else None,
                        template="plotly_white")
        elif chart_type == "Pizza":
            fig = px.pie(df, names=x_axis, values=value_columns[0],
                        hole=0.3)
        else:
            fig = px.line(df, x=x_axis, y=value_columns[0],
                        color='UF' if 'UF' in df.columns else None)
        
        fig.update_layout(margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig, use_container_width=True)

# --- EXPORTAÇÃO DE DADOS ---
st.subheader("💾 Exportar Dados")
export_format = st.radio("Formato", ["CSV", "Excel"], horizontal=True, label_visibility="collapsed")

if export_format == "CSV":
    st.download_button(
        "Baixar CSV",
        df.to_csv(index=False).encode('utf-8'),
        f"{selected_sheet}.csv",
        "text/csv"
    )
else:
    excel_buffer = BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name=selected_sheet)
    st.download_button(
        "Baixar Excel",
        excel_buffer.getvalue(),
        f"{selected_sheet}.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    
