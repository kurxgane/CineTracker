# CineTracker V5 — Configuração externa e proteção dos dados

A V5 representa uma etapa de amadurecimento do CineTracker. Além da interface e dos recursos de biblioteca presentes na V4, esta versão melhora a configuração da chave da API e adiciona mecanismos para reduzir o risco de perda dos dados locais.

## Funcionalidades

- Pesquisa de filmes na API OMDb.
- Biblioteca pessoal com status Quero ver, Assistindo e Assistido.
- Avaliação pessoal de 1 a 5 estrelas.
- Visualização de sinopses, pôsteres e informações dos filmes.
- Filtros por status e pesquisa dentro da biblioteca.
- Estatísticas da coleção e gráficos.
- Interface com layout adaptável e identidade visual escura com destaque dourado.
- Busca em segundo plano para manter a interface responsiva.
- Configuração da chave OMDb por variável de ambiente ou arquivo local `config.json`.
- Identificação opcional do aluno e do curso por configuração local.
- Cópia de segurança da biblioteca antes de gravar alterações.
- Gravação temporária antes da substituição do arquivo principal.
- Tratamento de biblioteca JSON ilegível, preservando o arquivo original e tentando recuperação pelo backup.

## Tecnologias

- Python 3.9 ou superior.
- CustomTkinter — interface gráfica.
- Requests — requisições HTTP.
- Pillow — imagens e pôsteres.
- Matplotlib — gráficos.
- JSON — configuração e persistência.
- Threading e Queue — tarefas em segundo plano.
- Shutil e tratamento de exceções — cópia e recuperação de dados.

## Instalação

Instale as dependências:

```bash
pip install customtkinter requests pillow matplotlib
```

## Configurar a chave da OMDb

A chave não fica gravada no código. A aplicação procura primeiro a variável de ambiente `OMDB_API_KEY`; se ela não estiver definida, procura o campo `omdb_api_key` no arquivo `config.json`, localizado ao lado do programa.

Uma configuração local pode ter este formato:

```json
{
  "omdb_api_key": "SUA_CHAVE_OMDB",
  "nome_aluno": "Seu nome",
  "curso_aluno": "Seu curso"
}
```

Os campos `nome_aluno` e `curso_aluno` são opcionais. Não publique o arquivo `config.json` nem sua chave de API.

Também é possível configurar a variável de ambiente no PowerShell:

```powershell
$env:OMDB_API_KEY="sua_chave_aqui"
```

## Execução

```bash
python CineTracker-v5.py
```

## Dados locais e recuperação

A aplicação utiliza:

- `biblioteca.json`: biblioteca pessoal.
- `biblioteca.json.bak`: cópia de segurança da biblioteca.
- `biblioteca.json.tmp`: arquivo temporário usado durante a gravação.
- `posters/`: pôsteres baixados.

Mantenha esses arquivos junto aos dados da aplicação. A cópia de segurança é um mecanismo local de proteção, não uma sincronização em nuvem.

## Nota sobre a versão

A V5 é um snapshot histórico do código e não inclui arquivos locais de configuração, chaves de API, biblioteca pessoal ou pôsteres. A versão definitiva do projeto está na raiz do repositório.
