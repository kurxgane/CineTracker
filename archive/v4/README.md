# CineTracker V4 — Reformulação visual e layout adaptável

A V4 mantém o fluxo de biblioteca pessoal da versão anterior e concentra uma evolução importante na apresentação da aplicação: identidade visual escura com destaque dourado, componentes mais consistentes e organização da grade de filmes conforme o espaço disponível.

## Funcionalidades

- Pesquisa de filmes pela API OMDb.
- Exibição de resultados com pôster, título e ano.
- Biblioteca pessoal com status Quero ver, Assistindo e Assistido.
- Avaliação pessoal de 1 a 5 estrelas.
- Visualização de sinopses e remoção de filmes.
- Filtros da biblioteca por status.
- Estatísticas da coleção, incluindo filmes assistidos, tempo assistido e avaliações.
- Salvamento local em `biblioteca.json` e pôsteres em `posters/`.
- Busca em thread separada e comunicação com a interface por fila.

## Evolução em relação à V3

- Identidade visual renovada, com fundo escuro e destaque dourado.
- Componentes visuais e espaçamentos mais padronizados.
- Grade de cartões com quantidade de colunas adaptável à largura da janela.
- Ajustes de layout para acomodar pôsteres e informações em diferentes larguras.
- Melhor organização visual da navegação e das páginas.

## Tecnologias

- Python 3.9 ou superior.
- CustomTkinter — interface gráfica.
- Requests — comunicação com a API OMDb.
- Pillow — tratamento e enquadramento dos pôsteres.
- Matplotlib — gráficos das estatísticas.
- JSON — armazenamento local.
- Threading e Queue — tarefas em segundo plano.

## Instalação

```bash
pip install customtkinter requests pillow matplotlib
```

Configure sua chave da OMDb pela variável de ambiente `OMDB_API_KEY`.

No PowerShell:

```powershell
$env:OMDB_API_KEY="sua_chave_aqui"
```

## Execução

```bash
python CineTracker-v4.py
```

## Dados locais

O programa utiliza `biblioteca.json` para os filmes cadastrados e a pasta `posters/` para os pôsteres baixados. Esses arquivos são criados localmente durante a utilização.

## Nota sobre o arquivo publicado

A cópia arquivada teve a chave de API que estava gravada no código substituída por uma configuração vazia. Utilize sua própria chave por meio de `OMDB_API_KEY`.

Esta é uma versão histórica de desenvolvimento, não a versão definitiva do CineTracker.
