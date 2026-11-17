# CineTracker 🎬

Aplicação desktop desenvolvida em Python para organizar uma biblioteca pessoal de filmes, acompanhar o que você pretende assistir e registrar sua experiência cinematográfica.

O projeto foi desenvolvido como trabalho final da disciplina de Algoritmos e Programação da Fatec Bebedouro.

## 🎯 Objetivo

O CineTracker surgiu da ideia de criar uma ferramenta simples para organizar o consumo de filmes em um só lugar.

Em vez de depender de anotações ou listas espalhadas, o usuário pode pesquisar títulos, adicioná-los à própria biblioteca, acompanhar seu progresso e visualizar estatísticas sobre seus hábitos cinematográficos.

## ✨ Funcionalidades

- **Busca de filmes:** pesquisa de títulos por meio da API OMDb.
- **Biblioteca pessoal:** adição e organização dos filmes encontrados.
- **Acompanhamento:** classificação dos filmes em "Quero ver", "Assistindo" e "Assistido".
- **Avaliações pessoais:** registro de notas para os filmes.
- **Pôsteres:** exibição e armazenamento local das imagens dos filmes.
- **Estatísticas:** visualização da quantidade de filmes, progresso, horas assistidas, média das avaliações e distribuição por gênero.
- **Persistência de dados:** armazenamento da biblioteca em arquivo JSON, com cópia de segurança.
- **Tradução complementar:** integração opcional com a API TMDb para obter títulos e sinopses em português.

## 🛠️ Tecnologias utilizadas

- **Python 3.9+:** linguagem principal.
- **CustomTkinter:** construção da interface gráfica.
- **Requests:** comunicação com APIs externas.
- **OMDb API:** obtenção dos dados dos filmes.
- **TMDb API (opcional):** complemento de títulos e sinopses em português.
- **Pillow:** processamento e exibição de imagens.
- **Matplotlib:** criação dos gráficos estatísticos.
- **JSON:** armazenamento local da biblioteca e configurações.
- **Threading e Queue:** execução de tarefas em segundo plano para evitar travamentos durante as consultas.

## ⚙️ Instalação

### 1. Requisitos

- Python 3.9 ou superior.
- Conexão com a internet.
- Uma chave de API da OMDb.

### 2. Baixar o projeto

Clone o repositório:

```bash
git clone https://github.com/kurxgane/CineTracker.git
cd CineTracker
```

### 3. Instalar as dependências

```bash
pip install -r requirements.txt
```

## 🔑 Configuração das APIs

O CineTracker utiliza a OMDb como fonte principal dos dados. A integração com a TMDb é opcional.

### OMDb (necessária)

1. Acesse https://www.omdbapi.com/apikey.aspx.
2. Solicite uma chave de API.
3. Copie o arquivo `config.example.json` e renomeie a cópia para `config.json`.
4. Abra o arquivo e preencha o campo `omdb_api_key` com sua chave.

### TMDb (opcional)

Para obter títulos e sinopses em português, é possível configurar também um token de leitura da TMDb.

Preencha o campo `tmdb_read_access_token` no `config.json`.

Sem essa configuração, o programa continua funcionando normalmente utilizando os dados da OMDb.

**Importante:** o arquivo `config.json` contém credenciais pessoais e não deve ser enviado ao GitHub.

## ▶️ Como executar

Depois de instalar as dependências e configurar a chave da OMDb, execute:

```bash
python dashboard.py
```

## 💾 Armazenamento dos dados

Os dados são mantidos localmente, na pasta do programa:

- `biblioteca.json`: biblioteca pessoal de filmes.
- `biblioteca.json.bak`: cópia de segurança da biblioteca.
- `posters/`: pôsteres armazenados localmente.
- `cache_tmdb.json`: cache das consultas à TMDb, quando utilizada.
- `config.json`: configurações e credenciais locais.

Esses arquivos são criados ou utilizados pelo programa durante sua execução. Os dados pessoais e as credenciais não fazem parte do repositório público.

## 📸 Capturas de tela

As imagens abaixo demonstram as principais áreas da aplicação.

> Adicionar imagens reais do programa nesta seção antes da publicação.

Sugestão de organização:

```text
screenshots/
├── inicio.png
├── busca.png
├── biblioteca.png
└── estatisticas.png
```

## 📚 Conhecimentos aplicados e adquiridos

Durante o desenvolvimento, foram aplicados conceitos estudados na disciplina, como:

- Variáveis e tipos de dados.
- Estruturas condicionais e de repetição.
- Operadores lógicos e relacionais.
- Funções para organização e reutilização do código.
- Listas e dicionários para manipulação de informações.
- Leitura e gravação de arquivos.

Também foram explorados novos recursos e tecnologias:

- Desenvolvimento de interfaces gráficas com CustomTkinter.
- Consumo de APIs REST para obtenção de dados externos.
- Armazenamento e recuperação de informações em JSON.
- Manipulação de imagens com Pillow.
- Construção de gráficos com Matplotlib.
- Uso de threads e filas para executar tarefas sem bloquear a interface.
- Tratamento de erros e criação de cópias de segurança dos dados.

## 🎓 Projeto acadêmico

Desenvolvido para a disciplina de Algoritmos e Programação.

**Curso:** Big Data no Agronegócio  
**Instituição:** Fatec Bebedouro

---

Desenvolvido com Python e uma paixão por cinema. 🍿
