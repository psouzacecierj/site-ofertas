# pages/gestao_oferta.py
import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Gestão de Oferta", layout="wide")

# --- CSS PERSONALIZADO ---
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    .stAppDeployButton {display: none;}
    footer {visibility: hidden;}
    .main .block-container {
        padding-top: 0.5rem;
        padding-bottom: 0rem;
        max-width: 100%;
    }
    .stButton > button {
        background: #2d6a4f;
        color: white;
        border-radius: 6px;
        font-size: 0.7rem;
        padding: 0.25rem 0.5rem;
        border: none;
        width: 100%;
    }
    .stButton > button:hover {
        background: #1b4d3e;
    }
    /* Botão inativo (cinza) */
    .stButton > button[kind="secondary"] {
        background: #f3f4f6;
        color: #9ca3af;
    }
    .stButton > button[kind="secondary"]:hover {
        background: #e5e7eb;
    }
    /* Expander com estilo mais compacto */
    .streamlit-expanderHeader {
        font-size: 0.85rem !important;
        font-weight: 500 !important;
    }
    .streamlit-expanderContent {
        padding-top: 0.5rem !important;
    }
</style>
""", unsafe_allow_html=True)

# --- RECUPERAR DADOS DO CURSO ---
if "sheet_id" not in st.session_state:
    st.warning("⚠️ Nenhum curso selecionado. Redirecionando para a página inicial...")
    st.switch_page("app.py")
    st.stop()

# --- FUNÇÃO PARA CARREGAR DADOS ---
@st.cache_data(ttl=60)
def carregar_dados(sheet_id):
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    
    tentativas = [
        {"header": None, "skiprows": None},
        {"header": 0, "skiprows": None},
        {"header": 1, "skiprows": None},
        {"header": 0, "skiprows": 1},
    ]
    
    for tentativa in tentativas:
        try:
            df = pd.read_csv(url, header=tentativa["header"], skiprows=tentativa["skiprows"])
            colunas = df.columns.tolist()
            
            for col in colunas:
                col_lower = str(col).lower().strip()
                if col_lower in ['periodo', 'período', 'period', 'per']:
                    df.rename(columns={col: 'Periodo'}, inplace=True)
                    return df
            
            for col in colunas:
                col_lower = str(col).lower().strip()
                if col_lower in ['disciplina', 'código', 'codigo']:
                    return df
        except:
            continue
    
    st.error("❌ Erro ao carregar planilha.")
    return None

# --- FUNÇÃO PARA DETECTAR POLOS ---
def detectar_polos(df):
    colunas = df.columns.tolist()
    polos = []
    polos_conhecidos = ['ARE', 'BJE', 'CAN', 'CGR', 'ITA', 'ITO', 'MAC', 'NIG', 
                        'PAR', 'PIR', 'RBO', 'RES', 'SAQ', 'SFI', 'SFR', 'SPE', 'VRE',
                        'BRO', 'MAG', 'NFR', 'PET', 'ROC', 'SGO']
    
    for col in colunas:
        col_str = str(col).strip()
        if (len(col_str) == 3 and col_str.isupper()) or col_str in polos_conhecidos:
            if col_str not in polos and col_str not in ['PER', 'DIS', 'NOM', 'CAR', 'EAD']:
                polos.append(col_str)
    return polos

# --- FUNÇÃO PARA OBTER STATUS DE UM POLO ---
def get_status(row, polo, df):
    if polo in row.index:
        polo_idx = df.columns.get_loc(polo)
        if polo_idx + 1 < len(df.columns):
            status_col = df.columns[polo_idx + 1]
            if status_col in row.index and pd.notna(row[status_col]):
                valor = str(row[status_col]).strip().upper()
                if valor == 'A':
                    return 'A'
    return 'D'

# --- FUNÇÃO PARA OBTER INSTITUIÇÃO DE UM POLO ---
def get_inst(row, polo):
    if polo in row.index and pd.notna(row[polo]):
        inst = str(row[polo]).strip()
        if inst and inst != 'nan':
            return inst
    return '—'

# --- CARREGAR DADOS ---
df = carregar_dados(SHEET_ID)
if df is None or df.empty:
    st.stop()

# --- GARANTIR COLUNA Periodo ---
if 'Periodo' not in df.columns:
    for col in df.columns:
        col_lower = str(col).lower().strip()
        if col_lower in ['periodo', 'período', 'period', 'per']:
            df.rename(columns={col: 'Periodo'}, inplace=True)
            break

if 'Periodo' not in df.columns:
    st.error("❌ Coluna 'Periodo' não encontrada")
    st.stop()

# --- IDENTIFICAR POLOS ---
POLOS = detectar_polos(df)

# --- INICIALIZAR ESTADO DAS OFERTAS NA SESSION ---
if "estado_ofertas" not in st.session_state:
    st.session_state.estado_ofertas = {}
    for _, row in df.iterrows():
        cod = row['Disciplina']
        for polo in POLOS:
            status = get_status(row, polo, df)
            st.session_state.estado_ofertas[f"{cod}_{polo}"] = (status == 'A')

# --- FUNÇÃO PARA ALTERNAR ---
def toggle(cod, polo):
    key = f"{cod}_{polo}"
    st.session_state.estado_ofertas[key] = not st.session_state.estado_ofertas[key]

# --- FUNÇÃO PARA SALVAR (APENAS ALTERAÇÕES) ---
def salvar_tudo():
    try:
        creds_dict = st.secrets["gcp_service_account"]
        scope = ['https://www.googleapis.com/auth/spreadsheets']
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)
        
        sheet = client.open_by_key(SHEET_ID).sheet1
        data = sheet.get_all_values()
        
        # Encontrar cabeçalhos
        header_row = 1
        for i, row in enumerate(data):
            if row and ('Disciplina' in row or 'Código' in row):
                header_row = i
                break
        
        headers = data[header_row]
        cod_col = 1
        
        # Mapear código da disciplina para linha
        linha_por_codigo = {}
        for i in range(header_row + 1, len(data)):
            row = data[i]
            if len(row) > cod_col and row[cod_col]:
                linha_por_codigo[row[cod_col]] = i + 1
        
        # Mapear APENAS colunas de Status
        status_colunas = {}
        for i, col in enumerate(headers):
            if col == 'Status':
                if i > 0:
                    polo_esquerda = headers[i - 1]
                    if polo_esquerda in POLOS:
                        status_colunas[polo_esquerda] = i + 1
        
        # Preparar APENAS as atualizações que mudaram
        updates = []
        total_alteracoes = 0
        
        for _, row in df.iterrows():
            cod = row['Disciplina']
            linha = linha_por_codigo.get(cod)
            if not linha:
                continue
            
            for polo in POLOS:
                status_col = status_colunas.get(polo)
                if status_col:
                    status_atual = st.session_state.estado_ofertas.get(f"{cod}_{polo}", False)
                    novo_valor = 'A' if status_atual else 'D'
                    
                    status_original = get_status(row, polo, df)
                    if status_original != novo_valor:
                        total_alteracoes += 1
                        updates.append({
                            'range': f'{gspread.utils.rowcol_to_a1(linha, status_col)}',
                            'values': [[novo_valor]]
                        })
        
        if updates:
            sheet.batch_update(updates)
        
        st.cache_data.clear()
        return True, total_alteracoes
    except Exception as e:
        return False, str(e)

# --- TÍTULO ---
st.markdown(f"""
<div style="background: #2d6a4f; padding: 0.8rem 2rem; border-radius: 10px; margin-bottom: 1rem;">
    <h1 style="color: white; margin: 0; font-size: 1.1rem;">📚 Gestão de Oferta de Disciplinas</h1>
    <p style="color: rgba(255,255,255,0.8); margin: 0.2rem 0 0 0; font-size: 0.7rem;">{CURSO_NOME} | 2º semestre / 2026</p>
