"""
CineTracker - Tracker de Filmes
Projeto Final - Algoritmos e Programação (Fatec Bebedouro)

Recursos novos usados além do que foi visto em aula:
- Interface gráfica com CustomTkinter
- Consumo de API (OMDb) com requests
- Armazenamento em arquivo JSON
- Imagens com Pillow
- Gráficos com matplotlib
- Threads + fila para a busca não travar a janela
"""
import os
import json
import os
import queue
import threading
from io import BytesIO

import customtkinter as ctk
import requests
from PIL import Image
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# ---------------------------------------------------------------
# Configurações gerais
# ---------------------------------------------------------------
# Configure a variável de ambiente OMDB_API_KEY antes de executar.
API_KEY = os.environ.get("OMDB_API_KEY")
URL_API = "https://www.omdbapi.com/"
ARQUIVO_JSON = "biblioteca.json"
PASTA_POSTERS = "posters"

NOME_ALUNO = "Projeto Final • Fatec Bebedouro"

STATUS_LISTA = ["Quero ver", "Assistindo", "Assistido"]
ICONES_STATUS = {"Quero ver": "📌", "Assistindo": "▶️", "Assistido": "✅"}
CORES_STATUS = {"Quero ver": "#6b7280", "Assistindo": "#2563eb", "Assistido": "#16a34a"}

COR_FUNDO = "#14151a"
COR_PAINEL = "#1c1d24"
COR_CARD = "#20222b"
COR_HOVER = "#2b2d38"
COR_ATIVO = "#3b6cf6"

COLUNAS = 4  # cards por linha

GENEROS_PT = {
    "Action": "Ação", "Adventure": "Aventura", "Animation": "Animação",
    "Biography": "Biografia", "Comedy": "Comédia", "Crime": "Crime",
    "Documentary": "Documentário", "Drama": "Drama", "Family": "Família",
    "Fantasy": "Fantasia", "History": "História", "Horror": "Terror",
    "Music": "Música", "Musical": "Musical", "Mystery": "Mistério",
    "Romance": "Romance", "Sci-Fi": "Ficção Científica", "Sport": "Esporte",
    "Thriller": "Suspense", "War": "Guerra", "Western": "Faroeste",
}

ERROS_PT = {
    "Movie not found!": "Filme não encontrado.",
    "Invalid API key!": "Chave da API inválida. Ative a chave pelo link do e-mail da OMDb.",
    "Too many results.": "Muitos resultados. Digite um nome mais específico.",
    "Request limit reached!": "Limite diário da API atingido.",
}

# ---------------------------------------------------------------
# Estado do programa
# ---------------------------------------------------------------
filtro_status = None        # None = mostra todos os filmes
pagina_atual = "biblioteca"
cache_imagens = {}          # caminho do pôster -> CTkImage (evita reabrir arquivos)
fila_ui = queue.Queue()     # threads colocam aqui o que deve rodar na janela principal

grade_ref = None            # referências da página da biblioteca (para redesenhar)
entrada_local_ref = None
titulo_ref = None


# ---------------------------------------------------------------
# Funções de dados (JSON)
# ---------------------------------------------------------------
def ler_lista():
    """Lê o arquivo JSON e devolve a lista de filmes (lista de dicionários)."""
    if not os.path.exists(ARQUIVO_JSON):
        return []
    with open(ARQUIVO_JSON, "r", encoding="utf-8") as arquivo:
        try:
            dados = json.load(arquivo)
        except json.JSONDecodeError:
            return []
    return dados if isinstance(dados, list) else []


def salvar_lista(lista):
    """Grava a lista de filmes no arquivo JSON."""
    with open(ARQUIVO_JSON, "w", encoding="utf-8") as arquivo:
        json.dump(lista, arquivo, ensure_ascii=False, indent=4)


def duracao_para_minutos(texto):
    """Converte '148 min' em 148. Se não der, devolve 0."""
    try:
        return int(str(texto).split()[0])
    except (ValueError, IndexError):
        return 0


def traduzir_generos(texto):
    """Traduz 'Action, Drama' para 'Ação, Drama'."""
    partes = [g.strip() for g in texto.split(",") if g.strip()]
    return ", ".join(GENEROS_PT.get(g, g) for g in partes)


