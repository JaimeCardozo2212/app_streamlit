import streamlit as st
import psycopg2  # Mudei de sqlite3 para psycopg2
import hashlib
import os
import re
from datetime import datetime
from time import sleep
from psycopg2 import sql, extras


# Configuração inicial
st.set_page_config(
    page_title="Bem Vindo ao Sistema",
    page_icon="🔒",
    layout="centered"
)
# Ocultar sidebar e outros elementos não necessários
st.markdown("""
    <style>
        [data-testid="stSidebarNav"], section[data-testid="stSidebar"] {
            display: none !important;
        }
    </style>
""", unsafe_allow_html=True)

# Configurações do PostgreSQL na nuvem
DB_CONFIG = {
    'host': st.secrets["db"]["host"],
    'database': st.secrets["db"]["database"],
    'user': st.secrets["db"]["user"],
    'password': st.secrets["db"]["password"],
    'port': st.secrets["db"]["port"],
    'sslmode': 'require'
}


# Funções do banco de dados
def get_db_connection():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        st.error(f"Erro ao conectar ao banco de dados: {str(e)}")
        return None  # explícito, para evitar erro de cursor

def init_db():
    """Garante que a tabela existe com todas as colunas necessárias"""
    try:
        conn = get_db_connection()
        if conn is None:
            st.error("Falha ao conectar ao banco de dados")
            return None

        with conn.cursor() as cur:
            # Verifica se a tabela existe
            cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'users'
            );
            """)
            exists = cur.fetchone()[0]

            if not exists:
                cur.execute("""
                CREATE TABLE users (
                    id SERIAL PRIMARY KEY,
                    nome VARCHAR(100) NOT NULL,
                    sobrenome VARCHAR(100) NOT NULL,
                    cpf VARCHAR(11) UNIQUE NOT NULL,
                    cidade VARCHAR(100) NOT NULL,
                    password_hash BYTEA NOT NULL,
                    salt BYTEA NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    admin BOOLEAN DEFAULT FALSE,
                    acesso_liberado BOOLEAN DEFAULT TRUE  -- Nova coluna
                )
                """)
                conn.commit()
            else:
                # Verifica e adiciona colunas faltantes
                columns_to_check = ['acesso_liberado', 'nome', 'sobrenome', 'cidade', 'admin']
                
                for column in columns_to_check:
                    cur.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='users' AND column_name=%s
                    """, (column,))
                    if not cur.fetchone():
                        if column == 'acesso_liberado':
                            cur.execute("ALTER TABLE users ADD COLUMN acesso_liberado BOOLEAN DEFAULT TRUE")
                        elif column == 'nome':
                            cur.execute("ALTER TABLE users ADD COLUMN nome VARCHAR(100) NOT NULL DEFAULT 'Nome não informado'")
                        # ... (similar para outras colunas)
                        conn.commit()

        return conn
    except Exception as e:
        st.error(f"Erro ao inicializar banco de dados: {str(e)}")
        if conn:
            conn.close()
        return None
    
def is_user_admin(cpf):
    """Verifica se o usuário tem privilégios de admin"""
    conn = get_db_connection()
    if conn is None:
        return False
    
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT admin FROM users WHERE cpf = %s", (cpf,))
            result = cur.fetchone()
            return result[0] if result else False
    except Exception as e:
        st.error(f"Erro ao verificar privilégios de admin: {str(e)}")
        return False
    finally:
        conn.close()


def hash_password(password, salt=None):
    if salt is None:
        salt = os.urandom(32)
    return hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000), salt


