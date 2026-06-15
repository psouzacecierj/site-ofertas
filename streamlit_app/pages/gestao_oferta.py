# pages/gestao_oferta.py
import streamlit as st
import pandas as pd
from datetime import datetime
import streamlit.components.v1 as components

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

# --- RECUPERAR DADOS DO CURSO ---
if "sheet_id" not in st.session_state:
    st.warning("⚠️ Nenhum curso selecionado. Volte para a página inicial.")
    st.stop()

SHEET_ID = st.session_state["sheet_id"]
CURSO_NOME = st.session_state.get("curso_nome", "Curso")

# --- FUNÇÃO PARA CARREGAR DADOS (MAIS ROBUSTA) ---
@st.cache_data(ttl=60)
def carregar_dados(sheet_id):
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    
    # Múltiplas tentativas com diferentes configurações
    tentativas = [
        {"header": None, "skiprows": None},      # Sem header, sem pular
        {"header": 0, "skiprows": None},         # Primeira linha como header
        {"header": 1, "skiprows": None},         # Segunda linha como header
        {"header": 0, "skiprows": 1},            # Pular linha 1, header na linha 2
        {"header": None, "skiprows": 2},         # Pular 2 linhas
    ]
    
    for tentativa in tentativas:
        try:
            df = pd.read_csv(
                url, 
                header=tentativa["header"],
                skiprows=tentativa["skiprows"]
            )
            
            # Verificar se encontrou colunas esperadas
            colunas = df.columns.tolist()
            
            # PROCURAR COLUNA DE PERÍODO (várias variações)
            col_periodo = None
            for col in colunas:
                col_lower = str(col).lower().strip()
                if col_lower in ['periodo', 'período', 'period', 'per']:
                    col_periodo = col
                    break
            
            if col_periodo:
                df.rename(columns={col_periodo: 'Periodo'}, inplace=True)
                return df
            
            # PROCURAR COLUNA DE DISCIPLINA (para confirmar que é uma planilha válida)
            for col in colunas:
                col_lower = str(col).lower().strip()
                if col_lower in ['disciplina', 'código', 'codigo']:
                    return df
                    
        except Exception as e:
            continue
    
    st.error(f"❌ Erro ao carregar planilha. Verifique se o link é público e a estrutura está correta.")
    return None

# --- FUNÇÃO PARA DETECTAR POLOS ---
def detectar_polos(df):
    colunas = df.columns.tolist()
    polos = []
    
    # Lista de polos conhecidos
    polos_conhecidos = ['ARE', 'BJE', 'CAN', 'CGR', 'ITA', 'ITO', 'MAC', 'NIG', 
                        'PAR', 'PIR', 'RBO', 'RES', 'SAQ', 'SFI', 'SFR', 'SPE', 'VRE',
                        'BRO', 'MAG', 'NFR', 'PET', 'ROC', 'SGO']
    
    for col in colunas:
        col_str = str(col).strip()
        # Verifica se é um código de polo (3 letras maiúsculas ou está na lista)
        if (len(col_str) == 3 and col_str.isupper()) or col_str in polos_conhecidos:
            if col_str not in polos and col_str not in ['PER', 'DIS', 'NOM', 'CAR', 'EAD']:
                polos.append(col_str)
    
    return polos

# --- FUNÇÃO PARA OBTER STATUS DE UM POLO ---
def get_status(row, polo, df):
    # Verifica se o polo existe na linha
    if polo in row.index:
        # Tenta encontrar a coluna de status (geralmente à direita)
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

# --- GARANTIR QUE A COLUNA 'Periodo' EXISTE ---
if 'Periodo' not in df.columns:
    # Tentar encontrar uma coluna que parece ser período
    for col in df.columns:
        col_lower = str(col).lower().strip()
        if col_lower in ['periodo', 'período', 'period', 'per']:
            df.rename(columns={col: 'Periodo'}, inplace=True)
            break
        # Verificar se os valores parecem períodos (01, 02, etc.)
        valores = df[col].dropna().astype(str).head(5)
        if all(v in ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10'] for v in valores):
            df.rename(columns={col: 'Periodo'}, inplace=True)
            break

if 'Periodo' not in df.columns:
    st.error("❌ Não foi possível encontrar a coluna 'Periodo' na planilha.")
    st.write("Colunas encontradas:", df.columns.tolist())
    st.stop()

# --- IDENTIFICAR POLOS ---
POLOS = detectar_polos(df)

if not POLOS:
    st.warning("⚠️ Nenhum polo detectado. Verifique a estrutura da planilha.")
    st.write("Colunas encontradas:", df.columns.tolist())

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
    # Garantir que a coluna Periodo existe antes de usar
    if 'Periodo' in df.columns:
        periodos = sorted([p for p in df['Periodo'].dropna().unique() if str(p) != 'nan'], key=lambda x: str(x))
        periodo_sel = st.selectbox("Período", ["Todos"] + list(periodos), key="periodo_select")
    else:
        periodo_sel = "Todos"
with col_f3:
    status_sel = st.selectbox("Status", ["Todos", "Com oferta", "Sem oferta"], key="status_select")
with col_f4:
    if st.button("🗑️ Limpar", use_container_width=True, key="limpar_filtros"):
        st.session_state.busca_input = ""
        st.session_state.periodo_select = "Todos"
        st.session_state.status_select = "Todos"
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
    # Verificar se as colunas existem
    if 'Disciplina' in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado['Disciplina'].astype(str).str.lower().str.contains(busca_lower, na=False)]
    elif 'Código' in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado['Código'].astype(str).str.lower().str.contains(busca_lower, na=False)]

