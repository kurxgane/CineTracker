# CineTracker

Gerenciador pessoal de filmes desenvolvido em Python, com interface gráfica e integração à API OMDb.

O projeto evoluiu de um protótipo simples de busca para uma biblioteca pessoal, com acompanhamento do que quero assistir, do que estou assistindo e do que já assisti.

## Histórico de versões

- [V1 — Protótipo inicial](archive/v1/): busca por título e lista local simples.
- [V2 — Biblioteca pessoal](archive/v2/): busca de filmes pela OMDb, biblioteca com pôsteres, status de acompanhamento, avaliação pessoal e estatísticas.

As versões são preservadas em `archive/` para documentar a evolução do projeto. A V2 foi publicada como marco funcional; ajustes posteriores de interface e layout serão registrados em uma etapa própria.

## Recursos da V2

- Busca de filmes na API OMDb.
- Biblioteca local com pôsteres e informações dos filmes.
- Status: Quero ver, Assistindo e Assistido.
- Filtro por status e busca dentro da biblioteca.
- Avaliação pessoal de 1 a 5 estrelas.
- Sinopse e informações do filme.
- Estatísticas de filmes cadastrados, assistidos, horas assistidas e média das notas pessoais.
- Gráfico de filmes por gênero.
- Busca em thread separada para evitar travar a interface.

## Tecnologias

- Python
- CustomTkinter
- Requests
- Pillow
- Matplotlib
- API [OMDb](https://www.omdbapi.com/)
- JSON para armazenamento local

## Executar a V2

Consulte o [README da V2](archive/v2/README.md) para instalar as dependências, configurar a chave da OMDb e iniciar o programa.

## Dados locais e segurança

A biblioteca e os pôsteres são armazenados localmente. Arquivos pessoais, cache, ambientes Python portáteis e chaves de API não devem ser enviados ao repositório.

A chave da OMDb é lida pela variável de ambiente `OMDB_API_KEY`; não coloque credenciais diretamente no código.