def encurtar(texto, limite=34):
    return texto if len(texto) <= limite else texto[: limite - 1] + "…"


def contar_por_status(lista):
    contagem = {status: 0 for status in STATUS_LISTA}
    for filme in lista:
        status = filme.get("status", "Quero ver")
        contagem[status] = contagem.get(status, 0) + 1
    return contagem


# ---------------------------------------------------------------
# Funções da API e de imagens
# ---------------------------------------------------------------
def buscar_filmes_api(termo):
    """Busca vários filmes pelo nome. Devolve (lista_de_resultados, mensagem_de_erro)."""
    if not API_KEY:
        return [], "Configure a variável de ambiente OMDB_API_KEY para usar a busca."
    resposta = requests.get(
        URL_API,
        params={"s": termo, "type": "movie", "apikey": API_KEY},
        timeout=10,
    ).json()
    if resposta.get("Response") == "True":
        return resposta.get("Search", []), None
    erro = resposta.get("Error", "Nenhum filme encontrado.")
    return [], ERROS_PT.get(erro, erro)


def buscar_detalhes_api(imdb_id):
    """Busca os detalhes completos de um filme (duração, gênero, sinopse...)."""
    return requests.get(
        URL_API,
        params={"i": imdb_id, "plot": "short", "apikey": API_KEY},
        timeout=10,
    ).json()


def baixar_imagem_pil(url):
    """Baixa uma imagem da internet. Devolve None se não houver pôster."""
    if not url or url == "N/A":
        return None
    try:
        dados = requests.get(url, timeout=10).content
        return Image.open(BytesIO(dados)).convert("RGB")
    except Exception:
        return None


def criar_ctk_image(pil_img, tamanho=(155, 225)):
    """Transforma uma imagem do Pillow em imagem do CustomTkinter."""
    if pil_img is None:
        pil_img = Image.new("RGB", tamanho, "#2b2d38")  # quadrado cinza se não há pôster
    return ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=tamanho)


def carregar_poster_local(caminho):
    """Carrega o pôster salvo na pasta 'posters' (com cache)."""
    if caminho in cache_imagens:
        return cache_imagens[caminho]
    pil = None
    if caminho and os.path.exists(caminho):
        try:
            pil = Image.open(caminho).convert("RGB")
        except Exception:
            pil = None
    imagem = criar_ctk_image(pil)
    cache_imagens[caminho] = imagem
    return imagem


def adicionar_filme(imdb_id, pil_poster):
    """Salva o filme na biblioteca. Devolve (deu_certo, mensagem)."""
    lista = ler_lista()
    if any(f.get("imdb_id") == imdb_id for f in lista):
        return False, "Esse filme já está na biblioteca."
    if not API_KEY:
        return False, "Configure a variável de ambiente OMDB_API_KEY para adicionar filmes."

    try:
        detalhes = buscar_detalhes_api(imdb_id)
    except (requests.exceptions.RequestException, ValueError):
        return False, "Erro de conexão com a Internet."

    if detalhes.get("Response") != "True":
        erro = detalhes.get("Error", "Erro ao buscar detalhes.")
        return False, ERROS_PT.get(erro, erro)

    if pil_poster is None:
        pil_poster = baixar_imagem_pil(detalhes.get("Poster"))

    caminho = ""
    if pil_poster is not None:
        os.makedirs(PASTA_POSTERS, exist_ok=True)
        caminho = os.path.join(PASTA_POSTERS, f"{imdb_id}.jpg")
        pil_poster.save(caminho)

    filme = {
        "imdb_id": imdb_id,
        "titulo": detalhes.get("Title", "Sem título"),
        "ano": detalhes.get("Year", "----"),
        "genero": detalhes.get("Genre", ""),
        "duracao_min": duracao_para_minutos(detalhes.get("Runtime", "")),
        "nota_imdb": detalhes.get("imdbRating", "N/A"),
        "sinopse": detalhes.get("Plot", ""),
        "poster": caminho,
        "status": "Quero ver",
        "nota_pessoal": 0,
    }
    lista.append(filme)
    salvar_lista(lista)
    return True, f"'{filme['titulo']}' adicionado à biblioteca!"


