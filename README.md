# CineTracker

Gerenciador pessoal de filmes desenvolvido em Python. O projeto começou como um protótipo simples com interface gráfica, busca na API OMDb e uma lista local de filmes.

## Histórico

- `archive/v1/`: primeira versão do CineTracker, preservada como registro da evolução do projeto.
- A versão arquivada permite pesquisar um filme pelo título, visualizar ano, avaliação e sinopse, e adicioná-lo a uma lista local em JSON.

## Tecnologias

- Python
- CustomTkinter
- Requests
- API [OMDb](https://www.omdbapi.com/)
- JSON para persistência local

## Versão arquivada (V1)

A V1 é um protótipo histórico e não representa necessariamente os recursos da versão mais recente em desenvolvimento. Para executá-la, use Python 3.9 ou superior.

### Instalação

```bash
pip install customtkinter requests
```

### Configuração da API

Obtenha uma chave no site da OMDb e configure a variável de ambiente `OMDB_API_KEY`. Não coloque sua chave diretamente no código nem a envie ao GitHub.

No PowerShell (apenas para a sessão atual):

```powershell
$env:OMDB_API_KEY="sua_chave_aqui"
```

### Execução

Na pasta `archive/v1/`, execute:

```bash
python buscador_omdb.py
```

A lista pessoal é salva localmente em `minha_lista.json`, no diretório de execução. Esse arquivo não deve ser versionado, pois contém os dados pessoais da biblioteca.
