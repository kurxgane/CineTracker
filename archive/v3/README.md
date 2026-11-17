# CineTracker V3 — Biblioteca com interface em páginas

A V3 amplia o CineTracker como uma biblioteca pessoal de filmes. Esta versão reúne busca na OMDb, gerenciamento da coleção, avaliações pessoais e estatísticas em uma interface gráfica organizada por páginas.

## Funcionalidades

- Pesquisa de filmes pelo título usando a API OMDb.
- Exibição de informações e pôsteres dos resultados.
- Adição de filmes à biblioteca pessoal.
- Organização por status: Quero ver, Assistindo e Assistido.
- Avaliação pessoal de 1 a 5 estrelas.
- Visualização da sinopse e remoção de filmes.
- Filtros da biblioteca por status.
- Painel de estatísticas com contagem por status, tempo assistido e avaliações.
- Salvamento local em `biblioteca.json`.
- Armazenamento de pôsteres na pasta `posters/`.
- Busca e carregamento em thread separada, com fila para atualizar a interface sem bloquear a janela.

## Tecnologias

- Python 3.9 ou superior.
- CustomTkinter — interface gráfica.
- Requests — requisições HTTP para a OMDb.
- Pillow — carregamento e tratamento de pôsteres.
- Matplotlib — gráficos das estatísticas.
- JSON — persistência dos dados.
- Threading e Queue — execução de tarefas em segundo plano.

## Instalação

Instale as dependências:

```bash
pip install customtkinter requests pillow matplotlib
```

É necessária uma chave da API OMDb. Configure-a na variável de ambiente `OMDB_API_KEY`.

No PowerShell:

```powershell
$env:OMDB_API_KEY="sua_chave_aqui"
```

## Execução

Dentro desta pasta, execute:

```bash
python CineTracker-v3.py
```

## Dados locais

Ao utilizar o programa, são criados:

- `biblioteca.json`: dados da biblioteca pessoal.
- `posters/`: pôsteres baixados para exibição local.

Esses arquivos são dados de execução e não fazem parte deste snapshot histórico.

## Nota sobre o arquivo publicado

A cópia arquivada não contém a chave de API que estava escrita diretamente no código original. Para executar, use sua própria chave pela variável de ambiente `OMDB_API_KEY`.

Esta versão é preservada como registro do desenvolvimento; a versão definitiva está na raiz do repositório.