# ---------------------------------------------------------------
# Ações sobre filmes da biblioteca
# ---------------------------------------------------------------
def agendar_atualizacao():
    """Redesenha a grade um instante depois (evita destruir o botão que acabou de ser clicado)."""
    app.after(150, atualizar_grade)


def mudar_status(imdb_id, novo_status):
    lista = ler_lista()
    for filme in lista:
        if filme.get("imdb_id") == imdb_id:
            filme["status"] = novo_status
    salvar_lista(lista)
    agendar_atualizacao()


def dar_nota(imdb_id, nota):
    """Define a nota pessoal (1 a 5). Clicar na mesma estrela de novo zera a nota."""
    lista = ler_lista()
    for filme in lista:
        if filme.get("imdb_id") == imdb_id:
            filme["nota_pessoal"] = 0 if filme.get("nota_pessoal", 0) == nota else nota
    salvar_lista(lista)
    agendar_atualizacao()


def remover_filme(imdb_id):
    lista = ler_lista()
    restantes = []
    for filme in lista:
        if filme.get("imdb_id") == imdb_id:
            caminho = filme.get("poster", "")
            cache_imagens.pop(caminho, None)
            if caminho and os.path.exists(caminho):
                os.remove(caminho)
        else:
            restantes.append(filme)
    salvar_lista(restantes)
    agendar_atualizacao()


def mostrar_sinopse(filme):
    """Abre uma janelinha com a sinopse do filme."""
    janela = ctk.CTkToplevel(app)
    janela.title(filme.get("titulo", "Filme"))
    janela.geometry("420x300")
    janela.attributes("-topmost", True)
    ctk.CTkLabel(janela, text=filme.get("titulo", ""), font=("Arial", 18, "bold"), wraplength=380).pack(pady=(20, 5))
    info = f"{filme.get('ano', '')} • {traduzir_generos(filme.get('genero', ''))}"
    ctk.CTkLabel(janela, text=info, text_color="gray").pack()
    sinopse = filme.get("sinopse") or "Sem sinopse disponível."
    ctk.CTkLabel(janela, text=sinopse, wraplength=380, justify="left").pack(padx=20, pady=15)


# ---------------------------------------------------------------
# Janela principal
# ---------------------------------------------------------------
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.geometry("1100x680")
app.minsize(960, 600)
app.title("CineTracker - Tracker de Filmes (Projeto Final Fatec)")
app.configure(fg_color=COR_FUNDO)


def limpar_conteudo():
    for widget in area_conteudo.winfo_children():
        widget.destroy()


# ---------------------------------------------------------------
# Página: Biblioteca
# ---------------------------------------------------------------
def criar_card_filme(pai, filme):
    imdb_id = filme.get("imdb_id")
    card = ctk.CTkFrame(pai, width=175, corner_radius=12, fg_color=COR_CARD)

    poster = carregar_poster_local(filme.get("poster", ""))
    ctk.CTkLabel(card, image=poster, text="").pack(padx=10, pady=(10, 6))

    ctk.CTkLabel(
        card, text=encurtar(filme.get("titulo", "")), font=("Arial", 14, "bold"),
        wraplength=155, justify="left", anchor="w",
    ).pack(padx=10, anchor="w")

    # Status (menu de seleção colorido)
    status = filme.get("status", "Quero ver")
    cor = CORES_STATUS.get(status, "#6b7280")
    ctk.CTkOptionMenu(
        card, values=STATUS_LISTA, width=155, height=24,
        fg_color=cor, button_color=cor, button_hover_color=cor,
        command=lambda novo, i=imdb_id: mudar_status(i, novo),
    ).pack(padx=10, pady=(6, 2))
    # Mostra o status atual no menu
    card.winfo_children()[-1].set(status)

    # Duração e nota do IMDb
    duracao = filme.get("duracao_min", 0)
    texto_duracao = f"🕒 {duracao} min" if duracao else "🕒 --"
    ctk.CTkLabel(card, text=f"{texto_duracao}  •  IMDb ⭐ {filme.get('nota_imdb', 'N/A')}",
                 font=("Arial", 12), text_color="gray").pack(padx=10, anchor="w")

    # Estrelas (nota pessoal)
    linha_estrelas = ctk.CTkFrame(card, fg_color="transparent")
    linha_estrelas.pack(padx=6, pady=(2, 0), anchor="w")
    nota = filme.get("nota_pessoal", 0)
    for n in range(1, 6):
        ctk.CTkButton(
            linha_estrelas, text="★", width=26, height=26, font=("Arial", 18),
            fg_color="transparent", hover_color=COR_HOVER,
            text_color="#facc15" if n <= nota else "#4b5563",
            command=lambda n=n, i=imdb_id: dar_nota(i, n),
        ).pack(side="left")

    # Botões de sinopse e remover
    linha_botoes = ctk.CTkFrame(card, fg_color="transparent")
    linha_botoes.pack(padx=10, pady=(4, 10), fill="x")
    ctk.CTkButton(
        linha_botoes, text="📝 Sinopse", width=80, height=26, fg_color=COR_HOVER,
        command=lambda f=filme: mostrar_sinopse(f),
    ).pack(side="left")
    ctk.CTkButton(
        linha_botoes, text="🗑", width=40, height=26, fg_color="#7f1d1d", hover_color="#991b1b",
        command=lambda i=imdb_id: remover_filme(i),
    ).pack(side="right")

    return card