if periodo_sel != "Todos" and 'Periodo' in df_filtrado.columns:
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

# --- CONSTRUIR TABELA HTML ---
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
        position: sticky;
        top: 0;
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
        font-family: 'Courier New', monospace;
        font-size: 11px;
        color: #6b7280;
        white-space: nowrap;
    }
    .disciplina-nome {
        font-weight: 500;
        color: #111827;
        text-align: left;
        max-width: 300px;
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
    }
    .polo-ativo {
        background: #dcfce7;
        color: #166534;
        padding: 4px 8px;
        border-radius: 16px;
        font-size: 10px;
        font-weight: 600;
        white-space: nowrap;
        display: inline-block;
    }
    .polo-inativo {
        background: #f3f4f6;
        color: #9ca3af;
        padding: 4px 8px;
        border-radius: 16px;
        font-size: 10px;
        white-space: nowrap;
        display: inline-block;
    }
    .btn-acao {
        background: #fee2e2;
        color: #991b1b;
        border: none;
        padding: 4px 8px;
        border-radius: 20px;
        font-size: 10px;
        font-weight: 600;
        cursor: pointer;
        white-space: nowrap;
        width: 100%;
    }
    .btn-acao-ativar {
        background: #dcfce7;
        color: #166534;
    }
    .section-header td {
        background: #f1f5f9;
        padding: 8px 12px;
        font-size: 11px;
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
function toggleOffer(disciplinaCod, polo, element) {
    const span = element.querySelector('span');
    const isActive = span.classList.contains('polo-ativo');
    const inst = span.getAttribute('data-inst') || 'UFF';
    
    if (isActive) {
        span.className = 'polo-inativo';
        span.innerHTML = '—';
        span.removeAttribute('data-inst');
    } else {
        span.className = 'polo-ativo';
        span.innerHTML = '✓ ' + inst;
        span.setAttribute('data-inst', inst);
    }
}

function toggleAll(disciplinaCod, acao) {
    alert(acao + ' todos: ' + disciplinaCod);
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
        
        # Cabeçalho do período
        html_content += f'<tr class="section-header"><td colspan="{len(POLOS)+4}"><strong>📌 PERÍODO {periodo}</strong></td></tr>'
        
        for _, row in df_periodo.iterrows():
            # Determinar colunas de código e nome
            cod_col = 'Disciplina' if 'Disciplina' in df.columns else 'Código' if 'Código' in df.columns else df.columns[1]
            nome_col = 'Nome' if 'Nome' in df.columns else df.columns[2]
            
            disciplina_cod = str(row[cod_col]).replace("'", "\\'")
            disciplina_nome = str(row[nome_col]).replace("'", "\\'")
            
            # Carga horária
            ch_col = 'Carga Horária' if 'Carga Horária' in df.columns else df.columns[3]
            ch = int(row[ch_col]) if pd.notna(row[ch_col]) else 0
            
            html_content += '<tr>'
            html_content += f'<td class="texto-centro"><span class="periodo-badge">{periodo}</span></td>'
            html_content += f'<td class="texto-centro"><span class="disciplina-code">{disciplina_cod}</span></td>'
            html_content += f'<td class="disciplina-nome">{disciplina_nome}</td>'
            html_content += f'<td class="texto-centro"><span class="carga">{ch}h</span></td>'
            
            # Polos
            algum_ativo = False
            for polo in POLOS:
                status = get_status(row, polo, df)
                inst = get_inst(row, polo)
                is_active = (status == 'A')
                
                if is_active:
                    algum_ativo = True
                    html_content += f'''
                    <td class="polo-cell" onclick="toggleOffer('{disciplina_cod}', '{polo}', this)">
                        <span class="polo-ativo" data-inst="{inst}">✓ {inst}</span>
                    </td>
                    '''
                else:
                    html_content += f'''
                    <td class="polo-cell" onclick="toggleOffer('{disciplina_cod}', '{polo}', this)">
                        <span class="polo-inativo">—</span>
                    </td>
                    '''
            
            # Botão de ação
            if algum_ativo:
                html_content += f'<td><button class="btn-acao" onclick="toggleAll(\'{disciplina_cod}\', \'Desativar\')">❌ Desativar todos</button></td>'
            else:
                html_content += f'<td><button class="btn-acao btn-acao-ativar" onclick="toggleAll(\'{disciplina_cod}\', \'Ativar\')">✅ Ativar todos</button></td>'
            
            html_content += '</tr>'
        
        # Espaçador
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