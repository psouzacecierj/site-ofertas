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
    }
    .stButton > button:hover {
        background: #1b4d3e;
    }
    div[data-testid="stExpander"] details summary p {
        font-weight: 600;
        color: #1a3a5c;
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

# --- FUNÇÃO PARA SALVAR NA PLANILHA ---
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
        
        # Mapear polos para colunas
        polo_colunas = {}
        for polo in POLOS:
            for i, col in enumerate(headers):
                if col == polo:
                    polo_colunas[polo] = i
                    break
        
        cod_col = 1
        
        # Para cada disciplina
        for _, row in df.iterrows():
            cod = row['Disciplina']
            
            # Encontrar linha
            linha = None
            for i in range(header_row + 1, len(data)):
                if len(data[i]) > cod_col and data[i][cod_col] == cod:
                    linha = i
                    break
            
            if linha is not None:
                for polo in POLOS:
                    status_atual = st.session_state.estado_ofertas.get(f"{cod}_{polo}", False)
                    novo_valor = 'A' if status_atual else 'D'
                    
                    polo_col = polo_colunas.get(polo)
                    if polo_col is not None:
                        status_col = polo_col + 1
                        sheet.update_cell(linha + 1, status_col + 1, novo_valor)
        
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Erro: {str(e)}")
        return False

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
    if st.button("💾 SALVAR TODAS AS ALTERAÇÕES NA PLANILHA", use_container_width=True):
        if salvar_tudo():
            st.success("✅ Todas as alterações foram salvas na planilha!")
            st.rerun()
        else:
            st.error("❌ Erro ao salvar. Verifique os logs.")

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
        <span>🔘 Clique na célula para alternar (depois clique em SALVAR)</span>
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

# --- EXIBIR TABELA ---
st.markdown("""
<style>
    .tabela-ofertas {
        width: 100%;
        border-collapse: collapse;
        font-size: 12px;
        background: white;
        border-radius: 10px;
        overflow: hidden;
    }
    .tabela-ofertas th {
        background: #2d6a4f;
        color: white;
        padding: 8px;
        text-align: center;
        font-weight: 600;
        font-size: 10px;
    }
    .tabela-ofertas td {
        padding: 6px;
        border-bottom: 1px solid #e5e7eb;
        text-align: center;
    }
    .tabela-ofertas tr:hover {
        background: #f9fafb;
    }
    .polo-ativo {
        background: #dcfce7;
        color: #166534;
        padding: 4px 8px;
        border-radius: 16px;
        display: inline-block;
        cursor: pointer;
        font-size: 10px;
        font-weight: 600;
    }
    .polo-inativo {
        background: #f3f4f6;
        color: #9ca3af;
        padding: 4px 8px;
        border-radius: 16px;
        display: inline-block;
        cursor: pointer;
        font-size: 10px;
    }
    .periodo-badge {
        background: #e0e7ff;
        color: #3730a3;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 11px;
        font-weight: 600;
        display: inline-block;
    }
    .disciplina-code {
        font-family: monospace;
        font-size: 11px;
        color: #6b7280;
    }
    .disciplina-nome {
        font-weight: 500;
        text-align: left;
    }
</style>
""", unsafe_allow_html=True)

# Construir tabela HTML
html = '<table class="tabela-ofertas"><thead><tr><th>Período</th><th>Código</th><th>Disciplina</th><th>CH</th>'
for polo in POLOS:
    html += f'<th>{polo}</th>'
html += '</thead><tbody>'

for _, row in df_filtrado.iterrows():
    cod = row['Disciplina']
    html += '<tr>'
    html += f'<td><span class="periodo-badge">{row["Periodo"]}</span></td>'
    html += f'<td><span class="disciplina-code">{cod}</span></td>'
    html += f'<td class="disciplina-nome">{row["Nome"]}</td>'
    html += f'<td>{int(row["Carga Horária"])}h</td>'
    
    for polo in POLOS:
        is_active = st.session_state.estado_ofertas.get(f"{cod}_{polo}", False)
        inst = get_inst(row, polo)
        
        if is_active:
            html += f'<td><span class="polo-ativo" onclick="alert(\'Clique para alternar\')">✓ {inst}</span></td>'
        else:
            html += f'<td><span class="polo-inativo" onclick="alert(\'Clique para alternar\')">—</span></td>'
    html += '</tr>'

html += '</tbody></table>'

st.markdown(html, unsafe_allow_html=True)

# --- RODAPÉ ---
st.divider()
st.caption(f"🔄 Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

# --- BOTÃO VOLTAR ---
if st.button("← Voltar para lista de cursos"):
    if "estado_ofertas" in st.session_state:
        del st.session_state["estado_ofertas"]
    del st.session_state["sheet_id"]
    del st.session_state["curso_nome"]
    st.switch_page("app.py")