def desenhar_grade(grade, texto_busca):
    """Desenha os cards da biblioteca aplicando o filtro de status e a busca."""
    for widget in grade.winfo_children():
        widget.destroy()

    lista = ler_lista()
    visiveis = []
    for filme in lista:
        passa_status = filtro_status is None or filme.get("status") == filtro_status
        passa_busca = texto_busca in filme.get("titulo", "").lower()
        if passa_status and passa_busca:
            visiveis.append(filme)

    if not visiveis:
        ctk.CTkLabel(
            grade, text="Nenhum filme por aqui ainda.\nUse 'Adicionar via API' para buscar filmes.",
            font=("Arial", 15), text_color="gray",
        ).grid(row=0, column=0, padx=40, pady=60)
        return

    for indice, filme in enumerate(visiveis):
        linha, coluna = divmod(indice, COLUNAS)
        criar_card_filme(grade, filme).grid(row=linha, column=coluna, padx=8, pady=8, sticky="n")


def texto_titulo_biblioteca():
    total = len(ler_lista())
    palavra = "FILME" if total == 1 else "FILMES"
    texto = f"MINHA BIBLIOTECA ({total} {palavra})"
    if filtro_status:
        texto += f" • {filtro_status}"
    return texto


def atualizar_grade():
    """Redesenha a grade da biblioteca sem recarregar a página inteira."""
    atualizar_contadores()
    if pagina_atual != "biblioteca" or grade_ref is None:
        return
    if not grade_ref.winfo_exists():
        return
    titulo_ref.configure(text=texto_titulo_biblioteca())
    desenhar_grade(grade_ref, entrada_local_ref.get().strip().lower())


def mostrar_biblioteca():
    global grade_ref, entrada_local_ref, titulo_ref
    limpar_conteudo()

    topo = ctk.CTkFrame(area_conteudo, fg_color="transparent")
    topo.pack(fill="x", padx=20, pady=(15, 5))

    titulo_ref = ctk.CTkLabel(topo, text=texto_titulo_biblioteca(), font=("Arial", 22, "bold"))
    titulo_ref.pack(side="left")

    ctk.CTkButton(
        topo, text="➕ Adicionar via API", height=34, font=("Arial", 13, "bold"),
        command=lambda: mostrar_pagina("busca"),
    ).pack(side="right")

    entrada_local_ref = ctk.CTkEntry(topo, placeholder_text="🔍 Buscar na biblioteca...", width=220, height=34)
    entrada_local_ref.pack(side="right", padx=10)

    grade_ref = ctk.CTkScrollableFrame(area_conteudo, fg_color="transparent")
    grade_ref.pack(fill="both", expand=True, padx=10, pady=10)

    entrada_local_ref.bind("<KeyRelease>", lambda event: atualizar_grade())
    desenhar_grade(grade_ref, "")


