import streamlit as st

# # Página inicial simples que redireciona para o login
# st.set_page_config(page_title="Sistema Principal", page_icon="🏠")
# # Oculte a sidebar completamente
st.set_page_config(initial_sidebar_state="collapsed")
st.markdown("""
    <style>
        section[data-testid="stSidebar"] {
            display: none !important;
        }
    </style>
""", unsafe_allow_html=True)
st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {
            display: none;
        }
    </style>
""", unsafe_allow_html=True)


st.switch_page("pages/login.py")
# st.title("Bem-vindo ao Sistema")

# if st.button("Ir para Login"):