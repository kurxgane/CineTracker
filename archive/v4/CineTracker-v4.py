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
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "libs"))
import json
import os
import queue
import threading
from io import BytesIO
from tkinter import font as tkfont

import customtkinter as ctk
import requests
from PIL import Image, ImageDraw, ImageOps
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# ---------------------------------------------------------------
# Configurações gerais
# ---------------------------------------------------------------
# Configure a variável de ambiente OMDB_API_KEY antes de executar.
API_KEY = os.environ.get("OMDB_API_KEY", "")
URL_API = "https://www.omdbapi.com/"
ARQUIVO_JSON = "biblioteca.json"
PASTA_POSTERS = "posters"

NOME_ALUNO = "Gustavo Armando da Silva"  # troque pelo seu nome completo
CURSO_ALUNO = "Big Data"

STATUS_LISTA = ["Quero ver", "Assistindo", "Assistido"]

# ---------------------------------------------------------------
# Identidade visual: "sala escura" com luz de projetor (dourado)
# ---------------------------------------------------------------
COR_FUNDO = "#0c0c10"           # área principal
COR_SUPERFICIE = "#121218"      # barra superior, menu lateral, rodapé
COR_CARD = "#181821"            # cards e painéis
COR_CARD_HOVER = "#20202b"      # hover e campos
COR_BORDA = "#272733"           # linhas e contornos
COR_TEXTO = "#ece9e1"           # branco quente
COR_TEXTO_SUAVE = "#a09eac"
COR_TEXTO_FRACO = "#6c6b79"
COR_DESTAQUE = "#e9b44c"        # dourado: ação principal, estrelas, item ativo
COR_DESTAQUE_HOVER = "#f4c766"
COR_SOBRE_DESTAQUE = "#1b1405"  # texto sobre o dourado
COR_ESTRELA_VAZIA = "#4b4b5a"

CORES_STATUS = {"Quero ver": "#8b93ff", "Assistindo": "#2ec4b6", "Assistido": "#5fd68a"}

# ---------------------------------------------------------------
# Escala de espaçamento (8-Point Grid) e dimensões da estrutura
# ---------------------------------------------------------------
# Margens, paddings e alturas da estrutura seguem múltiplos de 8 px (e meio passo de 4 px
# nos intervalos entre cards). Tamanhos de fonte e dimensões com justificativa funcional
# ficam fora da escala.
ESP_4 = 4
ESP_8 = 8
ESP_16 = 16
ESP_24 = 24
ESP_32 = 32
ESP_40 = 40

JANELA_INICIAL = "1152x720"
LARGURA_MINIMA = 960
ALTURA_MINIMA = 600

ALTURA_CABECALHO = 56
ALTURA_RODAPE = 24
LARGURA_SIDEBAR = 208
ALTURA_ITEM_MENU = 40
ALTURA_CONTROLE = 40            # campos e botões do topo das páginas
ALTURA_MENSAGEM = 24            # faixa fixa da mensagem de status da busca
ALTURA_TITULO_CARD = 36         # 2 linhas de título (função: todos os cards com a mesma altura)

# Grade de cards (colunas adaptáveis à largura da janela)
COLUNAS_MINIMAS = 4
COLUNAS_MAXIMAS = 12
LARGURA_CARD_ALVO = 216         # largura desejada de cada card; define quantas colunas cabem
LARGURA_POSTER_MINIMA = 96

ALTURA_SIDEBAR_COM_PROGRESSO = 360  # abaixo disso o cartão de progresso some para não cortar o menu
LARGURA_POSTER_DUAS_ETIQUETAS = 128  # abaixo disso a nota do IMDb sai do pôster e vai para a linha de informações
OPCOES_CARTAO_PROGRESSO = {"side": "bottom", "fill": "x", "padx": ESP_16, "pady": ESP_16}

# Janela inicial adaptada à tela (em pixels lógicos, já considerando a escala do Windows)
RESERVA_HORIZONTAL = 32         # folga lateral
RESERVA_VERTICAL = 120          # barra de título + barra de tarefas

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
cache_imagens = {}          # caminho do pôster -> (tamanho, CTkImage) (evita reabrir arquivos)
fila_ui = queue.Queue()     # threads colocam aqui o que deve rodar na janela principal

grade_ref = None            # referências da página da biblioteca (para redesenhar)
entrada_local_ref = None
subtitulo_ref = None
chips_ref = {}              # status (ou None) -> botão de filtro da biblioteca
layout_grade_atual = None   # (colunas, largura do pôster) usados no último desenho
resultados_ref = None       # referências da página de busca
cartoes_busca = []
job_reajuste = None         # agendamento do redesenho ao redimensionar a janela


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


def criar_ctk_image(pil_img, tamanho=(160, 240)):
    """Transforma uma imagem do Pillow em imagem do CustomTkinter (recorta no formato do pôster
    e arredonda os cantos). Sem pôster, usa um quadrado escuro."""
    escala = 2  # desenha com o dobro da resolução para ficar nítido
    alvo = (tamanho[0] * escala, tamanho[1] * escala)
    if pil_img is None:
        base = Image.new("RGB", alvo, COR_CARD_HOVER)
    else:
        base = ImageOps.fit(pil_img.convert("RGB"), alvo, Image.LANCZOS)
    mascara = Image.new("L", alvo, 0)
    ImageDraw.Draw(mascara).rounded_rectangle(
        (0, 0, alvo[0] - 1, alvo[1] - 1), radius=ESP_8 * escala, fill=255
    )
    base = base.convert("RGBA")
    base.putalpha(mascara)
    return ctk.CTkImage(light_image=base, dark_image=base, size=tamanho)


def carregar_poster_local(caminho, tamanho=(160, 240)):
    """Carrega o pôster salvo na pasta 'posters' (com cache do último tamanho usado)."""
    if caminho in cache_imagens and cache_imagens[caminho][0] == tamanho:
        return cache_imagens[caminho][1]
    pil = None
    if caminho and os.path.exists(caminho):
        try:
            pil = Image.open(caminho).convert("RGB")
        except Exception:
            pil = None
    imagem = criar_ctk_image(pil, tamanho)
    cache_imagens[caminho] = (tamanho, imagem)
    return imagem


