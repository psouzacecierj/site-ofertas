# teste_conexao.py
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime  # ← LINHA ADICIONADA!

st.set_page_config(page_title="Teste de Conexão", layout="centered")

st.title("🧪 Teste de Conexão com Google Sheets")

# ID da planilha de teste (NOVA)
SHEET_ID = "1i1dhZA0JhdjouUdbkKat_b4kkmap9x9A54rltw2Fwwk"  # ← USE ESTE ID!

st.write(f"📌 Planilha ID: `{SHEET_ID}`")

# Botão para testar
if st.button("🔌 Testar Conexão"):
    
    st.write("### Passo a passo:")
    
    # Passo 1: Verificar Secrets
    st.write("1. Verificando Secrets...")
    if "gcp_service_account" in st.secrets:
        st.success("✅ Secrets encontrado!")
        st.write(f"   - Email: {st.secrets['gcp_service_account'].get('client_email', 'N/A')}")
    else:
        st.error("❌ Secrets NÃO encontrado!")
        st.stop()
    
    # Passo 2: Criar credenciais
    st.write("2. Criando credenciais...")
    try:
        creds_dict = st.secrets["gcp_service_account"]
        scope = ['https://www.googleapis.com/auth/spreadsheets']
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        st.success("✅ Credenciais criadas!")
    except Exception as e:
        st.error(f"❌ Erro: {e}")
        st.stop()
    
    # Passo 3: Autorizar cliente
    st.write("3. Autorizando cliente...")
    try:
        client = gspread.authorize(creds)
        st.success("✅ Cliente autorizado!")
    except Exception as e:
        st.error(f"❌ Erro: {e}")
        st.stop()
    
    # Passo 4: Abrir planilha
    st.write("4. Abrindo planilha...")
    try:
        sheet = client.open_by_key(SHEET_ID)
        st.success(f"✅ Planilha encontrada: **{sheet.title}**")
    except gspread.exceptions.SpreadsheetNotFound:
        st.error("❌ Planilha NÃO encontrada!")
        st.info("Verifique se a Service Account tem acesso à planilha.")
        st.stop()
    except Exception as e:
        st.error(f"❌ Erro: {e}")
        st.stop()
    
    # Passo 5: Ler dados
    st.write("5. Lendo primeira linha...")
    try:
        worksheet = sheet.sheet1
        primeira_linha = worksheet.row_values(1)
        st.success(f"✅ Leitura OK! Primeira linha: {primeira_linha[:5]}...")
    except Exception as e:
        st.error(f"❌ Erro ao ler: {e}")
        st.stop()
    
    # Passo 6: Escrever dados
    st.write("6. Escrevendo célula B2...")
    try:
        worksheet.update_cell(2, 2, f"Teste {datetime.now()}")
        st.success("✅ Escrita realizada com sucesso!")
    except Exception as e:
        st.error(f"❌ Erro ao escrever: {e}")
        st.stop()
    
    st.balloons()
    st.success("🎉 CONEXÃO COMPLETA! Tudo funcionando!")