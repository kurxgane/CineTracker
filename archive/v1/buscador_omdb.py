import customtkinter as ctk
import requests
import json
import os

# 1. Configuração principal da janela
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.geometry("900x550")
app.title("CineTracker - Gestor de Filmes (Projeto Final Fatec)")

# A chave da API deve ser configurada na variável de ambiente OMDB_API_KEY.
# Não armazene credenciais diretamente no código-fonte.
API_KEY = os.environ.get("OMDB_API_KEY")
URL_API = "https://www.omdbapi.com/"
ARQUIVO_JSON = "minha_lista.json"

# Variável para armazenar temporariamente o filme pesquisado
filme_atual = {}


# --- Lógica de dados e API ---

def ler_lista():
    """Lê o arquivo JSON e devolve a lista de filmes (lista de dicionários)."""
    if not os.path.exists(ARQUIVO_JSON):
        return []
    with open(ARQUIVO_JSON, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def salvar_lista(lista):
    """Grava a lista de filmes no arquivo JSON."""
    with open(ARQUIVO_JSON, "w", encoding="utf-8") as f:
        json.dump(lista, f, ensure_ascii=False, indent=4)


def carregar_lista():
    """Atualiza o painel esquerdo com os filmes salvos."""
    textbox_lista.configure(state="normal")
    textbox_lista.delete("0.0", "end")

    lista = ler_lista()
    if not lista:
        textbox_lista.insert("0.0", "Sua lista está vazia.")
    else:
        # Laço 'for' para formatar cada dicionário da lista
        for i, filme in enumerate(lista, 1):
            texto = f"{i}. {filme['titulo']} ({filme['ano']})\n⭐ {filme['nota']}\n\n"
            textbox_lista.insert("end", texto)

    textbox_lista.configure(state="disabled")


def pesquisar_filme():
    """Busca o filme na API da OMDb e mostra o resultado na tela."""
    global filme_atual
    termo = entry_pesquisa.get().strip()

    if not termo:
        filme_titulo.configure(text="Erro: digite um nome!")
        return

    if not API_KEY:
        filme_titulo.configure(text="Configure a variável de ambiente OMDB_API_KEY.")
        filme_ano.configure(text="")
        filme_sinopse.configure(text="")
        filme_atual = {}
        return

    try:
        # 'params' cuida de espaços e acentos no título automaticamente
        resposta = requests.get(
            URL_API,
            params={"t": termo, "apikey": API_KEY, "plot": "short"},
            timeout=10,
        ).json()

        if resposta.get("Response") == "True":
            filme_titulo.configure(text=resposta.get("Title"))
            filme_ano.configure(
                text=f"Ano: {resposta.get('Year')} | Avaliação: {resposta.get('imdbRating')}"
            )
            filme_sinopse.configure(text=resposta.get("Plot"))

            # Guarda num dicionário temporário
            filme_atual = {
                "titulo": resposta.get("Title"),
                "ano": resposta.get("Year"),
                "nota": resposta.get("imdbRating"),
            }
        else:
            # Mostra a mensagem real da API (ex.: "Invalid API key!")
            filme_titulo.configure(text=resposta.get("Error", "Filme não encontrado."))
            filme_ano.configure(text="")
            filme_sinopse.configure(text="")
            filme_atual = {}

    except requests.exceptions.RequestException:
        filme_titulo.configure(text="Erro de conexão com a Internet.")
        filme_atual = {}


def adicionar_a_lista():
    """Adiciona o filme pesquisado ao arquivo JSON."""
    global filme_atual
    if not filme_atual:
        filme_titulo.configure(text="Pesquise um filme primeiro!")
        return

    lista = ler_lista()

    # Evita duplicados
    for filme in lista:
        if filme["titulo"] == filme_atual["titulo"] and filme["ano"] == filme_atual["ano"]:
            filme_titulo.configure(text="⚠️ Esse filme já está na lista.")
            return

    lista.append(filme_atual)
    salvar_lista(lista)

    carregar_lista()  # Atualiza a tela na hora
    filme_titulo.configure(text="✅ Adicionado com sucesso!")


# --- Construção da interface gráfica ---

left_panel = ctk.CTkFrame(app, width=280, corner_radius=0, fg_color="#1e1e1e")
left_panel.pack(side="left", fill="y")

title_label = ctk.CTkLabel(left_panel, text="🍿 CineTracker", font=("Arial", 26, "bold"))
title_label.pack(pady=30, padx=20)

lista_label = ctk.CTkLabel(left_panel, text="Minha Lista:", font=("Arial", 16))
lista_label.pack(pady=(10, 5), padx=20, anchor="w")

textbox_lista = ctk.CTkTextbox(left_panel, width=240, height=350)
textbox_lista.pack(pady=10, padx=20)

right_panel = ctk.CTkFrame(app, corner_radius=15)
right_panel.pack(side="right", fill="both", expand=True, padx=20, pady=20)

pesquisa_label = ctk.CTkLabel(right_panel, text="Pesquisar Filme", font=("Arial", 20, "bold"))
pesquisa_label.pack(pady=(30, 10))

search_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
search_frame.pack(pady=10)

entry_pesquisa = ctk.CTkEntry(search_frame, placeholder_text="Ex: Oppenheimer", width=350)
entry_pesquisa.pack(side="left", padx=10)
entry_pesquisa.bind("<Return>", lambda event: pesquisar_filme())  # Enter também busca

btn_pesquisar = ctk.CTkButton(search_frame, text="🔍 Buscar", width=100, command=pesquisar_filme)
btn_pesquisar.pack(side="left")

resultado_frame = ctk.CTkFrame(right_panel, corner_radius=10, fg_color="#2b2b2b")
resultado_frame.pack(pady=30, padx=50, fill="both", expand=True)

filme_titulo = ctk.CTkLabel(resultado_frame, text="Título: (aguardando pesquisa...)", font=("Arial", 20, "bold"))
filme_titulo.pack(pady=(30, 5))

filme_ano = ctk.CTkLabel(resultado_frame, text="Ano: -- | Avaliação: --", font=("Arial", 16), text_color="gray")
filme_ano.pack(pady=5)

filme_sinopse = ctk.CTkLabel(resultado_frame, text="A sinopse do filme aparecerá aqui.", wraplength=400, font=("Arial", 14))
filme_sinopse.pack(pady=30)

btn_adicionar = ctk.CTkButton(
    resultado_frame,
    text="➕ Adicionar à Lista",
    fg_color="#28a745",
    hover_color="#218838",
    font=("Arial", 14, "bold"),
    command=adicionar_a_lista,
)
btn_adicionar.pack(side="bottom", pady=30)

# Carrega a lista automaticamente ao abrir o programa
carregar_lista()

app.mainloop()