def adicionar_filme(imdb_id, pil_poster):
    """Salva o filme na biblioteca. Devolve (deu_certo, mensagem)."""
    lista = ler_lista()
    if any(f.get("imdb_id") == imdb_id for f in lista):
        return False, "Esse filme já está na biblioteca."

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


# ---------------------------------------------------------------
# Janela principal
# ---------------------------------------------------------------
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()


def escolher_fonte(preferidas, padrao):
    """Devolve a primeira fonte da lista que existe neste computador."""
    instaladas = set(tkfont.families(app))
    for nome in preferidas:
        if nome in instaladas:
            return nome
    return padrao


FAMILIA_TEXTO = escolher_fonte(["Segoe UI", "Helvetica Neue", "Inter", "Roboto"], "Arial")
FAMILIA_TITULO = escolher_fonte(["Georgia", "Cambria", "Palatino Linotype", "Times New Roman"], FAMILIA_TEXTO)


def fonte(tamanho, peso="normal", titulo=False):
    """Fonte do app: serifada nos títulos (ar de cartaz) e sem serifa no restante."""
    return ((FAMILIA_TITULO if titulo else FAMILIA_TEXTO), tamanho, peso)


def escala_widget(widget):
    """Fator de escala do Windows aplicado ao widget (1.0 = 100%)."""
    try:
        return widget._get_widget_scaling()
    except AttributeError:
        return 1.0


