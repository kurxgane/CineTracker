# CineTracker V2 — Biblioteca pessoal

A V2 marca a evolução do protótipo inicial para uma biblioteca pessoal de filmes, com acompanhamento de status, avaliação individual e estatísticas.

## Funcionalidades

- Pesquisa de filmes na API OMDb pelo nome.
- Exibição dos resultados com pôster, título e ano.
- Cadastro de filmes em uma biblioteca local.
- Identificação de filmes já cadastrados.
- Organização por status: Quero ver, Assistindo e Assistido.
- Filtro por status e pesquisa pelo título dentro da biblioteca.
- Avaliação pessoal de 1 a 5 estrelas.
- Visualização da sinopse.
- Remoção de filmes da biblioteca.
- Estatísticas de quantidade de filmes, assistidos, horas assistidas e média das avaliações pessoais.
- Gráfico com os gêneros mais frequentes.
- Busca em thread separada para manter a janela responsiva.

## Requisitos

- Python 3.9 ou superior.
- Uma chave da API OMDb.
- Dependências listadas em `requirements.txt`.

Instale as dependências:

```bash
pip install -r requirements.txt
```

## Configurar a chave da OMDb

Obtenha uma chave em [omdbapi.com](https://www.omdbapi.com/) e configure a variável de ambiente `OMDB_API_KEY`.

No PowerShell, apenas para a sessão atual:

```powershell
$env:OMDB_API_KEY="sua_chave_aqui"
```

Não coloque a chave diretamente no código nem a envie ao GitHub.

## Executar

Dentro desta pasta, execute:

```bash
python dashboard.py
```

## Arquivos e dados locais

- `biblioteca.json`: criado automaticamente para armazenar os filmes e suas informações.
- `posters/`: armazena os pôsteres baixados.

Esses dados são locais e não fazem parte do repositório. A biblioteca não é sincronizada entre computadores automaticamente.

## Observação sobre a versão

Esta pasta preserva a V2 como marco do desenvolvimento. Alterações posteriores de layout e espaçamento pertencem a uma etapa seguinte e não foram misturadas neste snapshot.