</div>
""", unsafe_allow_html=True)

# --- BOTÃO SALVAR ---
col_s1, col_s2, col_s3 = st.columns([1, 2, 1])
with col_s2:
    if st.button("💾 SALVAR ALTERAÇÕES NA PLANILHA", use_container_width=True):
        success, resultado = salvar_tudo()
        if success:
            st.success(f"✅ {resultado} alterações salvas na planilha!")
            st.rerun()
        else:
            st.error(f"❌ Erro: {resultado}")

st.markdown("---")

# --- FILTROS ---
col_f1, col_f2, col_f3 = st.columns([2, 1, 1])
with col_f1:
    busca = st.text_input("🔍 Buscar disciplina", placeholder="Nome ou código...")
with col_f2:
    periodos = sorted([p for p in df['Periodo'].dropna().unique() if str(p) != 'nan'], key=lambda x: str(x))
    periodo_sel = st.selectbox("Período", ["Todos"] + list(periodos))
with col_f3:
    status_sel = st.selectbox("Status", ["Todos", "Com oferta", "Sem oferta"])

# --- LEGENDA ---
st.markdown("""
<div style="display: flex; gap: 20px; margin-bottom: 1rem; flex-wrap: wrap; font-size: 11px;">
    <div style="display: flex; align-items: center; gap: 6px;">
        <span style="background: #dcfce7; color: #166534; padding: 2px 10px; border-radius: 4px;">✓ Oferta ativa</span>
    </div>
    <div style="display: flex; align-items: center; gap: 6px;">
        <span style="background: #f3f4f6; color: #9ca3af; padding: 2px 10px; border-radius: 4px;">— Sem oferta</span>
    </div>
    <div style="display: flex; align-items: center; gap: 6px;">
        <span>🔘 Clique no botão para alternar</span>
    </div>