def verify_user(cpf, password):
    conn = get_db_connection()
    if conn is None:
        return False
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
            SELECT password_hash, salt, nome, sobrenome, cidade, admin, acesso_liberado 
            FROM users WHERE cpf = %s
            """, (cpf,))
            result = cur.fetchone()
            
            if result:
                stored_hash, salt, nome, sobrenome, cidade, admin, acesso_liberado = result
                
                if not acesso_liberado:
                    st.error("Seu acesso não está liberado. Entre em contato com o administrador.")
                    return False
                
                stored_hash = bytes(stored_hash)
                salt = bytes(salt)
                new_hash, _ = hash_password(password, salt)
                
                if new_hash == stored_hash:
                    st.session_state.nome = nome
                    st.session_state.sobrenome = sobrenome
                    st.session_state.cidade = cidade
                    st.session_state.is_admin = admin
                    return True
            return False
    finally:
        conn.close()


def is_valid_cpf(cpf):
    """Valida formato do CPF"""
    return re.fullmatch(r'\d{11}', cpf) is not None

def promote_to_admin(cpf):
    """Promove um usuário a admin"""
    conn = get_db_connection()
    if conn is None:
        return False
    
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE users SET admin = TRUE WHERE cpf = %s", (cpf,))
            conn.commit()
            return cur.rowcount > 0
    except Exception as e:
        st.error(f"Erro ao promover usuário: {str(e)}")
        conn.rollback()
        return False
    finally:
        conn.close()

# Interface de Login (mantida igual, apenas atualizei as queries)
st.title("🔒 Bem Vindo ao Sistema")
st.markdown("*Por favor, faça login ou registre-se para continuar*")

tab_login, tab_register, tab_recover = st.tabs(["Login", "Cadastro", "Recuperar Senha"])

with tab_login:
    with st.form("login_form"):
        cpf = st.text_input("CPF (apenas números)", key="login_cpf", max_chars=11)
        password = st.text_input("Senha", type="password", key="login_pass")
        submit_login = st.form_submit_button("Entrar")
        
        if submit_login:
            if not is_valid_cpf(cpf):
                st.error("CPF inválido. Deve conter exatamente 11 dígitos numéricos.")
            elif verify_user(cpf, password):
                st.session_state.logged_in = True
                st.session_state.cpf = cpf
                st.success(f"Bem-vindo, {st.session_state.nome}!")
                sleep(1)
                st.switch_page("pages/2_pagina.py")
            else:
                st.error("CPF ou senha inválidos")

with tab_register:
    with st.form("register_form"):
        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input("Nome", key="reg_nome")
        with col2:
            sobrenome = st.text_input("Sobrenome", key="reg_sobrenome")
        
        new_cpf = st.text_input("CPF (apenas números)", key="reg_cpf", max_chars=11)
        cidade = st.text_input("Cidade", key="reg_cidade")
        new_pass = st.text_input("Senha (mínimo de 6 caracteres)", type="password", key="reg_pass")
        confirm_pass = st.text_input("Confirme a senha", type="password", key="conf_pass")
        
        # Se for admin, pode cadastrar outros admins
        is_admin = False
        if st.session_state.get('is_admin'):
            is_admin = st.checkbox("Usuário é administrador?", key="admin_check")
        
        submit_register = st.form_submit_button("Cadastrar")
        
        if submit_register:
            if not nome or not sobrenome or not cidade:
                st.error("Todos os campos pessoais são obrigatórios!")
            elif not is_valid_cpf(new_cpf):
                st.error("CPF inválido. Deve conter exatamente 11 dígitos numéricos.")
            elif new_pass != confirm_pass:
                st.error("As senhas não coincidem!")
            elif len(new_pass) < 6:
                st.error("A senha deve ter pelo menos 6 caracteres")
            else:
                conn = init_db()
                if conn is None:
                    st.error("Não foi possível estabelecer conexão com o banco de dados")
                else:
                    try:
                        with conn.cursor() as cur:
                            # Verifica se CPF já existe
                            cur.execute("SELECT cpf FROM users WHERE cpf = %s", (new_cpf,))
                            if cur.fetchone():
                                st.error("Este CPF já está cadastrado")
                            else:
                                password_hash, salt = hash_password(new_pass)
                                # No formulário de cadastro (tab_register), após a inserção do usuário:
                                cur.execute(
                                    """INSERT INTO users 
                                    (nome, sobrenome, cpf, cidade, password_hash, salt, admin, acesso_liberado) 
                                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                                    (nome, sobrenome, new_cpf, cidade, password_hash, salt, is_admin, False)  # Novo usuário tem acesso liberado por padrão
                                )
                                
                                conn.commit()
                                st.success("Cadastro realizado com sucesso!")
                                sleep(1.5)
                                st.switch_page("app.py")
                    except Exception as e:
                        st.error(f"Erro durante o cadastro: {str(e)}")
                        conn.rollback()
                    finally:
                        if conn:
                            conn.close()
with tab_recover:
    # Primeiro formulário para verificar o CPF
    with st.form("recover_form"):
        recovery_cpf = st.text_input("Digite seu CPF", key="rec_cpf", max_chars=11)
        submit_recover = st.form_submit_button("Redefinir Senha")
        
        if submit_recover:
            if not is_valid_cpf(recovery_cpf):
                st.error("CPF inválido. Deve conter exatamente 11 dígitos numéricos.")
            else:
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute("SELECT cpf FROM users WHERE cpf = %s", (recovery_cpf,))
                
                if cur.fetchone():
                    st.session_state.reset_cpf = recovery_cpf
                    st.success("CPF verificado. Por favor, defina sua nova senha abaixo.")
                else:
                    st.error("CPF não cadastrado no sistema")
                conn.close()
    
    # Formulário SEPARADO para nova senha
    if 'reset_cpf' in st.session_state:
        with st.form("new_password_form"):
            new_password = st.text_input("Nova senha", type="password")
            confirm_password = st.text_input("Confirme a nova senha", type="password")
            submit_new_pass = st.form_submit_button("Atualizar Senha")
            
            if submit_new_pass:
                if new_password != confirm_password:
                    st.error("As senhas não coincidem!")
                elif len(new_password) < 6:
                    st.error("A senha deve ter pelo menos 6 caracteres")
                else:
                    conn = get_db_connection()
                    cur = conn.cursor()
                    password_hash, salt = hash_password(new_password)
                    cur.execute(
                        "UPDATE users SET password_hash = %s, salt = %s WHERE cpf = %s",
                        (password_hash, salt, st.session_state.reset_cpf)
                    )
                    conn.commit()
                    st.success("Senha atualizada com sucesso!")
                    del st.session_state.reset_cpf
                    conn.close()
                    sleep(1)
                    st.switch_page("app.py")



