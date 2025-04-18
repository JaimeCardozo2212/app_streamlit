import streamlit as st
from database import promote_to_admin, get_db_connection
from time import sleep

# Esconder navegação padrão
st.markdown("""
    <style>
        [data-testid="stSidebarNav"] { display: none; }
        .metric-box { transition: all 0.5s ease; }
        .metric-box:hover { transform: scale(1.02); }
    </style>
""", unsafe_allow_html=True)

# Verificação mais robusta do estado de login
if not st.session_state.get('logged_in', False):
    st.warning("⚠️ Você precisa fazer login primeiro")
    sleep(1)  # Pequeno delay para visualização da mensagem
    st.switch_page("pages/Login.py")
    st.stop()
    
# Verificação específica para admin
if st.session_state.get('is_admin', False):
    st.success("Acesso autorizado: você é um administrador")
else:
    st.warning("Acesso negado: você não tem privilégios de administrador")
    sleep(2)
    st.switch_page("app.py")
    st.stop()

st.title("Painel de Administração Completo")
    

# Campo de busca na sidebar
with st.sidebar:
    st.subheader("Filtrar Usuários")
    search_term = st.text_input("Buscar por nome, sobrenome ou CPF:", key="search_users")
    
    # Opções de filtro adicionais
    st.markdown("---")
    st.subheader("Filtros Avançados")
    filter_access = st.selectbox(
        "Status de Acesso:",
        ["Todos", "Liberados", "Bloqueados"],
        key="filter_access"
    )
    
    filter_admin = st.selectbox(
        "Tipo de Usuário:",
        ["Todos", "Administradores", "Usuários Comuns"],
        key="filter_admin"
    )

# Lista todos os usuários com filtros aplicados
@st.cache_data
def list_users(search_term, filter_access, filter_admin):
    if st.session_state.get('is_admin'):
    # Conexão com o banco de dados
        conn = get_db_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    # Query base
                    query = """
                    SELECT cpf, nome, sobrenome, cidade, admin, acesso_liberado 
                    FROM users 
                    WHERE 1=1
                    """

                    params = []

                    # Aplica filtro de busca
                    if search_term:
                        query += """
                        AND (LOWER(nome) LIKE LOWER(%s) 
                        OR LOWER(sobrenome) LIKE LOWER(%s) 
                        OR cpf LIKE %s)
                        """
                        search_param = f"%{search_term}%"
                        params.extend([search_param, search_param, search_param])

                    # Aplica filtro de acesso
                    if filter_access == "Liberados":
                        query += " AND acesso_liberado = TRUE"
                    elif filter_access == "Bloqueados":
                        query += " AND acesso_liberado = FALSE"

                    # Aplica filtro de admin
                    if filter_admin == "Administradores":
                        query += " AND admin = TRUE"
                    elif filter_admin == "Usuários Comuns":
                        query += " AND admin = FALSE"

                    query += " ORDER BY created_at DESC"

                    cur.execute(query, params)
                    users = cur.fetchall()

                    return users
            except Exception as e:
                st.error(f"Erro ao acessar o banco de dados: {str(e)}")
            finally:
                conn.close()
    else:
        st.error("Acesso negado: apenas administradores podem acessar esta página")
        st.switch_page("pages/2_pagina.py")
        st.stop()
conn = get_db_connection()
if st.session_state.get('is_admin'):
    if conn:
        try:
            with conn.cursor() as cur:
                # Query base
                query = """
                SELECT cpf, nome, sobrenome, cidade, admin, acesso_liberado 
                FROM users 
                WHERE 1=1
                """

                params = []

                # Aplica filtro de busca
                if search_term:
                    query += """
                    AND (LOWER(nome) LIKE LOWER(%s) 
                    OR LOWER(sobrenome) LIKE LOWER(%s) 
                    OR cpf LIKE %s)
                    """
                    search_param = f"%{search_term}%"
                    params.extend([search_param, search_param, search_param])

                # Aplica filtro de acesso
                if filter_access == "Liberados":
                    query += " AND acesso_liberado = TRUE"
                elif filter_access == "Bloqueados":
                    query += " AND acesso_liberado = FALSE"

                # Aplica filtro de admin
                if filter_admin == "Administradores":
                    query += " AND admin = TRUE"
                elif filter_admin == "Usuários Comuns":
                    query += " AND admin = FALSE"

                query += " ORDER BY created_at DESC"

                cur.execute(query, params)
                users = cur.fetchall()

                # Mostra resultados da busca
                st.subheader(f"Usuários Encontrados: {len(users)}")

                if not users:
                    st.info("Nenhum usuário encontrado com os filtros aplicados")
                else:
                    for cpf, nome, sobrenome, cidade, is_admin, acesso_liberado in users:
                        with st.expander(f"{nome} {sobrenome} - CPF: {cpf}"):
                            # Colunas para exibição de informações
                            col_info1, col_info2, col_info3 = st.columns(3)
                            with col_info1:
                                st.write(f"**Cidade:** {cidade}")
                            with col_info2:
                                st.write(f"**Status Admin:** {'✅ Sim' if is_admin else '❌ Não'}")
                            with col_info3:
                                st.write(f"**Acesso:** {'🔓 Liberado' if acesso_liberado else '🔒 Bloqueado'}")

                            # Linha divisória
                            st.markdown("---")

                            # Colunas para controles administrativos
                            col_control1, col_control2 = st.columns(2)

                            with col_control1:
                                # Controle de acesso
                                new_access_status = st.checkbox(
                                    "Liberar acesso ao sistema",
                                    value=acesso_liberado,
                                    key=f"access_{cpf}"
                                )

                                if new_access_status != acesso_liberado:
                                    cur.execute("""
                                    UPDATE users SET acesso_liberado = %s WHERE cpf = %s
                                    """, (new_access_status, cpf))
                                    conn.commit()
                                    st.success("Status de acesso atualizado com sucesso!")
                                    st.rerun()

                            with col_control2:
                                # Controle de admin
                                if not is_admin:
                                    if st.button(f"Promover a Admin", key=f"promote_{cpf}"):
                                        if promote_to_admin(cpf):
                                            st.success(f"Usuário {nome} promovido a administrador!")
                                            st.rerun()
                                        else:
                                            st.error("Falha na operação")
                                else:
                                    st.write("Usuário já é administrador")
        except Exception as e:
            st.error(f"Erro ao acessar o banco de dados: {str(e)}")
        finally:
            conn.close()
else:
    st.error("Acesso negado: apenas administradores podem acessar esta página")
    st.switch_page("pages/2_pagina.py")
    st.stop()

with st.sidebar:
    if st.button(
        "Voltar para o Painel Principal",
        type="secondary",
        help="Clique para voltar ao painel principal",
        use_container_width=True,
        key="back_to_main"

    ):
        st.switch_page("pages/2_pagina.py")

with st.sidebar:
    if st.button("Logout",
                 use_container_width=True,
                 type="primary",
                 ):
        st.session_state.logged_in = False
        st.session_state.is_admin = False
        st.success("Você foi desconectado com sucesso!")
        sleep(1)
        st.switch_page("app.py")