</div>
""", unsafe_allow_html=True)

# --- FILTRAR DADOS ---
df_filtrado = df.copy()
if busca:
    df_filtrado = df_filtrado[df_filtrado['Nome'].astype(str).str.contains(busca, case=False, na=False) |
                              df_filtrado['Disciplina'].astype(str).str.contains(busca, case=False, na=False)]
if periodo_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado['Periodo'].astype(str) == str(periodo_sel)]
if status_sel != "Todos":
    if status_sel == "Com oferta":
        df_filtrado = df_filtrado[[any(st.session_state.estado_ofertas.get(f"{row['Disciplina']}_{polo}", False) for polo in POLOS) for _, row in df_filtrado.iterrows()]]
    else:
        df_filtrado = df_filtrado[[not any(st.session_state.estado_ofertas.get(f"{row['Disciplina']}_{polo}", False) for polo in POLOS) for _, row in df_filtrado.iterrows()]]

# --- EXIBIR TABELA COM BOTÕES STREAMLIT (NATIVOS) ---
for periodo in sorted(df_filtrado['Periodo'].dropna().unique(), key=lambda x: str(x)):
    st.markdown(f"#### 📌 PERÍODO {periodo}")
    
    df_periodo = df_filtrado[df_filtrado['Periodo'] == periodo]
    
    for _, row in df_periodo.iterrows():
        cod = row['Disciplina']
        nome = row['Nome']
        ch = int(row['Carga Horária']) if pd.notna(row['Carga Horária']) else 0
        
        with st.expander(f"[{periodo}] {cod} - {nome} ({ch}h)"):
            # Criar colunas para os polos + ação
            cols = st.columns(len(POLOS) + 1)
            
            for i, polo in enumerate(POLOS):
                with cols[i]:
                    is_active = st.session_state.estado_ofertas.get(f"{cod}_{polo}", False)
                    inst = get_inst(row, polo)
                    
                    if is_active:
                        if st.button(f"✅ {polo}", key=f"{cod}_{polo}_ativo", use_container_width=True):
                            toggle(cod, polo)
                            st.rerun()
                    else:
                        if st.button(f"❌ {polo}", key=f"{cod}_{polo}_inativo", use_container_width=True):
                            toggle(cod, polo)
                            st.rerun()
            
            # Botão para ativar/desativar todos
            with cols[-1]:
                any_active = any(st.session_state.estado_ofertas.get(f"{cod}_{polo}", False) for polo in POLOS)
                if any_active:
                    if st.button(f"❌ Desativar todos", key=f"all_{cod}_desativar", use_container_width=True):
                        for polo in POLOS:
                            toggle(cod, polo)
                        st.rerun()
                else:
                    if st.button(f"✅ Ativar todos", key=f"all_{cod}_ativar", use_container_width=True):
                        for polo in POLOS:
                            toggle(cod, polo)
                        st.rerun()
    
    st.markdown("---")

# --- RODAPÉ ---
st.caption(f"🔄 Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

# --- BOTÃO VOLTAR ---
if st.button("← Voltar para lista de cursos"):
    if "estado_ofertas" in st.session_state:
        del st.session_state["estado_ofertas"]
    del st.session_state["sheet_id"]
    del st.session_state["curso_nome"]
    st.switch_page("app.py")