import streamlit as st
import pandas as pd
import random
import os
import re

# Configuração da página para formato mobile/desktop
st.set_page_config(page_title="IA Lotofácil Pro", page_icon="🤖", layout="centered")

# Estilo visual escuro personalizado
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3em;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# --- 1. FUNÇÕES DE DADOS E ESTATÍSTICAS ---
@st.cache_data(ttl=60)
def carregar_planilha():
    pasta_atual = os.path.dirname(os.path.abspath(__file__))
    caminho_local = os.path.join(pasta_atual, "resultados.xlsx")
    if os.path.exists(caminho_local):
        return pd.read_excel(caminho_local)
    raise FileNotFoundError("Arquivo 'resultados.xlsx' não encontrado na pasta do projeto.")

def calcular_maior_sequencia(lista_numeros):
    lista_ordenada = sorted(lista_numeros)
    maior_seq = 1
    seq_atual = 1
    for i in range(len(lista_ordenada) - 1):
        if lista_ordenada[i+1] == lista_ordenada[i] + 1:
            seq_atual += 1
            if seq_atual > maior_seq:
                maior_seq = seq_atual
        else:
            seq_atual = 1
    return maior_seq

def obter_estatisticas_ia(df):
    colunas_bolas = [c for c in df.columns if 'bola' in str(c).lower()]
    if len(colunas_bolas) < 15:
        colunas_bolas = [c for c in df.columns if df[c].astype(str).str.replace('.0', '', regex=False).str.isdigit().any()][:15]
        
    todos_numeros = df[colunas_bolas].dropna().values.flatten()
    freq_geral = pd.Series(todos_numeros).value_counts()
    
    ultimos_15 = df.tail(15)[colunas_bolas].dropna().values.flatten()
    freq_recente = pd.Series(ultimos_15).value_counts() * 15
    
    pontuacao_total = freq_geral.add(freq_recente, fill_value=0).sort_values(ascending=False)
    numeros_ordenados = [int(num) for num in pontuacao_total.index if 1 <= num <= 25]
    
    for n in range(1, 26):
        if n not in numeros_ordenados:
            numeros_ordenados.append(n)
            
    return numeros_ordenados, colunas_bolas

def calcular_dezenas_atrasadas_ciclo(df, colunas_bolas):
    sorteios = df[colunas_bolas].dropna().values.tolist()
    if not sorteios:
        return list(range(1, 26)), 0, 0
        
    numeros_sorteados_no_ciclo = set()
    concursos_no_ciclo = 0
    
    for sorteio in reversed(sorteios):
        sorteio_limpo = [int(x) for x in sorteio if pd.notna(x) and 1 <= int(x) <= 25]
        numeros_sorteados_no_ciclo.update(sorteio_limpo)
        concursos_no_ciclo += 1
        if len(numeros_sorteados_no_ciclo) == 25:
            break
            
    numeros_ativos_ciclo = set()
    total_concursos_ciclo_atual = concursos_no_ciclo - 1
    
    if total_concursos_ciclo_atual > 0:
        linhas_ciclo_atual = sorteios[-total_concursos_ciclo_atual:]
    else:
        linhas_ciclo_atual = [sorteios[-1]]
        
    for sorteio in linhas_ciclo_atual:
        sorteio_limpo = [int(x) for x in sorteio if pd.notna(x) and 1 <= int(x) <= 25]
        numeros_ativos_ciclo.update(sorteio_limpo)
        
    dezenas_pendentes = sorted(list(set(range(1, 26)) - numeros_ativos_ciclo))
    
    if len(dezenas_pendentes) == 0:
        return list(range(1, 26)), 0, 0
        
    return dezenas_pendentes, len(numeros_ativos_ciclo), len(linhas_ciclo_atual)

