# app.py
import streamlit as st

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Gestão de Ofertas - CEDERJ",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --- CSS PERSONALIZADO ---
st.markdown("""
<style>
    /* Esconder elementos padrão do Streamlit */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    .stAppDeployButton {display: none;}
    
    /* Reset de margens */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 2rem;
    }
    
    /* Grid com gap maior entre os cards */
    .st-key-grid-container {
        gap: 1.5rem !important;
    }
    
    /* Cards clicáveis */
    .card-container {
        background-color: white;
        border-radius: 12px;
        padding: 1.2rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        transition: transform 0.2s, box-shadow 0.2s;
        cursor: pointer;
        height: 100%;
        border: 1px solid #e5e7eb;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .card-container:hover {
        transform: translateY(-4px);
        box-shadow: 0 4px 16px rgba(0,0,0,0.15);
    }
    .card-title {
        font-size: 1rem;
        font-weight: 600;
        color: #1a3a5c;
        margin-bottom: 0.25rem;
        line-height: 1.3;
    }
    .card-subtitle {
        font-size: 0.8rem;
        color: #4a627a;
        margin-bottom: 0.75rem;
    }
    .card-badge {
        display: inline-block;
        background-color: #e0e7ff;
        color: #1e3a8a;
        padding: 0.2rem 0.6rem;
        border-radius: 20px;
        font-size: 0.65rem;
        font-weight: 500;
        align-self: flex-start;
    }
    
    /* Ajuste para as colunas terem espaçamento igual */
    .stColumn {
        padding: 0 0.5rem !important;
    }
    
    /* Container do grid */
    .grid-container {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1.5rem;
        margin-top: 1rem;
    }
    
    /* Responsivo: 2 colunas em telas menores */
    @media (max-width: 768px) {
        .grid-container {
            grid-template-columns: repeat(2, 1fr);
            gap: 1rem;
        }
        .card-title {
            font-size: 0.9rem;
        }
    }
    
    /* Responsivo: 1 coluna em celular */
    @media (max-width: 480px) {
        .grid-container {
            grid-template-columns: 1fr;
        }
    }
</style>

<script>
function abrirCurso(sheetId, cursoNome) {
    // Navegar via query params
    const url = new URL(window.location.href);
    url.searchParams.set('sheet_id', sheetId);
    url.searchParams.set('curso_nome', cursoNome);
    window.location.href = url.toString();
}
</script>
""", unsafe_allow_html=True)

# --- TÍTULO ---
st.title("🎓 Gestão de Oferta de Disciplinas")
st.caption("Cursos de graduação a distância - Universidades consorciadas CEDERJ")