def ajustar_janela_inicial():
    """Usa 1152x720, mas nunca maior que a área útil da tela (considera a escala do Windows)."""
    try:
        escala = app._get_window_scaling()
    except AttributeError:
        escala = 1.0
    largura, altura = (int(valor) for valor in JANELA_INICIAL.split("x"))
    area_largura = int((app.winfo_screenwidth() - RESERVA_HORIZONTAL) / escala)
    area_altura = int((app.winfo_screenheight() - RESERVA_VERTICAL) / escala)
    largura = min(largura, area_largura)
    altura = min(altura, area_altura)
    # Em telas muito pequenas o mínimo também cede, para os controles não saírem da tela
    app.minsize(min(LARGURA_MINIMA, largura), min(ALTURA_MINIMA, altura))
    pos_x = max(0, (app.winfo_screenwidth() - round(largura * escala)) // 2)
    pos_y = max(0, (app.winfo_screenheight() - round(altura * escala)) // 2 - ESP_24)
    app.geometry(f"{largura}x{altura}+{pos_x}+{pos_y}")


ajustar_janela_inicial()
app.title("CineTracker - Tracker de Filmes (Projeto Final Fatec)")
app.configure(fg_color=COR_FUNDO)


def limpar_conteudo():
    for widget in area_conteudo.winfo_children():
        widget.destroy()


# ---------------------------------------------------------------
# Componentes reutilizáveis
# ---------------------------------------------------------------
def criar_cabecalho_pagina(titulo, subtitulo):
    """Topo padrão das páginas: título serifado + subtítulo. Devolve (quadro, rótulo do subtítulo)."""
    quadro = ctk.CTkFrame(area_conteudo, fg_color="transparent")
    quadro.pack(fill="x", padx=ESP_24, pady=(ESP_16, ESP_16))
    bloco = ctk.CTkFrame(quadro, fg_color="transparent")
    bloco.pack(side="left")
    ctk.CTkLabel(bloco, text=titulo, font=fonte(28, "bold", titulo=True), text_color=COR_TEXTO,
                 anchor="w", height=ESP_32).pack(anchor="w")
    rotulo_sub = ctk.CTkLabel(bloco, text=subtitulo, font=fonte(12), text_color=COR_TEXTO_SUAVE,
                              anchor="w", height=ESP_16)
    rotulo_sub.pack(anchor="w")
    return quadro, rotulo_sub


def criar_campo(pai, texto_dica, largura):
    return ctk.CTkEntry(
        pai, placeholder_text=texto_dica, width=largura, height=ALTURA_CONTROLE, corner_radius=ESP_24 - ESP_4,
        fg_color=COR_SUPERFICIE, border_color=COR_BORDA, border_width=1, text_color=COR_TEXTO,
        placeholder_text_color=COR_TEXTO_FRACO, font=fonte(13),
    )


def criar_botao_principal(pai, texto, comando, largura=0):
    botao = ctk.CTkButton(
        pai, text=texto, height=ALTURA_CONTROLE, corner_radius=ESP_24 - ESP_4, font=fonte(13, "bold"),
        fg_color=COR_DESTAQUE, hover_color=COR_DESTAQUE_HOVER, text_color=COR_SOBRE_DESTAQUE,
        text_color_disabled=COR_TEXTO_SUAVE, command=comando,
    )
    if largura:
        botao.configure(width=largura)
    return botao


def calcular_layout_grade(container):
    """Quantas colunas cabem e qual a largura do pôster, conforme a largura visível do container."""
    try:
        largura = container._parent_canvas.winfo_width() / escala_widget(container)
    except AttributeError:
        largura = 0
    if largura < 100:  # janela ainda não desenhada: usa a largura mínima
        largura = LARGURA_MINIMA - LARGURA_SIDEBAR - ESP_24 * 3 - ESP_16
    colunas = max(COLUNAS_MINIMAS, int((largura + ESP_8) // (LARGURA_CARD_ALVO + ESP_8)))
    largura_card = largura / colunas - ESP_8
    largura_poster = int((largura_card - 2 * ESP_8) // 8 * 8)
    return colunas, max(largura_poster, LARGURA_POSTER_MINIMA)


def configurar_colunas(container, colunas):
    for indice in range(COLUNAS_MAXIMAS):
        if indice < colunas:
            container.grid_columnconfigure(indice, weight=1, uniform="cartoes")
        else:
            container.grid_columnconfigure(indice, weight=0, uniform="")


def organizar_cartoes(cartoes, colunas):
    for indice, card in enumerate(cartoes):
        linha, coluna = divmod(indice, colunas)
        card.grid(row=linha, column=coluna, padx=ESP_4, pady=ESP_4, sticky="n")


def criar_icone_clicavel(pai, texto, comando, largura, tamanho_fonte, cor, cor_hover):
    """Ícone de texto clicável e compacto (um botão do CustomTkinter ficaria mais largo que o necessário)."""
    icone = ctk.CTkLabel(pai, text=texto, width=largura, height=24, font=fonte(tamanho_fonte), text_color=cor)
    icone.bind("<Button-1>", lambda evento: comando())
    icone.bind("<Enter>", lambda evento: icone.configure(text_color=cor_hover))
    icone.bind("<Leave>", lambda evento: icone.configure(text_color=cor))
    return icone


def criar_estado_vazio(pai, colunas, icone, titulo, texto, rotulo_botao=None, comando=None):
    pai.grid_columnconfigure(0, weight=1)
    quadro = ctk.CTkFrame(pai, fg_color="transparent")
    quadro.grid(row=0, column=0, columnspan=colunas, sticky="ew", pady=ESP_40)
    ctk.CTkLabel(quadro, text=icone, font=fonte(40)).pack()
    ctk.CTkLabel(quadro, text=titulo, font=fonte(20, "bold", titulo=True), text_color=COR_TEXTO).pack(pady=(ESP_8, 0))
    ctk.CTkLabel(quadro, text=texto, font=fonte(13), text_color=COR_TEXTO_SUAVE).pack(pady=(ESP_4, ESP_16))
    if rotulo_botao:
        criar_botao_principal(quadro, rotulo_botao, comando).pack()


# ---------------------------------------------------------------
# Janela de sinopse
# ---------------------------------------------------------------
def mostrar_sinopse(filme):
    """Abre uma janelinha com o pôster e a sinopse do filme."""
    janela = ctk.CTkToplevel(app)
    janela.title(filme.get("titulo", "Filme"))
    janela.geometry("560x320")
    janela.configure(fg_color=COR_SUPERFICIE)
    janela.attributes("-topmost", True)

    corpo = ctk.CTkFrame(janela, fg_color="transparent")
    corpo.pack(fill="both", expand=True, padx=ESP_24, pady=ESP_24)

    poster = carregar_poster_local(filme.get("poster", ""), (128, 192))
    ctk.CTkLabel(corpo, image=poster, text="").pack(side="left", anchor="n")

    texto = ctk.CTkFrame(corpo, fg_color="transparent")
    texto.pack(side="left", fill="both", expand=True, padx=(ESP_24, 0))
    ctk.CTkLabel(texto, text=filme.get("titulo", ""), font=fonte(20, "bold", titulo=True), text_color=COR_TEXTO,
                 wraplength=340, justify="left", anchor="w").pack(anchor="w")
    info = f"{filme.get('ano', '')} • {traduzir_generos(filme.get('genero', ''))}"
    ctk.CTkLabel(texto, text=info, font=fonte(12), text_color=COR_TEXTO_SUAVE, wraplength=340,
                 justify="left", anchor="w").pack(anchor="w", pady=(ESP_4, 0))
    ctk.CTkLabel(texto, text=f"IMDb ★ {filme.get('nota_imdb', 'N/A')}", font=fonte(12, "bold"),
                 text_color=COR_DESTAQUE, anchor="w").pack(anchor="w", pady=(ESP_8, ESP_16))
    sinopse = filme.get("sinopse") or "Sem sinopse disponível."
    ctk.CTkLabel(texto, text=sinopse, font=fonte(13), text_color=COR_TEXTO, wraplength=340,
                 justify="left", anchor="w").pack(anchor="w")


# ---------------------------------------------------------------
# Página: Biblioteca
# ---------------------------------------------------------------
def criar_card_filme(pai, filme, largura_poster):
    imdb_id = filme.get("imdb_id")
    altura_poster = largura_poster * 3 // 2
    card = ctk.CTkFrame(pai, width=largura_poster + 2 * ESP_8, corner_radius=ESP_16 - ESP_4,
                        fg_color=COR_CARD, border_width=1, border_color=COR_BORDA)

    # Pôster em destaque (clicar abre a sinopse), com etiquetas de status e nota do IMDb
    caminho = filme.get("poster", "")
    tem_poster = bool(caminho) and os.path.exists(caminho)
    poster = carregar_poster_local(caminho, (largura_poster, altura_poster))
    rotulo_poster = ctk.CTkLabel(card, image=poster, text="" if tem_poster else "🎬",
                                 font=fonte(32), text_color=COR_TEXTO_FRACO)
    rotulo_poster.pack(padx=ESP_8, pady=ESP_8)
    rotulo_poster.bind("<Button-1>", lambda evento, f=filme: mostrar_sinopse(f))

    status = filme.get("status", "Quero ver")
    cor = CORES_STATUS.get(status, "#6b7280")
    etiqueta_status = ctk.CTkLabel(card, text=f" {status} ", font=fonte(10, "bold"), height=20,
                                   corner_radius=ESP_8, fg_color=cor, text_color="#0b0b0f")
    etiqueta_status.place(in_=rotulo_poster, x=ESP_8, y=ESP_8)
    nota_na_info = largura_poster < LARGURA_POSTER_DUAS_ETIQUETAS
    if not nota_na_info:
        etiqueta_nota = ctk.CTkLabel(card, text=f" ★ {filme.get('nota_imdb', 'N/A')} ", font=fonte(10, "bold"),
                                     height=20, corner_radius=ESP_8, fg_color="#0b0b0f", text_color=COR_DESTAQUE)
        etiqueta_nota.place(in_=rotulo_poster, relx=1.0, x=-ESP_8, y=ESP_8, anchor="ne")

    # Título e informações
    ctk.CTkLabel(
        card, text=encurtar(filme.get("titulo", ""), 40), font=fonte(13, "bold"), text_color=COR_TEXTO,
        wraplength=largura_poster, justify="left", anchor="nw", height=ALTURA_TITULO_CARD,
    ).pack(padx=ESP_8, anchor="w")

    duracao = filme.get("duracao_min", 0)
    texto_duracao = f"{duracao} min" if duracao else "-- min"
    info_filme = f"{filme.get('ano', '')}  •  {texto_duracao}"
    if nota_na_info:
        info_filme += f"  •  ★ {filme.get('nota_imdb', 'N/A')}"
    ctk.CTkLabel(card, text=info_filme, font=fonte(11),
                 text_color=COR_TEXTO_SUAVE, anchor="w", height=ESP_16).pack(padx=ESP_8, anchor="w")

    # Nota pessoal (estrelas) e ações
    linha_acoes = ctk.CTkFrame(card, fg_color="transparent")
    linha_acoes.pack(padx=ESP_8, pady=(ESP_8, 0), fill="x")
    nota = filme.get("nota_pessoal", 0)
    for n in range(1, 6):
        cor_estrela = COR_DESTAQUE if n <= nota else COR_ESTRELA_VAZIA
        criar_icone_clicavel(
            linha_acoes, "★", lambda n=n, i=imdb_id: dar_nota(i, n), 17, 14, cor_estrela, COR_DESTAQUE_HOVER,
        ).pack(side="left")
    criar_icone_clicavel(
        linha_acoes, "🗑", lambda i=imdb_id: remover_filme(i), 22, 12, COR_TEXTO_SUAVE, "#f87171",
    ).pack(side="right")
    criar_icone_clicavel(
        linha_acoes, "ⓘ", lambda f=filme: mostrar_sinopse(f), 22, 14, COR_TEXTO_SUAVE, COR_TEXTO,
    ).pack(side="right")

    # Status (menu de seleção; a seta usa a cor do status)
    menu_status = ctk.CTkOptionMenu(
        card, values=STATUS_LISTA, width=largura_poster, height=28, corner_radius=ESP_8,
        font=fonte(12), dropdown_font=fonte(12), text_color=COR_TEXTO,
        fg_color=COR_CARD_HOVER, button_color=cor, button_hover_color=cor,
        dropdown_fg_color=COR_CARD, dropdown_hover_color=COR_CARD_HOVER, dropdown_text_color=COR_TEXTO,
        command=lambda novo, i=imdb_id: mudar_status(i, novo),
    )
    menu_status.set(status)
    menu_status.pack(padx=ESP_8, pady=ESP_8)

    return card


def desenhar_grade(grade, texto_busca):
    """Desenha os cards da biblioteca aplicando o filtro de status e a busca."""
    global layout_grade_atual
    for widget in grade.winfo_children():
        widget.destroy()

    lista = ler_lista()
    visiveis = []
    for filme in lista:
        passa_status = filtro_status is None or filme.get("status") == filtro_status
        passa_busca = texto_busca in filme.get("titulo", "").lower()
        if passa_status and passa_busca:
            visiveis.append(filme)

    colunas, largura_poster = calcular_layout_grade(grade)
    layout_grade_atual = (colunas, largura_poster)
    configurar_colunas(grade, colunas)

    if not visiveis:
        if not lista:
            criar_estado_vazio(
                grade, colunas, "🎞️", "Sua biblioteca está vazia",
                "Busque filmes na OMDb e monte o seu catálogo.",
                "+  Adicionar filme", lambda: mostrar_pagina("busca"),
            )
        else:
            criar_estado_vazio(grade, colunas, "🔎", "Nenhum filme por aqui",
                               "Tente outra categoria ou outro termo de busca.")
        return

    organizar_cartoes([criar_card_filme(grade, filme, largura_poster) for filme in visiveis], colunas)


def texto_subtitulo_biblioteca(texto_busca=""):
    """Quantos filmes estão visíveis (filtro de status + busca digitada) em relação ao total."""
    lista = ler_lista()
    total = len(lista)
    visiveis = sum(
        1 for filme in lista
        if (filtro_status is None or filme.get("status") == filtro_status)
        and texto_busca in filme.get("titulo", "").lower()
    )
    palavra = "filme" if total == 1 else "filmes"
    if filtro_status is None and not texto_busca:
        return f"{total} {palavra} no seu catálogo"
    prefixo = f"{filtro_status} • " if filtro_status else ""
    return f"{prefixo}{visiveis} de {total} {palavra}"


def atualizar_chips(contagem, total):
    """Atualiza os botões de filtro (contagens e qual está ativo)."""
    for status, chip in chips_ref.items():
        if not chip.winfo_exists():
            continue
        quantidade = total if status is None else contagem[status]
        nome = "Todos" if status is None else status
        cor = COR_DESTAQUE if status is None else CORES_STATUS[status]
        ativo = status == filtro_status
        chip.configure(
            text=f"{nome}  {quantidade}",
            fg_color=cor if ativo else "transparent",
            hover_color=cor if ativo else COR_CARD_HOVER,
            border_color=cor if ativo else COR_BORDA,
            text_color="#0b0b0f" if ativo else COR_TEXTO_SUAVE,
        )


def atualizar_grade():
    """Redesenha a grade da biblioteca sem recarregar a página inteira."""
    atualizar_contadores()
    if pagina_atual != "biblioteca" or grade_ref is None:
        return
    if not grade_ref.winfo_exists():
        return
    texto_busca = entrada_local_ref.get().strip().lower()
    subtitulo_ref.configure(text=texto_subtitulo_biblioteca(texto_busca))
    desenhar_grade(grade_ref, texto_busca)


def mostrar_biblioteca():
    global grade_ref, entrada_local_ref, subtitulo_ref
    limpar_conteudo()

    topo, subtitulo_ref = criar_cabecalho_pagina("Biblioteca", texto_subtitulo_biblioteca())

    criar_botao_principal(topo, "+  Adicionar filme", lambda: mostrar_pagina("busca")).pack(side="right")
    entrada_local_ref = criar_campo(topo, "🔍  Buscar na biblioteca", 240)
    entrada_local_ref.pack(side="right", padx=(0, ESP_16))

    filtros = ctk.CTkFrame(area_conteudo, fg_color="transparent")
    filtros.pack(fill="x", padx=ESP_24, pady=(0, ESP_8))
    chips_ref.clear()
    for status in [None] + STATUS_LISTA:
        chip = ctk.CTkButton(
            filtros, text="", height=32, corner_radius=ESP_16, border_width=1, font=fonte(12, "bold"),
            command=lambda s=status: definir_filtro(s),
        )
        chip.pack(side="left", padx=(0, ESP_8))
        chips_ref[status] = chip
    lista = ler_lista()
    atualizar_chips(contar_por_status(lista), len(lista))

    grade_ref = ctk.CTkScrollableFrame(
        area_conteudo, fg_color="transparent",
        scrollbar_button_color=COR_BORDA, scrollbar_button_hover_color=COR_TEXTO_FRACO,
    )
    grade_ref.pack(fill="both", expand=True, padx=ESP_16, pady=(0, ESP_8))

    entrada_local_ref.bind("<KeyRelease>", lambda event: atualizar_grade())
    desenhar_grade(grade_ref, "")


# ---------------------------------------------------------------
# Página: Buscar na API
# ---------------------------------------------------------------
def mostrar_busca():
    global resultados_ref
    limpar_conteudo()
    cartoes_busca.clear()

    criar_cabecalho_pagina("Buscar filmes", "Pesquise na base da OMDb e adicione à sua biblioteca")

    barra = ctk.CTkFrame(area_conteudo, fg_color="transparent")
    barra.pack(fill="x", padx=ESP_24, pady=(0, ESP_8))

    entrada = criar_campo(barra, "Ex: Oppenheimer, Interstellar...", 200)
    entrada.pack(side="left", fill="x", expand=True, padx=(0, ESP_8))
    botao_buscar = criar_botao_principal(barra, "🔍  Buscar", None, largura=ESP_16 * 7)
    botao_buscar.pack(side="left")

    msg = ctk.CTkLabel(
        area_conteudo, text="Digite o nome do filme (a OMDb funciona melhor com títulos em inglês).",
        text_color=COR_TEXTO_SUAVE, anchor="w", height=ALTURA_MENSAGEM, font=fonte(13),
    )
    msg.pack(fill="x", padx=ESP_24, pady=0)

    resultados = ctk.CTkScrollableFrame(
        area_conteudo, fg_color="transparent",
        scrollbar_button_color=COR_BORDA, scrollbar_button_hover_color=COR_TEXTO_FRACO,
    )
    resultados.pack(fill="both", expand=True, padx=ESP_16, pady=ESP_8)
    resultados_ref = resultados
    criar_estado_vazio(resultados, COLUNAS_MINIMAS, "🔎", "Encontre o próximo filme",
                       "Os resultados da busca aparecem aqui, com pôster e ano.")

    def ao_adicionar(filme_api, pil, botao):
        ok, mensagem = adicionar_filme(filme_api["imdbID"], pil)
        msg.configure(
            text=(("✅ " if ok else "⚠️ ") + mensagem),
            text_color="#4ade80" if ok else "#fbbf24",
        )
        if ok or "já está" in mensagem:
            botao.configure(text="✔ Na biblioteca", state="disabled", fg_color=COR_CARD_HOVER)
        atualizar_contadores()

    def exibir_resultados(filmes, imagens, erro):
        if not resultados.winfo_exists():  # o usuário mudou de página
            return
        botao_buscar.configure(state="normal")
        for widget in resultados.winfo_children():
            widget.destroy()
        cartoes_busca.clear()

        if erro:
            msg.configure(text=erro, text_color="#f87171")
            return

        msg.configure(text=f"{len(filmes)} resultado(s) encontrado(s).", text_color=COR_TEXTO_SUAVE)
        ids_salvos = {f.get("imdb_id") for f in ler_lista()}
        colunas, largura_poster = calcular_layout_grade(resultados)
        configurar_colunas(resultados, colunas)

        for filme_api, pil in zip(filmes, imagens):
            card = ctk.CTkFrame(resultados, width=largura_poster + 2 * ESP_8, corner_radius=ESP_16 - ESP_4,
                                fg_color=COR_CARD, border_width=1, border_color=COR_BORDA)
            cartoes_busca.append(card)

            ctk.CTkLabel(card, image=criar_ctk_image(pil, (largura_poster, largura_poster * 3 // 2)),
                         text="" if pil is not None else "🎬", font=fonte(32),
                         text_color=COR_TEXTO_FRACO).pack(padx=ESP_8, pady=ESP_8)
            ctk.CTkLabel(
                card, text=encurtar(filme_api.get("Title", ""), 40), font=fonte(13, "bold"), text_color=COR_TEXTO,
                wraplength=largura_poster, justify="left", anchor="nw", height=ALTURA_TITULO_CARD,
            ).pack(padx=ESP_8, anchor="w")
            ctk.CTkLabel(card, text=filme_api.get("Year", ""), font=fonte(11), text_color=COR_TEXTO_SUAVE,
                         anchor="w", height=ESP_16).pack(padx=ESP_8, anchor="w")

            ja_salvo = filme_api.get("imdbID") in ids_salvos
            botao = ctk.CTkButton(
                card, width=largura_poster, height=28, corner_radius=ESP_8, font=fonte(12, "bold"),
                text="✔ Na biblioteca" if ja_salvo else "+  Adicionar",
                state="disabled" if ja_salvo else "normal",
                fg_color=COR_CARD_HOVER if ja_salvo else COR_DESTAQUE,
                hover_color=COR_DESTAQUE_HOVER, text_color=COR_SOBRE_DESTAQUE,
                text_color_disabled=COR_TEXTO_SUAVE,
            )
            botao.configure(command=lambda fa=filme_api, p=pil, b=botao: ao_adicionar(fa, p, b))
            botao.pack(padx=ESP_8, pady=ESP_8)

        organizar_cartoes(cartoes_busca, colunas)

    def buscar(event=None):
        termo = entrada.get().strip()
        if not termo:
            msg.configure(text="Digite o nome de um filme.", text_color="#fbbf24")
            return
        msg.configure(text="Buscando...", text_color=COR_TEXTO_SUAVE)
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
def criar_cartao_numero(pai, titulo, valor, detalhe="", cor=COR_DESTAQUE):
    cartao = ctk.CTkFrame(pai, corner_radius=ESP_16 - ESP_4, fg_color=COR_CARD,
                          border_width=1, border_color=COR_BORDA)
    ctk.CTkFrame(cartao, width=ESP_24, height=3, corner_radius=2, fg_color=cor).pack(
        anchor="w", padx=ESP_16, pady=(ESP_16, ESP_8))
    ctk.CTkLabel(cartao, text=titulo.upper(), font=fonte(10, "bold"), text_color=COR_TEXTO_SUAVE,
                 anchor="w").pack(anchor="w", padx=ESP_16)
    ctk.CTkLabel(cartao, text=str(valor), font=fonte(30, "bold", titulo=True), text_color=COR_TEXTO,
                 anchor="w").pack(anchor="w", padx=ESP_16)
    ctk.CTkLabel(cartao, text=detalhe or " ", font=fonte(11), text_color=COR_TEXTO_FRACO,
                 anchor="w").pack(anchor="w", padx=ESP_16, pady=(0, ESP_16))
    return cartao


def criar_painel(pai, titulo):
    painel = ctk.CTkFrame(pai, corner_radius=ESP_16 - ESP_4, fg_color=COR_CARD,
                          border_width=1, border_color=COR_BORDA)
    ctk.CTkLabel(painel, text=titulo, font=fonte(16, "bold", titulo=True), text_color=COR_TEXTO,
                 anchor="w").pack(anchor="w", padx=ESP_16, pady=(ESP_16, ESP_8))
    return painel


def estilizar_eixo(eixo):
    eixo.set_facecolor(COR_CARD)
    eixo.tick_params(colors=COR_TEXTO_SUAVE, length=0, labelsize=9)
    for borda in eixo.spines.values():
        borda.set_visible(False)


def mostrar_estatisticas():
    limpar_conteudo()
    criar_cabecalho_pagina("Estatísticas", "Um resumo do seu catálogo e dos seus hábitos")

    lista = ler_lista()
    if not lista:
        quadro = ctk.CTkFrame(area_conteudo, fg_color="transparent")
        quadro.pack(fill="both", expand=True)
        criar_estado_vazio(quadro, 1, "📊", "Ainda não há o que mostrar",
                           "Adicione filmes à biblioteca para ver as estatísticas.",
                           "+  Adicionar filme", lambda: mostrar_pagina("busca"))
        return

    pagina = ctk.CTkScrollableFrame(
        area_conteudo, fg_color="transparent",
        scrollbar_button_color=COR_BORDA, scrollbar_button_hover_color=COR_TEXTO_FRACO,
    )
    pagina.pack(fill="both", expand=True, padx=ESP_16 + ESP_4, pady=(0, ESP_8))

    # --- Números principais ---
    assistidos = [f for f in lista if f.get("status") == "Assistido"]
    minutos = sum(f.get("duracao_min", 0) for f in assistidos)
    notas = [f["nota_pessoal"] for f in lista if f.get("nota_pessoal", 0) > 0]
    media = sum(notas) / len(notas) if notas else 0
    contagem_status = contar_por_status(lista)

    linha = ctk.CTkFrame(pagina, fg_color="transparent")
    linha.pack(fill="x", padx=ESP_4, pady=(0, ESP_8))
    cartoes = [
        criar_cartao_numero(linha, "Filmes na biblioteca", len(lista),
                            f"{contagem_status['Quero ver']} na lista para ver", COR_DESTAQUE),
        criar_cartao_numero(linha, "Assistidos", len(assistidos),
                            f"{len(assistidos) * 100 / len(lista):.0f}% da coleção", CORES_STATUS["Assistido"]),
        criar_cartao_numero(linha, "Horas assistidas", f"{minutos / 60:.1f} h",
                            f"em {len(assistidos)} filme(s)", CORES_STATUS["Assistindo"]),
        criar_cartao_numero(linha, "Sua nota média", f"{media:.1f} ★" if notas else "--",
                            f"{len(notas)} avaliação(ões)" if notas else "avalie com as estrelas",
                            CORES_STATUS["Quero ver"]),
    ]
    for indice, cartao in enumerate(cartoes):
        linha.grid_columnconfigure(indice, weight=1, uniform="kpi")
        cartao.grid(row=0, column=indice, sticky="nsew", padx=(0 if indice == 0 else ESP_8, 0))

    # --- Gráficos ---
    contagem = {}
    for filme in lista:
        for genero in traduzir_generos(filme.get("genero", "")).split(", "):
            if genero and genero != "N/A":
                contagem[genero] = contagem.get(genero, 0) + 1
    ordenado = sorted(contagem.items(), key=lambda item: item[1], reverse=True)[:8]

    paineis = ctk.CTkFrame(pagina, fg_color="transparent")
    paineis.pack(fill="both", expand=True, padx=ESP_4, pady=(ESP_8, 0))
    paineis.grid_columnconfigure(0, weight=3, uniform="grafico")
    paineis.grid_columnconfigure(1, weight=2, uniform="grafico")

    painel_generos = criar_painel(paineis, "Filmes por gênero")
    painel_generos.grid(row=0, column=0, sticky="nsew", padx=(0, ESP_8))
    if not ordenado:
        ctk.CTkLabel(painel_generos, text="Sem dados de gênero para mostrar.",
                     text_color=COR_TEXTO_SUAVE).pack(pady=ESP_40)
    else:
        nomes = [g for g, _ in ordenado][::-1]
        valores = [q for _, q in ordenado][::-1]
        figura = Figure(figsize=(4.2, 3.0), dpi=100, facecolor=COR_CARD, constrained_layout=True)
        eixo = figura.add_subplot(111)
        estilizar_eixo(eixo)
        barras = eixo.barh(nomes, valores, color=COR_DESTAQUE, height=0.6)
        eixo.set_xlim(0, max(valores) * 1.2)
        eixo.xaxis.set_major_locator(MaxNLocator(integer=True))
        eixo.xaxis.grid(True, color=COR_BORDA, linewidth=0.8)
        eixo.set_axisbelow(True)
        eixo.tick_params(axis="y", labelsize=10, colors=COR_TEXTO)
        for barra, valor in zip(barras, valores):
            eixo.text(valor + max(valores) * 0.03, barra.get_y() + barra.get_height() / 2, str(valor),
                      va="center", color=COR_TEXTO, fontsize=9)
        canvas = FigureCanvasTkAgg(figura, master=painel_generos)
        canvas.get_tk_widget().configure(width=240, height=256, bg=COR_CARD, highlightthickness=0)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=ESP_16, pady=(0, ESP_16))

    painel_status = criar_painel(paineis, "Seu progresso")
    painel_status.grid(row=0, column=1, sticky="nsew")
    figura = Figure(figsize=(2.4, 2.4), dpi=100, facecolor=COR_CARD, constrained_layout=True)
    eixo = figura.add_subplot(111)
    eixo.set_facecolor(COR_CARD)
    fatias = [(s, contagem_status[s]) for s in STATUS_LISTA if contagem_status[s] > 0]
    eixo.pie(
        [q for _, q in fatias], colors=[CORES_STATUS[s] for s, _ in fatias], startangle=90, counterclock=False,
        wedgeprops={"width": 0.38, "edgecolor": COR_CARD, "linewidth": 2},
    )
    eixo.text(0, 0, str(len(lista)), ha="center", va="center", color=COR_TEXTO, fontsize=22, fontweight="bold")
    canvas = FigureCanvasTkAgg(figura, master=painel_status)
    canvas.get_tk_widget().configure(width=160, height=168, bg=COR_CARD, highlightthickness=0)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True, padx=ESP_16)

    legenda = ctk.CTkFrame(painel_status, fg_color="transparent")
    legenda.pack(fill="x", padx=ESP_16, pady=(ESP_8, ESP_16))
    for status in STATUS_LISTA:
        item = ctk.CTkFrame(legenda, fg_color="transparent")
        item.pack(fill="x", pady=1)
        ctk.CTkLabel(item, text="●", font=fonte(12), text_color=CORES_STATUS[status], width=ESP_16).pack(side="left")
        ctk.CTkLabel(item, text=status, font=fonte(12), text_color=COR_TEXTO_SUAVE).pack(side="left", padx=ESP_4)
        ctk.CTkLabel(item, text=str(contagem_status[status]), font=fonte(12, "bold"),
                     text_color=COR_TEXTO).pack(side="right")


# ---------------------------------------------------------------
# Navegação
# ---------------------------------------------------------------
def atualizar_contadores():
    lista = ler_lista()
    contagem = contar_por_status(lista)
    total = len(lista)
    minutos = sum(f.get("duracao_min", 0) for f in lista if f.get("status") == "Assistido")
    progresso_rotulo.configure(text=f"{contagem['Assistido']} de {total} assistidos")
    barra_progresso.set(contagem["Assistido"] / total if total else 0)
    horas_rotulo.configure(text=f"{minutos / 60:.1f} h assistidas")
    if pagina_atual == "biblioteca":
        atualizar_chips(contagem, total)


def marcar_item_menu(item, ativo):
    item["ativo"] = ativo
    item["quadro"].configure(fg_color=COR_CARD if ativo else "transparent")
    item["rotulo"].configure(text_color=COR_TEXTO if ativo else COR_TEXTO_SUAVE)
    if ativo:
        item["indicador"].place(x=0, rely=0.5, anchor="w")
    else:
        item["indicador"].place_forget()


def atualizar_menu():
    for chave, item in botoes_menu.items():
        marcar_item_menu(item, chave == pagina_atual)
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


def ajustar_sidebar():
    """Em janelas muito baixas o menu tem prioridade: o cartão de progresso é escondido."""
    altura = sidebar.winfo_height() / escala_widget(sidebar)
    if altura < 20:  # janela ainda não desenhada
        return
    if altura < ALTURA_SIDEBAR_COM_PROGRESSO:
        cartao_progresso.pack_forget()
    elif not cartao_progresso.winfo_ismapped():
        cartao_progresso.pack(**OPCOES_CARTAO_PROGRESSO)


def reajustar_paginas():
    """Depois de redimensionar a janela, refaz as colunas dos cards se a largura mudou o layout."""
    global job_reajuste
    job_reajuste = None
    ajustar_sidebar()
    if pagina_atual == "biblioteca" and grade_ref is not None and grade_ref.winfo_exists():
        if calcular_layout_grade(grade_ref) != layout_grade_atual:
            atualizar_grade()
    elif pagina_atual == "busca" and cartoes_busca and resultados_ref.winfo_exists():
        colunas, _ = calcular_layout_grade(resultados_ref)
        configurar_colunas(resultados_ref, colunas)
        organizar_cartoes(cartoes_busca, colunas)


def agendar_reajuste(evento=None):
    global job_reajuste
    if job_reajuste is not None:
        app.after_cancel(job_reajuste)
    job_reajuste = app.after(120, reajustar_paginas)


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
header = ctk.CTkFrame(app, height=ALTURA_CABECALHO, corner_radius=0, fg_color=COR_SUPERFICIE)
header.pack(side="top", fill="x")
header.pack_propagate(False)
ctk.CTkFrame(app, height=1, corner_radius=0, fg_color=COR_BORDA).pack(side="top", fill="x")

# Marca (esquerda): botão "play" dourado + nome
bloco_titulo = ctk.CTkFrame(header, fg_color="transparent")
bloco_titulo.pack(side="left", padx=ESP_24)
ctk.CTkLabel(bloco_titulo, text="▶", width=ESP_32 - ESP_4, height=ESP_32 - ESP_4, corner_radius=ESP_8,
             fg_color=COR_DESTAQUE, text_color=COR_SOBRE_DESTAQUE, font=fonte(12)).pack(side="left")
ctk.CTkLabel(bloco_titulo, text="Cine", font=fonte(20, "bold", titulo=True), text_color=COR_TEXTO).pack(
    side="left", padx=(ESP_8, 0))
ctk.CTkLabel(bloco_titulo, text="Tracker", font=fonte(20, "bold", titulo=True), text_color=COR_DESTAQUE).pack(
    side="left")

# Identificação do aluno (direita): iniciais + nome e curso
bloco_aluno = ctk.CTkFrame(header, fg_color="transparent")
bloco_aluno.pack(side="right", padx=ESP_24)
partes_nome = NOME_ALUNO.split()
iniciais = (partes_nome[0][0] + partes_nome[-1][0]).upper() if partes_nome else "?"
ctk.CTkLabel(bloco_aluno, text=iniciais, width=ESP_32, height=ESP_32, corner_radius=ESP_16,
             fg_color=COR_CARD_HOVER, text_color=COR_DESTAQUE, font=fonte(12, "bold")).pack(side="right")
dados_aluno = ctk.CTkFrame(bloco_aluno, fg_color="transparent")
dados_aluno.pack(side="right", padx=(0, ESP_8))
ctk.CTkLabel(dados_aluno, text=NOME_ALUNO, font=fonte(12), text_color=COR_TEXTO, height=ESP_16).pack(anchor="e")
ctk.CTkLabel(dados_aluno, text=CURSO_ALUNO, font=fonte(11), text_color=COR_TEXTO_FRACO, height=ESP_16).pack(anchor="e")

rodape = ctk.CTkFrame(app, height=ALTURA_RODAPE, corner_radius=0, fg_color=COR_SUPERFICIE)
rodape.pack(side="bottom", fill="x")
rodape.pack_propagate(False)
ctk.CTkLabel(rodape, text="🟢 Conectado à API OMDb • Dados salvos em biblioteca.json",
             anchor="w", font=fonte(11), text_color=COR_TEXTO_FRACO).pack(side="left", padx=ESP_24)
ctk.CTkLabel(rodape, text="Fatec Bebedouro • Algoritmos e Programação",
             anchor="e", font=fonte(11), text_color=COR_TEXTO_FRACO).pack(side="right", padx=ESP_24)

sidebar = ctk.CTkFrame(app, width=LARGURA_SIDEBAR, corner_radius=0, fg_color=COR_SUPERFICIE)
sidebar.pack(side="left", fill="y")
sidebar.pack_propagate(False)
ctk.CTkFrame(app, width=1, corner_radius=0, fg_color=COR_BORDA).pack(side="left", fill="y")

ctk.CTkLabel(sidebar, text="NAVEGAÇÃO", font=fonte(10, "bold"), text_color=COR_TEXTO_FRACO, anchor="w").pack(
    anchor="w", padx=ESP_24, pady=(ESP_24, ESP_8))


def criar_item_menu(pai, texto, comando):
    """Item do menu lateral: marcador dourado quando ativo, destaque suave ao passar o mouse."""
    quadro = ctk.CTkFrame(pai, height=ALTURA_ITEM_MENU, corner_radius=ESP_8, fg_color="transparent")
    quadro.pack(fill="x", padx=ESP_16, pady=(0, ESP_4))
    quadro.pack_propagate(False)
    indicador = ctk.CTkFrame(quadro, width=3, height=ESP_16 + ESP_4, corner_radius=2, fg_color=COR_DESTAQUE)
    rotulo = ctk.CTkLabel(quadro, text=texto, font=fonte(13), text_color=COR_TEXTO_SUAVE, anchor="w")
    rotulo.pack(side="left", fill="both", expand=True, padx=(ESP_16, 0))
    item = {"quadro": quadro, "rotulo": rotulo, "indicador": indicador, "ativo": False}

    def ao_entrar(evento):
        if not item["ativo"]:
            quadro.configure(fg_color=COR_CARD_HOVER)

    def ao_sair(evento):
        if not item["ativo"]:
            quadro.configure(fg_color="transparent")

    for widget in (quadro, rotulo):
        widget.bind("<Button-1>", lambda evento: comando())
        widget.bind("<Enter>", ao_entrar)
        widget.bind("<Leave>", ao_sair)
    return item


botoes_menu = {}
itens_menu = [
    ("biblioteca", "📚   Biblioteca"),
    ("busca", "🔎   Buscar filmes"),
    ("estatisticas", "📊   Estatísticas"),
]
for chave, texto in itens_menu:
    botoes_menu[chave] = criar_item_menu(sidebar, texto, lambda c=chave: navegar(c))

# Cartão de progresso no fim do menu. É empacotado depois dos itens: se a janela for muito baixa,
# o menu tem prioridade e o cartão é escondido (veja ajustar_sidebar)
cartao_progresso = ctk.CTkFrame(sidebar, corner_radius=ESP_16 - ESP_4, fg_color=COR_CARD,
                                border_width=1, border_color=COR_BORDA)
cartao_progresso.pack(**OPCOES_CARTAO_PROGRESSO)
ctk.CTkLabel(cartao_progresso, text="SEU PROGRESSO", font=fonte(10, "bold"), text_color=COR_TEXTO_FRACO,
             anchor="w").pack(anchor="w", padx=ESP_16, pady=(ESP_16, ESP_8))
progresso_rotulo = ctk.CTkLabel(cartao_progresso, text="", font=fonte(13, "bold"), text_color=COR_TEXTO, anchor="w")
progresso_rotulo.pack(anchor="w", padx=ESP_16)
barra_progresso = ctk.CTkProgressBar(cartao_progresso, height=6, fg_color=COR_BORDA, progress_color=COR_DESTAQUE)
barra_progresso.pack(fill="x", padx=ESP_16, pady=ESP_8)
horas_rotulo = ctk.CTkLabel(cartao_progresso, text="", font=fonte(11), text_color=COR_TEXTO_SUAVE, anchor="w")
horas_rotulo.pack(anchor="w", padx=ESP_16, pady=(0, ESP_16))

area_conteudo = ctk.CTkFrame(app, corner_radius=0, fg_color=COR_FUNDO)
area_conteudo.pack(side="left", fill="both", expand=True)
area_conteudo.bind("<Configure>", agendar_reajuste)

# ---------------------------------------------------------------
# Início do programa
# ---------------------------------------------------------------
mostrar_pagina("biblioteca")
verificar_fila()
app.mainloop()