# pages/gestao_oferta.py
import streamlit as st
import pandas as pd
from datetime import datetime
import streamlit.components.v1 as components
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
</style>
""", unsafe_allow_html=True)

# --- PROCESSAR SALVAMENTO VIA QUERY PARAMS ---
query_params = st.query_params

if "save" in query_params:
    sheet_id = query_params.get("sheet_id")
    disciplina_cod = query_params.get("disciplina_cod")
    polo = query_params.get("polo")
    novo_status = query_params.get("status") == "true"
    
    try:
        creds_dict = st.secrets["gcp_service_account"]
        scope = ['https://www.googleapis.com/auth/spreadsheets']
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)
        
        sheet = client.open_by_key(sheet_id).sheet1
        data = sheet.get_all_values()
        
        # Encontrar cabeçalhos
        header_row = 1
        for i, row in enumerate(data):
            if row and ('Disciplina' in row or 'Código' in row):
                header_row = i
                break
        
        headers = data[header_row]
        
        # Encontrar coluna do polo
        polo_col = None
        for i, col in enumerate(headers):
            if col == polo:
                polo_col = i
                break
        
        if polo_col is not None:
            status_col = polo_col + 1
            cod_col = 1
            
            # Encontrar linha da disciplina
            disciplina_row = None
            for i in range(header_row + 1, len(data)):
                if len(data[i]) > cod_col and data[i][cod_col] == disciplina_cod:
                    disciplina_row = i
                    break
            
            if disciplina_row is not None:
                novo_valor = 'A' if novo_status else 'D'
                sheet.update_cell(disciplina_row + 1, status_col + 1, novo_valor)
                st.cache_data.clear()
    except Exception as e:
        pass
    
    st.query_params.clear()
    st.rerun()

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

# --- TÍTULO ---
st.markdown(f"""
<div style="background: #2d6a4f; padding: 0.8rem 2rem; border-radius: 10px; margin-bottom: 1rem;">
    <h1 style="color: white; margin: 0; font-size: 1.1rem;">📚 Gestão de Oferta de Disciplinas</h1>
    <p style="color: rgba(255,255,255,0.8); margin: 0.2rem 0 0 0; font-size: 0.7rem;">{CURSO_NOME} | 2º semestre / 2026</p>
