# pages/gestao_oferta.py
import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Gestão de Oferta", layout="wide")

# --- CSS PERSONALIZADO ---
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    .stAppDeployButton {display: none;}
    footer {visibility: hidden;}
    .stActionButton {display: none;}
    
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
        max-width: 100%;
    }
    
    /* Estilos da tabela */
    .tabela-ofertas {
        width: 100%;
        border-collapse: collapse;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-size: 12px;
        background: white;
        border-radius: 10px;
        overflow-x: auto;
        display: block;
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
        padding: 4px 10px;
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
    .texto-esquerda {
        text-align: left;
    }
    .texto-centro {
        text-align: center;
    }
</style>

<script>
function toggleOffer(disciplinaCod, polo, element) {
    const span = element.querySelector('span');
    const isActive = span.classList.contains('polo-ativo');
    const inst = span.getAttribute('data-inst') || 'UFRRJ';
    
    if (isActive) {
        span.className = 'polo-inativo';
        span.innerHTML = '—';
        span.removeAttribute('data-inst');
        console.log('Desativado:', disciplinaCod, polo);
    } else {
        span.className = 'polo-ativo';
        span.innerHTML = '✓ ' + inst;
        span.setAttribute('data-inst', inst);
        console.log('Ativado:', disciplinaCod, polo);
    }
}

function toggleAll(disciplinaCod, acao) {
    console.log(acao + ' todos:', disciplinaCod);
    alert(acao + ' todos: ' + disciplinaCod);
}
</script>
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
    try:
        df = pd.read_csv(url)
        if len(df.columns) < 8:
            df = pd.read_csv(url, header=1)
        return df
    except Exception as e:
        st.error(f"Erro ao carregar planilha: {str(e)}")
        return None

# --- FUNÇÃO PARA DETECTAR POLOS ---
def detectar_polos(df):
    colunas = df.columns.tolist()
    polos = []
    for col in colunas:
        if col and len(col) == 3 and col.isupper() and col not in ['PER', 'DIS', 'NOM', 'CAR', 'EAD']:
            polos.append(col)
    return polos

# --- FUNÇÃO PARA OBTER STATUS DE UM POLO ---
def get_status(row, polo, df):
    for col in df.columns:
        if col == polo:
            polo_idx = df.columns.get_loc(col)
            if polo_idx + 1 < len(df.columns):
                status_col = df.columns[polo_idx + 1]
                if status_col in row.index:
                    val = row[status_col]
                    if pd.notna(val):
                        return str(val).strip()
            break
    return 'D'

# --- FUNÇÃO PARA OBTER INSTITUIÇÃO DE UM POLO ---
def get_inst(row, polo):
    if polo in row.index and pd.notna(row[polo]):
        return str(row[polo]).strip()
    return '—'

# --- CARREGAR DADOS ---
df = carregar_dados(SHEET_ID)
if df is None or df.empty:
    st.stop()

POLOS = detectar_polos(df)

# --- TÍTULO ---
st.markdown(f"""
<div style="background: #2d6a4f; padding: 1.2rem 2rem; border-radius: 10px; margin-bottom: 1.5rem;">
    <h1 style="color: white; margin: 0; font-size: 1.3rem;">📚 Gestão de Oferta de Disciplinas</h1>
    <p style="color: rgba(255,255,255,0.8); margin: 0.25rem 0 0 0; font-size: 0.8rem;">{CURSO_NOME} | 2º semestre / 2026</p>
</div>
""", unsafe_allow_html=True)

# --- ESTATÍSTICAS ---
total_disciplinas = len(df)
total_polos = len(POLOS)

ofertas_ativas = 0
for _, row in df.iterrows():
    for polo in POLOS:
        status = get_status(row, polo, df)
        if status == 'A':
            ofertas_ativas += 1

total_possivel = total_disciplinas * total_polos

col1, col2, col3, col4 = st.columns(4)

col1.markdown(f"""
<div style="background: white; padding: 0.8rem; border-radius: 10px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
    <div style="font-size: 0.75rem; color: #6b7280;">Com oferta (✓)</div>
    <div style="font-size: 1.8rem; font-weight: bold; color: #2e7d32;">{ofertas_ativas}</div>
</div>
""", unsafe_allow_html=True)

col2.markdown(f"""
<div style="background: white; padding: 0.8rem; border-radius: 10px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
    <div style="font-size: 0.75rem; color: #6b7280;">Sem oferta (vazio)</div>
    <div style="font-size: 1.8rem; font-weight: bold; color: #9ca3af;">{total_possivel - ofertas_ativas}</div>
</div>
""", unsafe_allow_html=True)

col3.markdown(f"""
<div style="background: white; padding: 0.8rem; border-radius: 10px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
    <div style="font-size: 0.75rem; color: #6b7280;">Disciplinas</div>
    <div style="font-size: 1.8rem; font-weight: bold; color: #1a5276;">{total_disciplinas}</div>
</div>
""", unsafe_allow_html=True)

col4.markdown(f"""
<div style="background: white; padding: 0.8rem; border-radius: 10px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
    <div style="font-size: 0.75rem; color: #6b7280;">Polos</div>
    <div style="font-size: 1.8rem; font-weight: bold; color: #1a5276;">{total_polos}</div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# --- FILTROS ---
col_f1, col_f2, col_f3 = st.columns([2, 1, 1])
with col_f1:
    busca = st.text_input("🔍 Buscar disciplina ou código...", placeholder="Digite o nome ou código", key="busca_input")
with col_f2:
    periodos = sorted([p for p in df['Periodo'].dropna().unique() if str(p) != 'nan'], key=lambda x: str(x))
    periodo_sel = st.selectbox("Período", ["Todos"] + list(periodos), key="periodo_select")
with col_f3:
    status_sel = st.selectbox("Status", ["Todos", "Com oferta", "Sem oferta"], key="status_select")

col_b1, col_b2 = st.columns(2)
with col_b1:
    if st.button("🗑️ Limpar filtros", use_container_width=True, key="limpar_filtros"):
        st.session_state.busca_input = ""
        st.session_state.periodo_select = "Todos"
        st.session_state.status_select = "Todos"
        st.rerun()
with col_b2:
    if st.button("🔄 Resetar ofertas (original)", use_container_width=True, key="reset_ofertas"):
        st.cache_data.clear()
        st.rerun()

# --- FILTRAR DADOS ---
df_filtrado = df.copy()

if busca:
    df_filtrado = df_filtrado[
        df_filtrado['Disciplina'].astype(str).str.contains(busca, case=False, na=False) |
        df_filtrado['Nome'].astype(str).str.contains(busca, case=False, na=False)
    ]

if periodo_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado['Periodo'].astype(str) == str(periodo_sel)]

if status_sel != "Todos":
    mascara = []
    for _, row in df_filtrado.iterrows():
        tem_oferta = any(get_status(row, polo, df) == 'A' for polo in POLOS)
        mascara.append(tem_oferta)
    
    if status_sel == "Com oferta":
        df_filtrado = df_filtrado[mascara]
    else:
        df_filtrado = df_filtrado[[not m for m in mascara]]

# --- LEGENDA ---
st.markdown("""
<div style="display: flex; gap: 20px; margin-bottom: 1rem; flex-wrap: wrap;">
    <div style="display: flex; align-items: center; gap: 6px;">
        <span style="background: #dcfce7; color: #166534; padding: 2px 10px; border-radius: 4px; font-size: 11px; font-weight: 500;">✓ UFRRJ</span>
        <span style="font-size: 12px; color: #6b7280;">Oferta ativa (verde)</span>
    </div>
    <div style="display: flex; align-items: center; gap: 6px;">
        <span style="background: #f3f4f6; color: #9ca3af; padding: 2px 10px; border-radius: 4px; font-size: 11px;">—</span>
        <span style="font-size: 12px; color: #6b7280;">Sem oferta (vazio/branco)</span>
    </div>
    <div style="display: flex; align-items: center; gap: 6px;">
        <span style="background: #eef2ff; padding: 2px 10px; border-radius: 4px; font-size: 11px;">🔘</span>
        <span style="font-size: 12px; color: #6b7280;">Clique na célula para alternar</span>
    </div>
</div>
""", unsafe_allow_html=True)

# --- CONSTRUIR TABELA HTML ---
html_table = '<div style="overflow-x: auto;"><table class="tabela-ofertas">'
html_table += '<thead><tr>'
html_table += '<th>Período</th><th>Código</th><th style="text-align:left">Disciplina</th><th>CH</th>'

for polo in POLOS:
    html_table += f'<th>{polo}</th>'

html_table += '<th style="width:100px">Ação</th>'
html_table += '</thead><tbody>'

# Agrupar por período
periodos_unicos = sorted(df_filtrado['Periodo'].dropna().unique(), key=lambda x: str(x))

for periodo in periodos_unicos:
    df_periodo = df_filtrado[df_filtrado['Periodo'] == periodo]
    
    # Cabeçalho do período
    html_table += f'<tr class="section-header"><td colspan="{len(POLOS)+4}"><strong>📌 PERÍODO {periodo}</strong></td></tr>'
    
    for _, row in df_periodo.iterrows():
        disciplina_cod = str(row['Disciplina']).replace("'", "\\'")
        disciplina_nome = str(row['Nome']).replace("'", "\\'")
        ch = int(row['Carga Horária']) if pd.notna(row['Carga Horária']) else 0
        
        html_table += '<tr>'
        html_table += f'<td class="texto-centro"><span class="periodo-badge">{periodo}</span></td>'
        html_table += f'<td class="texto-centro"><span class="disciplina-code">{disciplina_cod}</span></td>'
        html_table += f'<td class="disciplina-nome">{disciplina_nome}</td>'
        html_table += f'<td class="texto-centro"><span class="carga">{ch}h</span></td>'
        
        # Polos
        algum_ativo = False
        for polo in POLOS:
            status = get_status(row, polo, df)
            inst = get_inst(row, polo)
            is_active = (status == 'A')
            
            if is_active:
                algum_ativo = True
                html_table += f'''
                <td class="polo-cell" onclick="toggleOffer('{disciplina_cod}', '{polo}', this)">
                    <span class="polo-ativo" data-inst="{inst}">✓ {inst}</span>
                </td>
                '''
            else:
                html_table += f'''
                <td class="polo-cell" onclick="toggleOffer('{disciplina_cod}', '{polo}', this)">
                    <span class="polo-inativo">—</span>
                </td>
                '''
        
        # Botão de ação
        if algum_ativo:
            html_table += f'<td><button class="btn-acao" onclick="toggleAll(\'{disciplina_cod}\', \'Desativar\')">❌ Desativar todos</button></td>'
        else:
            html_table += f'<td><button class="btn-acao btn-acao-ativar" onclick="toggleAll(\'{disciplina_cod}\', \'Ativar\')">✅ Ativar todos</button></td>'
        
        html_table += '</tr>'
    
    # Espaçador
    html_table += f'<tr class="section-spacer"><td colspan="{len(POLOS)+4}"></td></tr>'

html_table += '</tbody></table></div>'

# Exibir tabela
st.markdown(html_table, unsafe_allow_html=True)

# --- RODAPÉ ---
st.divider()
st.caption(f"🔄 Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

# --- BOTÃO VOLTAR ---
if st.button("← Voltar para lista de cursos", use_container_width=False):
    del st.session_state["sheet_id"]
    del st.session_state["curso_nome"]
    st.switch_page("app.py")