# ---------------------------------------------------------------
# Página: Buscar na API
# ---------------------------------------------------------------
def mostrar_busca():
    limpar_conteudo()

    ctk.CTkLabel(area_conteudo, text="BUSCAR NA API OMDb", font=("Arial", 22, "bold")).pack(
        anchor="w", padx=20, pady=(15, 5)
    )

    barra = ctk.CTkFrame(area_conteudo, fg_color="transparent")
    barra.pack(fill="x", padx=20, pady=5)

    entrada = ctk.CTkEntry(barra, placeholder_text="Ex: Oppenheimer, Interstellar...", width=380, height=34)
    entrada.pack(side="left", padx=(0, 10))
    botao_buscar = ctk.CTkButton(barra, text="🔍 Buscar", width=100, height=34)
    botao_buscar.pack(side="left")

    msg = ctk.CTkLabel(
        area_conteudo, text="Digite o nome do filme (a OMDb funciona melhor com títulos em inglês).",
        text_color="gray", anchor="w",
    )
    msg.pack(fill="x", padx=20, pady=(5, 0))

    resultados = ctk.CTkScrollableFrame(area_conteudo, fg_color="transparent")
    resultados.pack(fill="both", expand=True, padx=10, pady=10)

    def ao_adicionar(filme_api, pil, botao):
        ok, mensagem = adicionar_filme(filme_api["imdbID"], pil)
        msg.configure(
            text=("✅ " if ok else "⚠️ ") + mensagem,
            text_color="#4ade80" if ok else "#fbbf24",
        )
        if ok or "já está" in mensagem:
            botao.configure(text="✔ Na biblioteca", state="disabled")
        atualizar_contadores()

    def exibir_resultados(filmes, imagens, erro):
        if not resultados.winfo_exists():  # o usuário mudou de página
            return
        botao_buscar.configure(state="normal")
        for widget in resultados.winfo_children():
            widget.destroy()

        if erro:
            msg.configure(text=erro, text_color="#f87171")
            return

        msg.configure(text=f"{len(filmes)} resultado(s) encontrado(s).", text_color="gray")
        ids_salvos = {f.get("imdb_id") for f in ler_lista()}

        for indice, (filme_api, pil) in enumerate(zip(filmes, imagens)):
            linha, coluna = divmod(indice, COLUNAS)
            card = ctk.CTkFrame(resultados, width=175, corner_radius=12, fg_color=COR_CARD)
            card.grid(row=linha, column=coluna, padx=8, pady=8, sticky="n")

            ctk.CTkLabel(card, image=criar_ctk_image(pil), text="").pack(padx=10, pady=(10, 6))
            ctk.CTkLabel(
                card, text=encurtar(filme_api.get("Title", "")), font=("Arial", 14, "bold"),
                wraplength=155, justify="left", anchor="w",
            ).pack(padx=10, anchor="w")
            ctk.CTkLabel(card, text=filme_api.get("Year", ""), text_color="gray").pack(padx=10, anchor="w")

            ja_salvo = filme_api.get("imdbID") in ids_salvos
            botao = ctk.CTkButton(
                card, width=155, height=28,
                text="✔ Na biblioteca" if ja_salvo else "➕ Adicionar",
                state="disabled" if ja_salvo else "normal",
                fg_color="#28a745", hover_color="#218838",
            )
            botao.configure(command=lambda fa=filme_api, p=pil, b=botao: ao_adicionar(fa, p, b))
            botao.pack(padx=10, pady=(6, 10))

    def buscar(event=None):
        termo = entrada.get().strip()
        if not termo:
            msg.configure(text="Digite o nome de um filme.", text_color="#fbbf24")
            return
        msg.configure(text="Buscando...", text_color="gray")
        botao_buscar.configure(state="disabled")

        def tarefa():
            # Roda em outra thread para a janela não travar durante os downloads
            try:
                filmes, erro = buscar_filmes_api(termo)
                imagens = [baixar_imagem_pil(f.get("Poster")) for f in filmes]
                fila_ui.put(lambda: exibir_resultados(filmes, imagens, erro))
            except (requests.exceptions.RequestException, ValueError):
                fila_ui.put(lambda: exibir_resultados([], [], "Erro de conexão com a Internet."))

        threading.Thread(target=tarefa, daemon=True).start()

    botao_buscar.configure(command=buscar)
    entrada.bind("<Return>", buscar)
    entrada.focus()


