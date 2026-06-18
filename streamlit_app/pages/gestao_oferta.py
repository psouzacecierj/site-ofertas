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
    
    /* Tabela com scroll no topo */
    .tabela-wrapper {
        overflow-x: auto;
        overflow-y: auto;
        border-radius: 10px;
        border: 1px solid #e5e7eb;
        background: white;
        max-height: 600px;
        position: relative;
        display: flex;
        flex-direction: column;
    }
    
    .tabela-ofertas {
        width: 100%;
        border-collapse: collapse;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-size: 12px;
        min-width: 800px;
        margin-top: 0;
    }
    
    .tabela-ofertas th {
        background: #2d6a4f;
        color: white;
        padding: 10px 6px;
        text-align: center;
        font-weight: 600;
        font-size: 10px;
        white-space: nowrap;
        position: sticky;
        top: 0;
        z-index: 10;
    }
    
    .tabela-ofertas td {
        padding: 8px 6px;
        border-bottom: 1px solid #f3f4f6;
        vertical-align: middle;
    }
    
    .tabela-ofertas tr:hover {
        background: #f9fafb;
    }
    
    .periodo-badge {
        background: #e0e7ff;
        color: #3730a3;
        padding: 3px 9px;
        border-radius: 12px;
        font-size: 11px;
        font-weight: 600;
        display: inline-block;
        white-space: nowrap;
    }
    
    .disciplina-code {
        font-family: monospace;
        font-size: 11px;
        color: #6b7280;
        white-space: nowrap;
    }
    
    .disciplina-nome {
        font-weight: 500;
        text-align: left;
        max-width: 200px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    
    .carga {
        font-size: 11px;
        color: #9ca3af;
        white-space: nowrap;
    }
    
    .polo-cell {
        text-align: center;
        cursor: pointer;
        padding: 4px 2px;
    }
    
    .polo-ativo {
        background: #dcfce7;
        color: #166534;
        padding: 4px 8px;
        border-radius: 16px;
        font-size: 10px;
        font-weight: 600;
        display: inline-block;
        white-space: nowrap;
        cursor: pointer;
    }
    
    .polo-inativo {
        background: #f3f4f6;
        color: #9ca3af;
        padding: 4px 8px;
        border-radius: 16px;
        font-size: 10px;
        display: inline-block;
        white-space: nowrap;
        cursor: pointer;
    }
    
    .btn-acao {
        background: #fee2e2;
        color: #991b1b;
        border: none;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 10px;
        font-weight: 600;
        cursor: pointer;
        width: 100%;
        white-space: nowrap;
    }
    
    .btn-acao-ativar {
        background: #dcfce7;
        color: #166534;
    }
    
    .section-header td {
        background: #f1f5f9;
        padding: 8px 12px;
        font-weight: 700;
        color: #475569;
    }
    
    .section-spacer td {
        height: 12px;
        background: #f4f6f9;
        border: none;
    }
    
    .texto-centro {
        text-align: center;
    }
</style>

<script>
// Garantir que a barra de rolagem fique no topo
function fixScrollBar() {
    const wrapper = document.querySelector('.tabela-wrapper');
    if (wrapper) {
        wrapper.scrollTop = 0;
        wrapper.scrollLeft = 0;
    }
}

// Executar quando a página carregar
document.addEventListener('DOMContentLoaded', function() {
    fixScrollBar();
    setTimeout(fixScrollBar, 200);
});

// Observar mudanças na tabela
const observer = new MutationObserver(function() {
    fixScrollBar();
});
observer.observe(document.body, { childList: true, subtree: true });
</script>
""", unsafe_allow_html=True)

# --- RECUPERAR DADOS DO CURSO ---
if "sheet_id" not in st.session_state:
    st.warning("⚠️ Nenhum curso selecionado. Redirecionando...")
    st.switch_page("app.py")
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

# --- FUNÇÃO PARA DETECTAR POLOS (ATUALIZADA) ---
def detectar_polos(df):
    colunas = df.columns.tolist()
    polos = []
    polos_conhecidos = [
        'ARE', 'BJE', 'CAN', 'CGR', 'ITA', 'ITO', 'MAC', 'NIG', 
        'PAR', 'PIR', 'RBO', 'RES', 'SAQ', 'SFI', 'SFR', 'SPE', 'VRE',
        'BRO', 'MAG', 'NFR', 'PET', 'ROC', 'SGO',
        'BPI', 'DCA', 'ITG', 'NIT', 'PTY', 'RFL', 'TRI'
    ]
    
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

# --- FUNÇÃO PARA SALVAR ---
def salvar_tudo():
    try:
        creds_dict = st.secrets["gcp_service_account"]
        scope = ['https://www.googleapis.com/auth/spreadsheets']
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)
        
        sheet = client.open_by_key(SHEET_ID).sheet1
        data = sheet.get_all_values()
        
        header_row = 1
        for i, row in enumerate(data):
            if row and ('Disciplina' in row or 'Código' in row):
                header_row = i
                break
        
        headers = data[header_row]
        cod_col = 1
        
        linha_por_codigo = {}
        for i in range(header_row + 1, len(data)):
            row = data[i]
            if len(row) > cod_col and row[cod_col]:
                linha_por_codigo[row[cod_col]] = i + 1
        
        status_colunas = {}
        for i, col in enumerate(headers):
            if col == 'Status':
                if i > 0:
                    polo_esquerda = headers[i - 1]
                    if polo_esquerda in POLOS:
                        status_colunas[polo_esquerda] = i + 1
        
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

# --- TÍTULO (AZUL MICROSOFT) ---
st.markdown(f"""
<div style="background: #0078d4; padding: 0.8rem 2rem; border-radius: 10px; margin-bottom: 1rem;">
    <h1 style="color: white; margin: 0; font-size: 1.1rem; font-weight: 400;">📚 Gestão de Oferta de Disciplinas</h1>
    <p style="color: rgba(255,255,255,0.9); margin: 0.2rem 0 0 0; font-size: 1rem;">{CURSO_NOME} | 2º semestre / 2026</p>
</div>
""", unsafe_allow_html=True)

# --- BOTÃO SALVAR (CINZA) ---
st.markdown("""
<style>
    div.stButton > button {
        background: #e0e0e0 !important;
        color: #333333 !important;
        border-radius: 6px !important;
        padding: 0.6rem 1.5rem !important;
        font-size: 1rem !important;
        font-weight: 500 !important;
        border: none !important;
        width: 100% !important;
        transition: background 0.2s !important;
    }
    div.stButton > button:hover {
        background: #cccccc !important;
    }
    div.stButton > button:active {
        background: #b3b3b3 !important;
    }
</style>
""", unsafe_allow_html=True)

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
        <span>🔘 Clique na célula para alternar</span>
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

# --- CONSTRUIR TABELA HTML ---
html_content = '<div class="tabela-wrapper"><table class="tabela-ofertas"><thead><tr><th>Período</th><th>Código</th><th style="text-align:left">Disciplina</th><th>CH</th>'

for polo in POLOS:
    html_content += f"<th>{polo}</th>"

html_content += '<th>Ação</th></tr></thead><tbody>'

for periodo in sorted(df_filtrado['Periodo'].dropna().unique(), key=lambda x: str(x)):
    df_periodo = df_filtrado[df_filtrado['Periodo'] == periodo]
    
    html_content += f'<tr class="section-header"><td colspan="{len(POLOS)+4}"><strong>📌 PERÍODO {periodo}</strong></td></tr>'
    
    for _, row in df_periodo.iterrows():
        cod_col = 'Disciplina' if 'Disciplina' in df.columns else df.columns[1]
        nome_col = 'Nome' if 'Nome' in df.columns else df.columns[2]
        
        disciplina_cod = str(row[cod_col]).replace("'", "\\'")
        disciplina_nome = str(row[nome_col]).replace("'", "\\'")
        
        ch_col = 'Carga Horária' if 'Carga Horária' in df.columns else df.columns[3]
        ch = int(row[ch_col]) if pd.notna(row[ch_col]) else 0
        
        html_content += '<tr>'
        html_content += f'<td class="texto-centro"><span class="periodo-badge">{periodo}</span></td>'
        html_content += f'<td class="texto-centro"><span class="disciplina-code">{disciplina_cod}</span></td>'
        html_content += f'<td class="disciplina-nome">{disciplina_nome}</td>'
        html_content += f'<td class="texto-centro"><span class="carga">{ch}h</span></td>'
        
        algum_ativo = False
        for polo in POLOS:
            status = get_status(row, polo, df)
            inst = get_inst(row, polo)
            is_active = (status == 'A')
            
            if is_active:
                algum_ativo = True
                html_content += f'<td class="polo-cell" onclick="toggleOffer(\'{disciplina_cod}\', \'{polo}\', this, \'{SHEET_ID}\')"><span class="polo-ativo" data-inst="{inst}">✅ {inst}</span></td>'
            else:
                html_content += f'<td class="polo-cell" onclick="toggleOffer(\'{disciplina_cod}\', \'{polo}\', this, \'{SHEET_ID}\')"><span class="polo-inativo">❌ {polo}</span></td>'
        
        if algum_ativo:
            html_content += f'<td><button class="btn-acao" onclick="toggleAll(\'{disciplina_cod}\', \'Desativar\', \'{SHEET_ID}\')">❌ Desativar todos</button></td>'
        else:
            html_content += f'<td><button class="btn-acao btn-acao-ativar" onclick="toggleAll(\'{disciplina_cod}\', \'Ativar\', \'{SHEET_ID}\')">✅ Ativar todos</button></td>'
        
        html_content += '</tr>'
    
    html_content += f'<tr class="section-spacer"><td colspan="{len(POLOS)+4}"></td></tr>'

html_content += '</tbody></table></div>'

# --- JAVASCRIPT PARA TOGGLE E SALVAMENTO ---
html_content += f"""
<script>
function toggleOffer(disciplinaCod, polo, element, sheetId) {{
    const span = element.querySelector('span');
    const isActive = span.classList.contains('polo-ativo');
    const novoStatus = !isActive;
    const inst = span.getAttribute('data-inst') || 'UFF';
    
    if (isActive) {{
        span.className = 'polo-inativo';
        span.innerHTML = '❌ ' + polo;
    }} else {{
        span.className = 'polo-ativo';
        span.innerHTML = '✅ ' + inst;
        span.setAttribute('data-inst', inst);
    }}
    
    fetch(window.location.href, {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{
            sheet_id: sheetId,
            disciplina_cod: disciplinaCod,
            polo: polo,
            status: novoStatus
        }})
    }}).catch(error => console.error('Erro:', error));
}}

function toggleAll(disciplinaCod, acao, sheetId) {{
    alert(acao + ' todos: ' + disciplinaCod + ' (em desenvolvimento)');
}}
</script>
"""

# Renderizar
st.markdown(html_content, unsafe_allow_html=True)

# --- RODAPÉ ---
st.caption(f"🔄 Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

# --- BOTÃO VOLTAR ---
if st.button("← Voltar para lista de cursos"):
    if "estado_ofertas" in st.session_state:
        del st.session_state["estado_ofertas"]
    del st.session_state["sheet_id"]
    del st.session_state["curso_nome"]
    st.switch_page("app.py")