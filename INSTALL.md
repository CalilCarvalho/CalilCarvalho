# Matrix Contributions — instalação

Este pacote foi preparado para um **repositório de perfil do GitHub**.

## 1. Repositório correto

O repositório de perfil precisa ser público e ter exatamente o mesmo nome do seu usuário.

Exemplo:

- usuário: `meuusuario`
- repositório: `meuusuario/meuusuario`

## 2. Copie o conteúdo

Copie para a raiz do repositório:

- `.github/workflows/update-matrix.yml`
- `assets/matrix-contributions.gif`
- `scripts/generate_matrix_contributions.py`
- `requirements.txt`
- `README.md`

Se você já possui um README de perfil, não substitua tudo. Use o bloco existente em `README_SNIPPET.md`.

## 3. Faça commit e push

Depois de enviar os arquivos, abra a aba **Actions** do repositório.

Procure:

`Update Matrix Contributions`

Use **Run workflow** para a primeira atualização.

## 4. Funcionamento automático

Depois disso, o workflow roda diariamente e:

1. lê o calendário público de contribuições do dono do repositório;
2. gera `assets/matrix-contributions.gif`;
3. faz commit do novo GIF se houver alteração.

Nesta versão não é necessário criar Personal Access Token.

## 5. Frase usada

`WAKE UP, DEVelop a new world_`

O trecho `DEV` permanece em maiúsculas exatamente como definido.

## Teste local opcional

Instale as dependências:

```bash
pip install -r requirements.txt
```

Teste sem internet, com dados sintéticos:

```bash
python scripts/generate_matrix_contributions.py --demo
```

Teste com um perfil real:

```bash
python scripts/generate_matrix_contributions.py SEU_USUARIO
```

## Observação sobre esta V3

Esta é a versão simples: os dados são lidos da página pública de contribuições do GitHub.
Ela não precisa de token, mas depende da estrutura HTML pública usada pelo GitHub.

Uma evolução futura pode usar a API GraphQL oficial do GitHub para maior controle.


## V3.1 — correção do cache do perfil

Esta versão também resolve o caso em que o GIF novo aparece dentro do repositório,
mas o perfil continua exibindo uma versão antiga.

O workflow altera automaticamente o parâmetro `?v=` no `README.md` em cada execução.
Isso muda a URL usada no perfil e evita que o proxy/cache de imagens reutilize a versão anterior.

Também foram aplicados:

- texto fixo `@CalilCarvalho`;
- 72 frames;
- 130 ms por frame;
- ciclo aproximado de 9,36 segundos.

Voce pode mudar os dados, mudando principalmente o GIF gerado para algo contendo seu nome, abaixo vou deixar o comando para gerar o mesmo gif, você pode e deve melhorar ele hehe