# ---------------------------------------------------------------
# Página: Estatísticas
# ---------------------------------------------------------------
def criar_cartao_numero(pai, titulo, valor):
    cartao = ctk.CTkFrame(pai, corner_radius=12, fg_color=COR_CARD)
    ctk.CTkLabel(cartao, text=str(valor), font=("Arial", 26, "bold")).pack(padx=25, pady=(12, 0))
    ctk.CTkLabel(cartao, text=titulo, text_color="gray").pack(padx=25, pady=(0, 12))
    return cartao


def mostrar_estatisticas():
    limpar_conteudo()
    ctk.CTkLabel(area_conteudo, text="ESTATÍSTICAS", font=("Arial", 22, "bold")).pack(
        anchor="w", padx=20, pady=(15, 5)
    )

    lista = ler_lista()
    if not lista:
        ctk.CTkLabel(
            area_conteudo, text="Adicione filmes à biblioteca para ver as estatísticas.",
            font=("Arial", 15), text_color="gray",
        ).pack(pady=80)
        return

    # --- Números principais ---
    assistidos = [f for f in lista if f.get("status") == "Assistido"]
    minutos = sum(f.get("duracao_min", 0) for f in assistidos)
    notas = [f["nota_pessoal"] for f in lista if f.get("nota_pessoal", 0) > 0]
    media = sum(notas) / len(notas) if notas else 0

    linha = ctk.CTkFrame(area_conteudo, fg_color="transparent")
    linha.pack(fill="x", padx=12, pady=10)
    criar_cartao_numero(linha, "Filmes na biblioteca", len(lista)).pack(side="left", padx=8)
    criar_cartao_numero(linha, "Assistidos", len(assistidos)).pack(side="left", padx=8)
    criar_cartao_numero(linha, "Horas assistidas", f"{minutos / 60:.1f} h").pack(side="left", padx=8)
    criar_cartao_numero(linha, "Sua nota média", f"{media:.1f} ★" if notas else "--").pack(side="left", padx=8)

    # --- Gráfico de filmes por gênero ---
    contagem = {}
    for filme in lista:
        for genero in traduzir_generos(filme.get("genero", "")).split(", "):
            if genero and genero != "N/A":
                contagem[genero] = contagem.get(genero, 0) + 1
    ordenado = sorted(contagem.items(), key=lambda item: item[1], reverse=True)[:8]

    quadro = ctk.CTkFrame(area_conteudo, corner_radius=12, fg_color=COR_PAINEL)
    quadro.pack(fill="both", expand=True, padx=20, pady=10)

    if not ordenado:
        ctk.CTkLabel(quadro, text="Sem dados de gênero para mostrar.", text_color="gray").pack(pady=40)
        return

    figura = Figure(figsize=(7, 3.6), dpi=100, facecolor=COR_PAINEL)
    eixo = figura.add_subplot(111)
    eixo.set_facecolor(COR_PAINEL)
    eixo.bar([g for g, _ in ordenado], [q for _, q in ordenado], color="#3b82f6")
    eixo.set_title("Filmes por gênero", color="white")
    eixo.tick_params(colors="white")
    eixo.tick_params(axis="x", rotation=30)
    eixo.yaxis.set_major_locator(MaxNLocator(integer=True))
    for borda in eixo.spines.values():
        borda.set_color("#4b5563")
    figura.tight_layout()

    canvas = FigureCanvasTkAgg(figura, master=quadro)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)


# ---------------------------------------------------------------
# Navegação
# ---------------------------------------------------------------
def atualizar_contadores():
    lista = ler_lista()
    contagem = contar_por_status(lista)
    botoes_categoria[None].configure(text=f"🎞️  Todos ({len(lista)})")
    for status in STATUS_LISTA:
        botoes_categoria[status].configure(text=f"{ICONES_STATUS[status]}  {status} ({contagem[status]})")


