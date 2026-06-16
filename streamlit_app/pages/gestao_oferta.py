def salvar_tudo():
    st.write("=== DEBUG: Iniciando salvamento em lote ===")
    
    try:
        creds_dict = st.secrets["gcp_service_account"]
        scope = ['https://www.googleapis.com/auth/spreadsheets']
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)
        
        sheet = client.open_by_key(SHEET_ID).sheet1
        st.write(f"✅ Planilha aberta: {sheet.title}")
        
        # Mostrar primeiras linhas para debug
        data = sheet.get_all_values()
        st.write(f"📋 Total de linhas na planilha: {len(data)}")
        
        # Preparar lista de atualizações em lote
        batch_updates = []
        total_alteracoes = 0
        
        for _, row in df.iterrows():
            cod = row['Disciplina']
            st.write(f"🔍 Buscando disciplina: {cod}")
            
            # Tentar encontrar a célula com o código da disciplina
            try:
                celula_codigo = sheet.find(cod)
                if celula_codigo:
                    linha = celula_codigo.row
                    st.write(f"   ✅ Disciplina {cod} encontrada na linha {linha}")
                    
                    for polo in POLOS:
                        status_atual = st.session_state.estado_ofertas.get(f"{cod}_{polo}", False)
                        status_original = get_status(row, polo, df) == 'A'
                        
                        if status_atual != status_original:
                            total_alteracoes += 1
                            novo_valor = 'A' if status_atual else 'D'
                            
                            # Encontrar a coluna do polo
                            celula_polo = sheet.find(polo)
                            if celula_polo:
                                coluna_status = celula_polo.col + 1
                                batch_updates.append({
                                    'range': f'{gspread.utils.rowcol_to_a1(linha, coluna_status)}',
                                    'values': [[novo_valor]]
                                })
                                st.write(f"      - Polo {polo} -> {novo_valor} (linha {linha}, coluna {coluna_status})")
                            else:
                                st.warning(f"   ⚠️ Polo {polo} não encontrado!")
                else:
                    st.warning(f"   ⚠️ Disciplina {cod} NÃO encontrada na planilha!")
            except Exception as e:
                st.error(f"   ❌ Erro ao buscar {cod}: {str(e)}")
        
        if batch_updates:
            st.write(f"📊 Enviando {len(batch_updates)} atualizações em lote...")
            st.write(f"📊 Primeiras 5 atualizações: {batch_updates[:5]}")
            
            try:
                sheet.batch_update(batch_updates)
                st.success("✅ Lote enviado com sucesso!")
            except Exception as e:
                st.error(f"❌ Erro no batch_update: {str(e)}")
                return False
        else:
            st.write("📊 Nenhuma alteração para salvar.")
            return True
        
        st.cache_data.clear()
        st.write("=== DEBUG: Salvamento concluído ===")
        return True
    except Exception as e:
        st.error(f"❌ Erro geral: {str(e)}")
        return False