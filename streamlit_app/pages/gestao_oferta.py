# pages/gestao_oferta.py
import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Gestão de Oferta", layout="wide")

# --- CSS PERSONALIZADO (mantendo o visual) ---
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    .stAppDeployButton {display: none;}
    .stButton > button {
        background: #2d6a4f !important;
        color: white !important;
        border-radius: 6px !important;
        padding: 0.25rem 0.75rem !important;
        font-size: 0.75rem !important;
    }
    .stButton > button:hover {
        background: #1b4d3e !important;
    }
    div[data-testid="stExpander"] details summary p {
        font-weight: 600;
        color: #1a3a5c;
    }
    .st-bb {
        background-color: #f4f6f9;
    }
</style>
""", unsafe_allow_html=True)

# --- RECUPERAR DADOS DO CURSO ---
if "sheet_id" not in st.session_state:
    st.warning("⚠️ Nenhum curso selecionado. Volte para a página inicial.")
    st.stop()

SHEET_ID = st.session_state["sheet_id"]
CURSO_NOME = st.session_state.get("curso_nome", "Curso")

# --- FUNÇÃO PARA CARREGAR DADOS ---
@st.cache_data(ttl=60)
def carregar_dados(sheet_id):
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=0"
    try:
        df = pd.read_csv(url, header=1)
        return df
    except Exception as e:
        st.error(f"Erro ao carregar planilha: {e}")
        return None

# --- FUNÇÃO PARA DETECTAR POLOS ---
def detectar_polos(df):
    colunas = df.columns.tolist()
    polos = []
    for col in colunas:
        # Procura por códigos de polo (3 letras maiúsculas)
        if col and len(col) == 3 and col.isupper() and col not in ['PER', 'DIS', 'NOM', 'CAR']:
            polos.append(col)
    return polos

# --- CARREGAR DADOS ---
df = carregar_dados(SHEET_ID)
if df is None or df.empty:
    st.stop()

# --- IDENTIFICAR POLOS ---
POLOS = detectar_polos(df)

# --- TÍTULO ---
st.title(f"📚 Gestão de Oferta de Disciplinas")
st.caption(f"{CURSO_NOME} | 2º semestre / 2026")

# --- ESTATÍSTICAS ---
col1, col2, col3, col4 = st.columns(4)

# Processar dados para estatísticas
total_disciplinas = len(df)
total_polos = len(POLOS)

col1.metric("📚 Disciplinas", total_disciplinas)
col2.metric("🏫 Polos", total_polos)

# Calcular ofertas ativas
ofertas_ativas = 0
for _, row in df.iterrows():
    for polo in POLOS:
        status_col = f"{polo}.1" if f"{polo}.1" in df.columns else None
        if status_col and row[status_col] == 'A':
            ofertas_ativas += 1

col3.metric("✅ Ofertas ativas", ofertas_ativas)
col4.metric("📊 Aproveitamento", f"{ofertas_ativas/(total_disciplinas*total_polos)*100:.0f}%" if total_disciplinas*total_polos > 0 else "0%")

st.divider()

# --- EXIBIR DISCIPLINAS ---
st.subheader("📋 Disciplinas e Ofertas por Polo")

# Filtros
col_f1, col_f2, col_f3 = st.columns(3)
with col_f1:
    busca = st.text_input("🔍 Buscar disciplina", placeholder="Nome ou código...")
with col_f2:
    periodos = sorted(df['Periodo'].dropna().unique())
    periodo_sel = st.selectbox("📌 Período", ["Todos"] + list(periodos))
with col_f3:
    status_sel = st.selectbox("🏷️ Status", ["Todos", "Com oferta", "Sem oferta"])

# Filtrar dados
df_filtrado = df.copy()
if busca:
    df_filtrado = df_filtrado[
        df_filtrado['Disciplina'].str.contains(busca, case=False, na=False) |
        df_filtrado['Nome'].str.contains(busca, case=False, na=False)
    ]
if periodo_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado['Periodo'] == periodo_sel]

# Exibir cada disciplina
for idx, row in df_filtrado.iterrows():
    disciplina_cod = row['Disciplina']
    disciplina_nome = row['Nome']
    periodo = row['Periodo']
    ch = row['Carga Horária']
    
    # Verificar se atende ao filtro de status
    if status_sel != "Todos":
        tem_oferta = False
        for polo in POLOS:
            status_col = f"{polo}.1" if f"{polo}.1" in df.columns else None
            if status_col and row[status_col] == 'A':
                tem_oferta = True
                break
        if status_sel == "Com oferta" and not tem_oferta:
            continue
        if status_sel == "Sem oferta" and tem_oferta:
            continue
    
    with st.expander(f"📖 [{periodo}] {disciplina_cod} - {disciplina_nome} ({ch}h)"):
        # Criar colunas para cada polo
        cols = st.columns(len(POLOS) + 1)
        
        for i, polo in enumerate(POLOS):
            status_col = f"{polo}.1" if f"{polo}.1" in df.columns else None
            is_active = status_col and row[status_col] == 'A'
            
            with cols[i]:
                if is_active:
                    if st.button(f"✅ {polo}", key=f"{disciplina_cod}_{polo}"):
                        # TODO: Implementar salvamento na planilha
                        st.toast(f"💾 {disciplina_cod} - Polo {polo}: desativado", icon="✅")
                else:
                    if st.button(f"❌ {polo}", key=f"{disciplina_cod}_{polo}"):
                        # TODO: Implementar salvamento na planilha
                        st.toast(f"💾 {disciplina_cod} - Polo {polo}: ativado", icon="✅")
        
        # Botão para ativar/desativar todos
        with cols[-1]:
            any_active = False
            for polo in POLOS:
                status_col = f"{polo}.1" if f"{polo}.1" in df.columns else None
                if status_col and row[status_col] == 'A':
                    any_active = True
                    break
            
            if any_active:
                if st.button(f"❌ Desativar todos", key=f"all_{disciplina_cod}"):
                    st.toast(f"💾 {disciplina_cod}: todos os polos desativados", icon="✅")
            else:
                if st.button(f"✅ Ativar todos", key=f"all_{disciplina_cod}"):
                    st.toast(f"💾 {disciplina_cod}: todos os polos ativados", icon="✅")

# --- RODAPÉ ---
st.divider()
st.caption(f"🔄 Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

# --- BOTÃO PARA VOLTAR ---
if st.button("← Voltar para lista de cursos"):
    del st.session_state["sheet_id"]
    del st.session_state["curso_nome"]
    st.switch_page("app.py")  # ← REMOVA O 'v' NO FINAL!