def atualizar_menu():
    for chave, botao in botoes_menu.items():
        botao.configure(fg_color=COR_ATIVO if chave == pagina_atual else "transparent")
    for status, botao in botoes_categoria.items():
        ativo = pagina_atual == "biblioteca" and status == filtro_status
        botao.configure(fg_color=COR_HOVER if ativo else "transparent")
    atualizar_contadores()


def mostrar_pagina(nome):
    global pagina_atual
    pagina_atual = nome
    atualizar_menu()
    if nome == "biblioteca":
        mostrar_biblioteca()
    elif nome == "busca":
        mostrar_busca()
    else:
        mostrar_estatisticas()


def navegar(nome):
    """Clique no menu lateral: a biblioteca volta a mostrar todos os filmes."""
    global filtro_status
    if nome == "biblioteca":
        filtro_status = None
    mostrar_pagina(nome)


def definir_filtro(status):
    global filtro_status
    filtro_status = status
    mostrar_pagina("biblioteca")


def verificar_fila():
    """Executa na janela principal o que as threads colocaram na fila."""
    try:
        while True:
            funcao = fila_ui.get_nowait()
            funcao()
    except queue.Empty:
        pass
    app.after(100, verificar_fila)


# ---------------------------------------------------------------
# Construção da interface (cabeçalho, rodapé, menu lateral, conteúdo)
# ---------------------------------------------------------------
header = ctk.CTkFrame(app, height=60, corner_radius=0, fg_color=COR_PAINEL)
header.pack(side="top", fill="x")
header.pack_propagate(False)

bloco_titulo = ctk.CTkFrame(header, fg_color="transparent")
bloco_titulo.pack(side="left", padx=20)
ctk.CTkLabel(bloco_titulo, text="🎬 CINETRACKER", font=("Arial", 20, "bold")).pack(anchor="w")
ctk.CTkLabel(bloco_titulo, text="FATEC Bebedouro • Algoritmos e Programação",
             font=("Arial", 11), text_color="gray").pack(anchor="w")
ctk.CTkLabel(header, text=NOME_ALUNO, font=("Arial", 14)).pack(side="right", padx=20)

rodape = ctk.CTkLabel(
    app, text="🟢 Conectado à API OMDb • Dados salvos em biblioteca.json • Fatec Bebedouro",
    anchor="w", height=26, font=("Arial", 11), text_color="gray",
)
rodape.pack(side="bottom", fill="x", padx=14)

sidebar = ctk.CTkFrame(app, width=230, corner_radius=16, fg_color=COR_PAINEL)
sidebar.pack(side="left", fill="y", padx=(12, 0), pady=12)
sidebar.pack_propagate(False)

botoes_menu = {}
itens_menu = [
    ("biblioteca", "📚  Minha Biblioteca"),
    ("busca", "🔎  Buscar na API OMDb"),
    ("estatisticas", "📊  Estatísticas"),
]
for chave, texto in itens_menu:
    botao = ctk.CTkButton(
        sidebar, text=texto, anchor="w", height=38, font=("Arial", 14),
        fg_color="transparent", hover_color=COR_HOVER,
        command=lambda c=chave: navegar(c),
    )
    botao.pack(fill="x", padx=12, pady=(14 if chave == "biblioteca" else 3, 3))
    botoes_menu[chave] = botao

ctk.CTkLabel(sidebar, text="Categorias", font=("Arial", 14, "bold")).pack(anchor="w", padx=18, pady=(25, 6))

botoes_categoria = {}
for status in [None] + STATUS_LISTA:
    botao = ctk.CTkButton(
        sidebar, text="", anchor="w", height=34, font=("Arial", 13),
        fg_color="transparent", hover_color=COR_HOVER,
        command=lambda s=status: definir_filtro(s),
    )
    botao.pack(fill="x", padx=12, pady=2)
    botoes_categoria[status] = botao

area_conteudo = ctk.CTkFrame(app, corner_radius=16, fg_color=COR_FUNDO)
area_conteudo.pack(side="left", fill="both", expand=True, padx=12, pady=12)

# ---------------------------------------------------------------
# Início do programa
# ---------------------------------------------------------------
mostrar_pagina("biblioteca")
verificar_fila()
app.mainloop()