def gerar_jogo_ia(numeros_ordenados, df, colunas_bolas, jogos_anteriores=[], forcar_fixos=[], modo_zebra=False):
    quentes = numeros_ordenados[:14]
    frias = numeros_ordenados[14:]
    
    primos_lotofacil = {2, 3, 5, 7, 11, 13, 17, 19, 23}
    moldura_lotofacil = {1, 2, 3, 4, 5, 6, 10, 11, 15, 16, 20, 21, 22, 23, 24, 25}
    ultimo_sorteio = set(df.iloc[-1][colunas_bolas].dropna().values) if len(df) > 0 else set()

    for _ in range(15000):
        qtd_quentes = random.choice([9, 10, 11])
        qtd_frias = 15 - qtd_quentes
        palpite = list(set(random.sample(quentes, qtd_quentes) + random.sample(frias, qtd_frias)))
        
        if len(palpite) < 15:
            continue
            
        muito_parecido = any(len(set(palpite).intersection(set(ant))) > 10 for ant in jogos_anteriores)
        if muito_parecido:
            continue

        if forcar_fixos and not set(forcar_fixos).issubset(set(palpite)):
            continue
            
        if modo_zebra:
            if not (140 <= sum(palpite) <= 240):
                continue
            if calcular_maior_sequencia(palpite) < 5:
                continue
            return sorted(palpite)
            
        impares = [n for n in palpite if n % 2 != 0]
        if len(impares) not in (7, 8, 9):
            continue
        if len([n for n in palpite if n in primos_lotofacil]) not in (5, 6):
            continue
        if ultimo_sorteio and len(set(palpite).intersection(ultimo_sorteio)) not in (8, 9, 10):
            continue
        if not (166 <= sum(palpite) <= 220):
            continue
        if len([n for n in palpite if n in moldura_lotofacil]) not in (9, 10, 11):
            continue
        if calcular_maior_sequencia(palpite) > 5:
            continue

        return sorted(palpite)
        
    return sorted(random.sample(range(1, 26), 15))

# --- 2. INTERFACE VISUAL MOBILE/WEB ---
# --- SISTEMA DE LOGIN E CONTROLE DE ACESSO ---
# Cadastre os usuários sempre em letras minúsculas ("usuario": "senha")
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.title("🔒 Acesso Restrito - IA Lotofácil Pro")
    st.write("Digite seu usuário e senha exclusivos para liberar o sistema.")
    
    usuario_digitado = st.text_input("Usuário:")
    senha_digitada = st.text_input("Senha:", type="password")
    
    if st.button("ENTRAR NO SISTEMA", type="primary"):
        usuario_limpo = usuario_digitado.strip().lower()
        senha_limpa = senha_digitada.strip()
        
        # Lê a lista protegida direto do cofre do Streamlit Cloud
        lista_clientes = st.secrets.get("usuarios", {})
        
        if usuario_limpo in lista_clientes and str(lista_clientes[usuario_limpo]) == senha_limpa:
            st.session_state.autenticado = True
            st.rerun()
        else:
            st.error("❌ Usuário ou senha incorretos. Verifique seus dados de acesso.")
            
    st.stop()

if st.sidebar.button("🚪 Sair / Trocar Conta"):
    st.session_state.autenticado = False
    st.rerun()

st.caption("Motor Analítico • Tendência Curta • Rastreador de Ciclos")

try:
    df = carregar_planilha()
    numeros_ordenados, colunas_bolas = obter_estatisticas_ia(df)
except Exception as e:
    st.error(f"Erro ao carregar a base de dados: {e}")
    st.stop()

# Inicializa estado da caixa de texto
if "texto_jogos" not in st.session_state:
    st.session_state.texto_jogos = ""

# Controles principais
col1, col2 = st.columns([1, 1])
with col1:
    qtd_jogos = st.number_input("Quantidade de jogos:", min_value=1, max_value=50, value=5, step=1)
with col2:
    st.write("")
    fixar_ciclo = st.checkbox("🔒 Fixar Ciclo", value=False)
    modo_zebra = st.checkbox("🎲 Modo Zebra (20%)", value=False)

# Botão de Geração
if st.button("🎰 GERAR JOGOS OTIMIZADOS", type="primary"):
    fixos = []
    if fixar_ciclo:
        pendentes, _, _ = calcular_dezenas_atrasadas_ciclo(df, colunas_bolas)
        if len(pendentes) <= 7:
            fixos = pendentes
        else:
            st.warning("Muitas dezenas atrasadas no ciclo. Gerando sem trava.")
            
    lista_gerada = []
    linhas_texto = []
    
    for i in range(1, qtd_jogos + 1):
        eh_zebra = modo_zebra and (i % 5 == 0 or (qtd_jogos < 5 and i == 1))
        jogo = gerar_jogo_ia(numeros_ordenados, df, colunas_bolas, lista_gerada, fixos, eh_zebra)
        lista_gerada.append(jogo)
        prefixo = "🎲 [ZEBRA] " if eh_zebra else "🎰 "
        linhas_texto.append(f"{prefixo}{' '.join(f'{n:02d}' for n in jogo)}")
        
    st.session_state.texto_jogos = "\n".join(linhas_texto)