# --- LISTA DE CURSOS COMPLETA (MATEMÁTICA UFF É O PRIMEIRO) ---
cursos = [
    # MATEMÁTICA UFF - PRIMEIRO!
    {"id": "1oyUNJmT07bUcOFYZw9XEfPmkMkbIvSs_mrRnh88zdIE", "nome": "Matemática", "instituicao": "UFF", "polos": 17},
    # Demais cursos
    {"id": "1mTD-q9WTqVIWOEnZOB1JjiZXeS4j6xujf-4vD9I98ks", "nome": "Administração", "instituicao": "UFF", "polos": 18},
    {"id": "1GIetae_LEYlzbHC8JoyTQNh_s50W3eGhul4U7Yn4lCA", "nome": "Ciências Biológicas", "instituicao": "UENF", "polos": 8},
    {"id": "1XxDyPDLW7eSwxIESnqsVAQQcyOc_OTjf9dWOme5MjEQ", "nome": "Ciências Biológicas", "instituicao": "UERJ", "polos": 6},
    {"id": "149OrpiWIi8VMNeCf0bKWltNMdynw3SXrhCZ9Om5bITU", "nome": "Ciências Biológicas", "instituicao": "UFRJ", "polos": 7},
    {"id": "1vSGmy7o_SDrWvUsawz1UKXUVXDXulRskl1LcX0Gvm30", "nome": "Física", "instituicao": "UFRJ", "polos": 10},
    {"id": "1qmcgaTolwAMVB0kwe5Zu-6MJ7kkLWLD6ad6xQJOWawM", "nome": "Administração", "instituicao": "UFRRJ", "polos": 18},
    {"id": "1-3uZrlXgDKh5RLzmfpnL-VdmH5u6v8RTUdrS1GdO_NQ", "nome": "Química", "instituicao": "UENF", "polos": 5},
    {"id": "1QwhTxDjUSdh7JkMabcgaLfzM8yiL8wKW2TJ_vPjJI14", "nome": "Química", "instituicao": "UFRJ", "polos": 5},
    {"id": "1CgfGjUy0o3Z57dpWPnKUp0qwWoi-Ozuw2ZqCSTW0vI4", "nome": "Licenciatura em Pedagogia", "instituicao": "UENF", "polos": 8},
    {"id": "1TqMjvbxlO9lXx51dC132s5Mwb68RfZWehBAGK_5Ha6s", "nome": "Licenciatura em Pedagogia", "instituicao": "UERJ", "polos": 14},
    {"id": "1QUOVGiOuAxZttn7D5F55CLuK06h7YQcEME6np0lR_Zk", "nome": "Licenciatura em Pedagogia", "instituicao": "UNIRIO", "polos": 12},
    {"id": "1Xd0GKLj4j1XdVymeQrKrWKmuX3FZ1khjK65MMjSaDUw", "nome": "História", "instituicao": "UNIRIO", "polos": 5},
    {"id": "1l2Zm4y8npqyWSHyleogaBSdudjJKH6c26oGz-a4vet8", "nome": "Turismo", "instituicao": "UFRRJ", "polos": 5},
    {"id": "1sZDL9ob18KSlEi21pl7ZO8x8cp5HSiEirna55NMa7iI", "nome": "Turismo", "instituicao": "UNIRIO", "polos": 5},
    {"id": "113eEUYHARt2K6AWUXLHjAxYzAhk1zM1vQYwJoC0NLgc", "nome": "Administração Pública", "instituicao": "UFF", "polos": 9},
    {"id": "1yMr7iwMTXv7Dmk1ohii58tJW46P40BxHJDlpYxO1keQ", "nome": "Letras", "instituicao": "UFF", "polos": 6},
    {"id": "1Qh3dGrOKszmxRsO1nm1L97YGlgLXTIW3dbbWKPRyBEk", "nome": "Gestão de Turismo", "instituicao": "CEFET-RJ", "polos": 7},
    {"id": "1GRIR0yuszPuOEwP1k4kVtHlOlGL2bo4Ef_87d8hyJKU", "nome": "Geografia", "instituicao": "UERJ", "polos": 11},
    {"id": "1000X6WksETcccZJIunrwmIMrbT0wzoIwRqi8ZKKl4Ms", "nome": "Segurança Pública", "instituicao": "UFF", "polos": 12},
    {"id": "1ring7lzrz7FNJwZuPi-yko5QOvd0d9g2AfT4939QkrQ", "nome": "Engenharia de Produção", "instituicao": "UFF", "polos": 5},
    {"id": "1J28novyPrlNvDBGUvi4OKEyA_JXVa_5dj-Zy1spHK84", "nome": "Ciências Contábeis", "instituicao": "UFF", "polos": 7},
    {"id": "1Yj1XBF03-p5bT3Ir0YXxohDbPK6Zy_TC4ZHAGfdxrD4", "nome": "Ciências Contábeis", "instituicao": "UFRJ", "polos": 7},
    {"id": "1R-CQLxB7Ng7-ejp1fP1VD7puDn631mNiiH7x-z9Nrmo", "nome": "Engenharia Meteorológica", "instituicao": "UENF", "polos": 1},
    {"id": "1vVmyCcQXhqZtWf_PSfUThFCf0TpOcGhBnVbBkEVRfd4", "nome": "Biblioteconomia", "instituicao": "UFF", "polos": 5},
    {"id": "1rsOpCyYcriv-eoYwWRuKKhc1rqVeFvUDbuYr3EfLOzQ", "nome": "Biblioteconomia", "instituicao": "UNIRIO", "polos": 7},
    {"id": "19Dn9fhDn5jl6tmA8cwsV5ejwLt6DRoO4m7YcvHg1QbE", "nome": "Design Gráfico", "instituicao": "IFF", "polos": 4},
    {"id": "1vtguRvG6x6Yz58pY6zMws5Ncs1q-8KcWBKNR628ZEbI", "nome": "Licenciatura em Administração", "instituicao": "UFRRJ", "polos": 8},
]

# --- FILTRO DE BUSCA ---
busca = st.text_input("🔍 Buscar curso ou instituição...", placeholder="Ex: Matemática ou UFF")

cursos_filtrados = [
    c for c in cursos 
    if busca.lower() in c["nome"].lower() or busca.lower() in c["instituicao"].lower()
]

# --- EXIBIÇÃO DOS CARDS COM GRID CSS ---
if not cursos_filtrados:
    st.info("Nenhum curso encontrado com esse termo.")
else:
    # Construir HTML do grid manualmente para melhor controle do espaçamento
    grid_html = '<div class="grid-container">'
    
    for curso in cursos_filtrados:
        card_html = f'''
        <div class="card-container" onclick="abrirCurso('{curso['id']}', '{curso['nome']} - {curso['instituicao']}')">
            <div>
                <div class="card-title">{curso['nome']}</div>
                <div class="card-subtitle">{curso['instituicao']}</div>
            </div>
            <span class="card-badge">{curso['polos']} polos</span>
        </div>
        '''
        grid_html += card_html
    
    grid_html += '</div>'
    
    st.markdown(grid_html, unsafe_allow_html=True)
    
    # Total de cursos
    st.markdown(f"<p style='text-align: center; margin-top: 2rem; color: #6b7280; font-size: 0.8rem;'>📊 Total: {len(cursos_filtrados)} oferta(s) de cursos</p>", unsafe_allow_html=True)

# --- PROCESSAR CLIQUE DO CARD (via query_params) ---
query_params = st.query_params
if "sheet_id" in query_params:
    st.session_state["sheet_id"] = query_params["sheet_id"]
    st.session_state["curso_nome"] = query_params.get("curso_nome", "Curso")
    st.switch_page("pages/gestao_oferta.py")