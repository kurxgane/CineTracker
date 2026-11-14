# CineTracker V1 — Protótipo inicial

Esta pasta preserva a primeira versão do CineTracker como parte do histórico de desenvolvimento.

## O que esta versão faz

- Pesquisa um filme pelo título na API OMDb.
- Exibe título, ano, avaliação do IMDb e sinopse.
- Permite adicionar o resultado à lista pessoal.
- Salva os filmes em `minha_lista.json`.
- Evita adicionar novamente um filme com o mesmo título e ano.

## Requisitos

- Python 3.9 ou superior.
- `customtkinter`
- `requests`
- Uma chave válida da API OMDb.

Instale as dependências:

```bash
pip install customtkinter requests
```

Configure a variável de ambiente `OMDB_API_KEY` com sua chave da OMDb antes de executar. No PowerShell:

```powershell
$env:OMDB_API_KEY="sua_chave_aqui"
```

Execute com:

```bash
python buscador_omdb.py
```

## Observação

Esta é uma versão histórica, mantida para documentar a evolução do projeto. O arquivo `minha_lista.json` é criado localmente e não deve ser enviado ao repositório.