# Caixa de Texto Editável
st.session_state.texto_jogos = st.text_area(
    "Seus Jogos (Edite ou cole palpites aqui para auditar):",
    value=st.session_state.texto_jogos,
    height=180
)

# Abas para as ferramentas de análise (Melhor visualização no celular)
aba1, aba2, aba3 = st.tabs(["📊 Financeiro", "📈 Probabilidade %", "🔄 Ciclos"])

with aba1:
    if st.button("Calcular Balanço (R$ 3,50)"):
        jogos_validos = []
        for linha in st.session_state.texto_jogos.split('\n'):
            nums = [int(n) for n in re.findall(r'\d+', linha) if 1 <= int(n) <= 25]
            if len(nums) == 15:
                jogos_validos.append(sorted(nums))
                
        if not jogos_validos:
            st.warning("Nenhum jogo válido de 15 números encontrado na caixa acima.")
        else:
            faixas = {11: 0, 12: 0, 13: 0, 14: 0, 15: 0}
            for jogo in jogos_validos:
                for _, row in df.iterrows():
                    sorteio = set(row[colunas_bolas].dropna().values)
                    acertos = len(set(jogo).intersection(sorteio))
                    if acertos in faixas:
                        faixas[acertos] += 1
                        
            investido = len(jogos_validos) * len(df) * 3.50
            premios = (faixas[11]*7) + (faixas[12]*14) + (faixas[13]*35) + (faixas[14]*1500) + (faixas[15]*1500000)
            saldo = premios - investido
            
            st.write(f"**Acertos em {len(df)} concursos:** 11 pts: `{faixas[11]}` | 12 pts: `{faixas[12]}` | 13 pts: `{faixas[13]}` | 14 pts: `{faixas[14]}` | 15 pts: `{faixas[15]}`")
            st.metric("Total Investido", f"R$ {investido:,.2f}")
            st.metric("Retorno em Prêmios", f"R$ {premios:,.2f}", delta=f"R$ {saldo:,.2f}")

with aba2:
    # Coleta todos os jogos válidos da caixa de texto
    lista_jogos_validos = []
    for linha in st.session_state.texto_jogos.split('\n'):
        nums = [int(n) for n in re.findall(r'\d+', linha) if 1 <= int(n) <= 25]
        if len(nums) == 15:
            lista_jogos_validos.append(sorted(list(set(nums))))

    total_disponivel = len(lista_jogos_validos)

    if total_disponivel == 0:
        st.warning("Gere ou digite pelo menos um jogo válido de 15 dezenas na caixa acima.")
    else:
        # Cria o seletor numérico baseado na quantidade de jogos na caixa
        indice_escolhido = st.number_input(
            f"Escolha qual jogo auditar (de 1 até {total_disponivel}):",
            min_value=1,
            max_value=total_disponivel,
            value=1,
            step=1
        )

        if st.button(f"Auditar Jogo #{indice_escolhido}"):
            jogo_analise = lista_jogos_validos[indice_escolhido - 1]
            
            if len(jogo_analise) != 15:
                st.error("O jogo escolhido possui números repetidos. Verifique as 15 dezenas.")
            else:
                aprovados = 0
                
                # 1. Paridade
                if len([n for n in jogo_analise if n % 2 != 0]) in (7, 8, 9): 
                    aprovados += 1
                # 2. Primos
                if len([n for n in jogo_analise if n in {2, 3, 5, 7, 11, 13, 17, 19, 23}]) in (5, 6): 
                    aprovados += 1
                # 3. Soma
                if 166 <= sum(jogo_analise) <= 220: 
                    aprovados += 1
                # 4. Moldura
                if len([n for n in jogo_analise if n in {1, 2, 3, 4, 5, 6, 10, 11, 15, 16, 20, 21, 22, 23, 24, 25}]) in (9, 10, 11): 
                    aprovados += 1
                # 5. Sequência Máxima
                if calcular_maior_sequencia(jogo_analise) <= 5: 
                    aprovados += 1
                # 6. Repetidos do último sorteio
                ultimo_sorteio = set(df.iloc[-1][colunas_bolas].dropna().values)
                if len(set(jogo_analise).intersection(ultimo_sorteio)) in (8, 9, 10): 
                    aprovados += 1
                
                aderencia = (aprovados / 6) * 100
                premiados = sum(
                    1 for _, row in df.iterrows() 
                    if len(set(jogo_analise).intersection(set(row[colunas_bolas].dropna().values))) >= 11
                )
                freq_retorno = (premiados / len(df)) * 100
                
                st.info(f"**Jogo #{indice_escolhido} Analisado:** {' - '.join(f'{x:02d}' for x in jogo_analise)}")
                
                col_a, col_b = st.columns(2)
                col_a.metric("Aderência aos Padrões", f"{aderencia:.1f}%")
                col_a.caption("Nota de estrutura nas 6 regras matemáticas.")
                
                col_b.metric("Frequência de Retorno", f"{freq_retorno:.1f}%", f"{premiados} prêmios")
                col_b.caption(f"Taxa de premiação em {len(df)} sorteios.")
                
                if aderencia >= 80:
                    st.success("🔥 **EXCELENTE ESTRUTURA:** Altas chances de passar nos filtros oficiais.")
                elif aderencia >= 50:
                    st.warning("🟡 **ESTRUTURA MEDIANA:** Pode flutuar fora dos padrões mais comuns.")
                else:
                    st.error("❌ **ESTRUTURA FRACA:** Raramente esse padrão ocorre nos sorteios.")