</div>
""", unsafe_allow_html=True)

# --- FILTROS ---
col_f1, col_f2, col_f3, col_f4, col_f5 = st.columns([2, 1, 1, 1, 1])
with col_f1:
    busca = st.text_input("🔍 Buscar disciplina", placeholder="Nome ou código...", key="busca_input")
with col_f2:
    periodos = sorted([p for p in df['Periodo'].dropna().unique() if str(p) != 'nan'], key=lambda x: str(x))
    periodo_sel = st.selectbox("Período", ["Todos"] + list(periodos), key="periodo_select")
with col_f3:
    status_sel = st.selectbox("Status", ["Todos", "Com oferta", "Sem oferta"], key="status_select")
with col_f4:
    if st.button("🗑️ Limpar", use_container_width=True, key="limpar_filtros"):
        for key in ['busca_input', 'periodo_select', 'status_select']:
            if key in st.session_state:
                st.session_state[key] = "" if key == 'busca_input' else "Todos"
        st.rerun()
with col_f5:
    if st.button("🔄 Resetar", use_container_width=True, key="reset_ofertas"):
        st.cache_data.clear()
        st.rerun()

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
    busca_lower = busca.lower()
    if 'Disciplina' in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado['Disciplina'].astype(str).str.lower().str.contains(busca_lower, na=False)]

if periodo_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado['Periodo'].astype(str) == str(periodo_sel)]

if status_sel != "Todos" and POLOS:
    mascara = []
    for _, row in df_filtrado.iterrows():
        tem_oferta = any(get_status(row, polo, df) == 'A' for polo in POLOS)
        mascara.append(tem_oferta)
    
    if status_sel == "Com oferta":
        df_filtrado = df_filtrado[mascara]
    else:
        df_filtrado = df_filtrado[[not m for m in mascara]]

# --- CONSTRUIR TABELA HTML COM REDIRECIONAMENTO ---
html_content = """
<style>
    .tabela-wrapper {
        overflow-x: auto;
        border-radius: 10px;
        border: 1px solid #e5e7eb;
        background: white;
    }
    .tabela-ofertas {
        width: 100%;
        border-collapse: collapse;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-size: 12px;
        min-width: 800px;
    }
    .tabela-ofertas th {
        background: #2d6a4f;
        color: white;
        padding: 10px 6px;
        text-align: center;
        font-weight: 600;
        font-size: 10px;
        white-space: nowrap;
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
    .carga {
        font-size: 11px;
        color: #9ca3af;
    }
    .polo-cell {
        text-align: center;
        cursor: pointer;
    }
    .polo-ativo {
        background: #dcfce7;
        color: #166534;
        padding: 4px 8px;
        border-radius: 16px;
        font-size: 10px;
        font-weight: 600;
        display: inline-block;
    }
    .polo-inativo {
        background: #f3f4f6;
        color: #9ca3af;
        padding: 4px 8px;
        border-radius: 16px;
        font-size: 10px;
        display: inline-block;
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
    }
</style>

<script>
function toggleOffer(disciplinaCod, polo, element, sheetId) {
    const span = element.querySelector('span');
    const isActive = span.classList.contains('polo-ativo');
    const novoStatus = !isActive;
    const inst = span.getAttribute('data-inst') || 'UFF';
    
    // Mudar visual imediatamente
    if (isActive) {
        span.className = 'polo-inativo';
        span.innerHTML = '—';
        span.removeAttribute('data-inst');
    } else {
        span.className = 'polo-ativo';
        span.innerHTML = '✓ ' + inst;
        span.setAttribute('data-inst', inst);
    }
    
    // Redirecionar para salvar (recarrega a página, mas o visual já mudou)
    const url = window.location.href.split('?')[0];
    window.location.href = url + '?save=true&sheet_id=' + sheetId + '&disciplina_cod=' + encodeURIComponent(disciplinaCod) + '&polo=' + polo + '&status=' + novoStatus;
}

function toggleAll(disciplinaCod, acao, sheetId) {
    const novoStatus = (acao === 'Ativar');
    alert(acao + ' todos: ' + disciplinaCod + ' (recarregando para salvar)');
    const url = window.location.href.split('?')[0];
    window.location.href = url + '?save_all=true&sheet_id=' + sheetId + '&disciplina_cod=' + encodeURIComponent(disciplinaCod) + '&status=' + novoStatus;
}
</script>

<div class="tabela-wrapper">
<table class="tabela-ofertas">
    <thead>
        <tr>
            <th>Período</th>
            <th>Código</th>
            <th style="text-align:left">Disciplina</th>
            <th>CH</th>
"""

for polo in POLOS:
    html_content += f"<th>{polo}</th>"

html_content += """
            <th>Ação</th>
        </tr>
    </thead>
    <tbody>
"""

# Agrupar por período
if 'Periodo' in df_filtrado.columns:
    periodos_unicos = sorted(df_filtrado['Periodo'].dropna().unique(), key=lambda x: str(x))
    
    for periodo in periodos_unicos:
        df_periodo = df_filtrado[df_filtrado['Periodo'] == periodo]
        
        html_content += f'<tr class="section-header"><td colspan="{len(POLOS)+4}"><strong>📌 PERÍODO {periodo}</strong><td></td>'
        
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
                    html_content += f'''
                    <td class="polo-cell" onclick="toggleOffer('{disciplina_cod}', '{polo}', this, '{SHEET_ID}')" data-disciplina="{disciplina_cod}" data-polo="{polo}">
                        <span class="polo-ativo" data-inst="{inst}">✓ {inst}</span>
                    </td>
                    '''
                else:
                    html_content += f'''
                    <td class="polo-cell" onclick="toggleOffer('{disciplina_cod}', '{polo}', this, '{SHEET_ID}')" data-disciplina="{disciplina_cod}" data-polo="{polo}">
                        <span class="polo-inativo">—</span>
                    </td>
                    '''
            
            if algum_ativo:
                html_content += f'<td><button class="btn-acao" onclick="toggleAll(\'{disciplina_cod}\', \'Desativar\', \'{SHEET_ID}\')">❌ Desativar todos</button></td>'
            else:
                html_content += f'<td><button class="btn-acao btn-acao-ativar" onclick="toggleAll(\'{disciplina_cod}\', \'Ativar\', \'{SHEET_ID}\')">✅ Ativar todos</button></td>'
            
            html_content += '</tr>'
        
        html_content += f'<tr class="section-spacer"><td colspan="{len(POLOS)+4}"></td></tr>'

html_content += """
    </tbody>
</table>
</div>
"""

# Renderizar o HTML
if html_content:
    components.html(html_content, height=600, scrolling=True)
else:
    st.info("Nenhuma disciplina encontrada com os filtros selecionados.")

# --- RODAPÉ ---
st.divider()
st.caption(f"🔄 Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

# --- BOTÃO VOLTAR ---
if st.button("← Voltar para lista de cursos"):
    del st.session_state["sheet_id"]
    del st.session_state["curso_nome"]
    st.switch_page("app.py")