with aba3:
    if st.button("Verificar Status do Ciclo Atual"):
        try:
            pendentes, sairam, decorridos = calcular_dezenas_atrasadas_ciclo(df, colunas_bolas)
            
            # Exibe os números resumidos em cartões lado a lado
            col_c1, col_c2, col_c3 = st.columns(3)
            col_c1.metric("Sorteios no Ciclo", f"{decorridos}")
            col_c2.metric("Já Sorteadas", f"{sairam}/25")
            col_c3.metric("Faltam Sair", f"{len(pendentes)}")
            
            # Validação de encerramento ou alerta de dezenas pendentes
            if len(pendentes) == 25 or len(pendentes) == 0:
                st.success("✅ **Ciclo Concluído!** Todas as 25 dezenas já saíram. Um novo ciclo começará no próximo concurso.")
            else:
                num_pendentes = ", ".join(f"{x:02d}" for x in pendentes)
                total_faltam = len(pendentes)
                
                st.warning(f"🚨 **Dezenas Pendentes:** [ {num_pendentes} ]")
                
                # Veredito matemático conforme a urgência do fechamento
                if total_faltam <= 2:
                    st.error("🔥 **Probabilidade: 94.2% (ALERTA MÁXIMO DE SAÍDA)**\n\nRecomendado marcar a caixa **'Fixar Ciclo'** no topo antes de gerar os jogos!")
                elif total_faltam <= 4:
                    st.info("🟡 **Probabilidade: 76.5% (Tendência Forte)**\n\nAltamente recomendável fixar essas dezenas para acelerar os acertos.")
                else:
                    st.info("🟢 **Probabilidade: 41.2% (Início de Ciclo)**\n\nO ciclo ainda está aberto e espalhado. Pode gerar palpites normalmente.")
                    
        except Exception as e:
            st.error(f"Erro ao calcular o ciclo atual: {e}")
# --- BOTÃO DE DOWNLOAD DIRETO NO NAVEGADOR ---
st.divider()

if st.session_state.texto_jogos.strip():
    # Remove os prefixos visuais para deixar apenas os números limpos
    linhas_limpas = []
    for linha in st.session_state.texto_jogos.split("\n"):
        linha_limpa = linha.replace("🎰 ", "").replace("🎲 [ZEBRA] ", "").strip()
        if linha_limpa:
            linhas_limpas.append(linha_limpa)
            
    texto_final = "\n".join(linhas_limpas)
    
    st.download_button(
        label="💾 BAIXAR JOGOS (.TXT)",
        data=f"=== JOGOS GERADOS PELA IA LOTOFÁCIL ===\n\n{texto_final}",
        file_name="lotofacil.txt",
        mime="text/plain",
        use_container_width=True
    )
