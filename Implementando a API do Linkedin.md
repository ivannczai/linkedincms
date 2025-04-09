Perfeito. Vou pesquisar como integrar a API do LinkedIn em uma aplicação web Python com frontend em Tailwind, permitindo que usuários façam login com segurança e agendem postagens em seus perfis pessoais diretamente pelo seu sistema.

Já volto com um guia detalhado para você implementar isso com segurança e eficiência.

# **Guia de Integração da API do LinkedIn em Aplicação Web Python**

Este guia passo a passo descreve como integrar a **API do LinkedIn** em uma aplicação web Python (com frontend em Tailwind CSS) para atingir os seguintes objetivos:

* **Login com LinkedIn (OAuth 2.0)**: Permitir que usuários façam login de forma segura usando sua conta LinkedIn, integrando esse login com o sistema de autenticação interno já existente.

* **Obtenção de Tokens**: Recuperar os tokens de acesso necessários (access token e refresh token, se disponível) para realizar chamadas à API em nome do usuário.

* **Publicação Agendada no Perfil**: Permitir que o usuário agende uma postagem (texto e/ou imagem) através da aplicação para ser publicada futuramente em seu perfil pessoal no LinkedIn.

Vamos cobrir desde o registro do aplicativo no LinkedIn Developers, configuração de permissões, fluxo OAuth 2.0 (3-legged), armazenamento seguro de tokens, até o uso das APIs de **User Generated Content (UGC)** do LinkedIn para criar postagens e considerações de agendamento, limitações e boas práticas.

## **1\. Registro do Aplicativo no LinkedIn Developers**

O primeiro passo é **registrar uma aplicação** no portal de desenvolvedores do LinkedIn. Isso fornecerá as credenciais (Client ID e Client Secret) necessárias para usar a API e configurar os escopos de permissão adequados. Siga estes passos:

1. **Crie uma LinkedIn Page (Página da empresa)**: O LinkedIn requer que você associe o app a uma página. Caso você não tenha uma página, crie uma nova (pode ser temporária ou representando sua aplicação) ([Create a new app for a LinkedIn Page | LinkedIn Help](https://www.linkedin.com/help/linkedin/answer/a1667239#:~:text=4,in%20the%20App%20name%20box)).

2. **Acesse o LinkedIn Developer Portal**: Entre em [developer.linkedin.com](https://developer.linkedin.com/) com sua conta. Clique em **"My Apps"** no canto superior e depois em **"Create App"** ([Create a new app for a LinkedIn Page | LinkedIn Help](https://www.linkedin.com/help/linkedin/answer/a1667239#:~:text=1)).

3. **Preencha os Detalhes do App**: Forneça um nome para o aplicativo e selecione a LinkedIn Page criada no passo anterior. Informe também a URL da política de privacidade da sua aplicação (obrigatório) ([Create a new app for a LinkedIn Page | LinkedIn Help](https://www.linkedin.com/help/linkedin/answer/a1667239#:~:text=5,company%20page%20name%20or%20URL)). Faça upload de um logo do aplicativo e aceite os termos para concluir a criação ([Create a new app for a LinkedIn Page | LinkedIn Help](https://www.linkedin.com/help/linkedin/answer/a1667239#:~:text=6,enter%20your%20privacy%20policy%20URL)).

4. **Anote o Client ID e Client Secret**: Após criar, abra o app em "My Apps". Na aba **Auth** (ou similar), você encontrará o **Client ID** (Identificador do cliente) e poderá gerar um **Client Secret** (Segredo do cliente). Guarde esses valores em local seguro – **nunca os exponha publicamente ou no frontend**. (Ex.: use variáveis de ambiente no backend para armazená-los). *Dica:* O LinkedIn recomenda seguir boas práticas para manter o Client Secret seguro ([LinkedIn 3-Legged OAuth Flow \- LinkedIn | Microsoft Learn](https://learn.microsoft.com/en-us/linkedin/shared/authentication/authorization-code-flow#:~:text=code%20string%20The%20authorization%20code,Yes)).

5. **Configure os URLs de Redirecionamento (OAuth Redirect URLs)**: Ainda na aba de autenticação, adicione o URL de callback da sua aplicação (ex.: `https://seuapp.com/auth/linkedin/callback`). Esse é o endereço para o qual o LinkedIn redirecionará o usuário após o login, retornando o código de autorização.

6. **Adicione Produtos e Permissões (Scopes)**: Na aba **Products** do app, habilite os produtos **"Sign In with LinkedIn"** (para autenticação do usuário) e **"Share on LinkedIn"** (para postar em nome do usuário). Ao habilitar "Sign In with LinkedIn using OpenID Connect", seu app receberá automaticamente permissões de leitura básica de perfil e email do membro autenticado, e ao adicionar "Share on LinkedIn", você obtém o escopo `w_member_social` necessário para postar em nome do usuário ([Getting Access to LinkedIn APIs \- LinkedIn | Microsoft Learn](https://learn.microsoft.com/en-us/linkedin/shared/authentication/getting-access#:~:text=Product%2FProgram%20Permission%20Description%20Sign%20in,behalf%20of%20an%20authenticated%20member)) ([Share on LinkedIn \- LinkedIn | Microsoft Learn](https://learn.microsoft.com/en-us/linkedin/consumer/integrations/self-serve/share-on-linkedin#:~:text=New%20members%20Sharing%20on%20LinkedIn,scope)). Esses são escopos **abertos** disponíveis a todos os desenvolvedores (não requerem aprovação especial) ([Getting Access to LinkedIn APIs \- LinkedIn | Microsoft Learn](https://learn.microsoft.com/en-us/linkedin/shared/authentication/getting-access#:~:text=Open%20Permissions%20)).

**Escopos necessários:** Para nossos objetivos, vamos usar principalmente:

* `r_liteprofile` (perfil básico) e `r_emailaddress` (email) – possibilitam obter nome, foto do perfil e email do usuário autenticado ([Getting Access to LinkedIn APIs \- LinkedIn | Microsoft Learn](https://learn.microsoft.com/en-us/linkedin/shared/authentication/getting-access#:~:text=Sign%20in%20with%20LinkedIn%20using,authenticated%20member%27s%20primary%20email%20address)). Essas permissões são obtidas através do produto "Sign In with LinkedIn".

* `w_member_social` – permite postar, comentar e curtir em nome do membro autenticado (necessária para publicar no perfil) ([Getting Access to LinkedIn APIs \- LinkedIn | Microsoft Learn](https://learn.microsoft.com/en-us/linkedin/shared/authentication/getting-access#:~:text=Sign%20in%20with%20LinkedIn%20using,behalf%20of%20an%20authenticated%20member)), fornecida pelo produto "Share on LinkedIn".

**Nota:** Caso algum desses escopos não apareça disponível, verifique se os produtos corretos foram habilitados no app. Por exemplo, sem adicionar o "Share on LinkedIn", não será possível solicitar `w_member_social` ([Share on LinkedIn \- LinkedIn | Microsoft Learn](https://learn.microsoft.com/en-us/linkedin/consumer/integrations/self-serve/share-on-linkedin#:~:text=If%20your%20application%20does%20not,w_member_social)). Após adicionar, o LinkedIn pode levar alguns minutos para aplicar as permissões. Além disso, garanta que sua aplicação tenha uma **URL de política de privacidade** válida e cumpra os termos de uso do LinkedIn, pois esses são requisitos para obter permissão de login e compartilhamento.

## **2\. Fluxo de Autenticação OAuth 2.0 (Login com LinkedIn)**

Com o aplicativo registrado e permissões configuradas, podemos implementar o **OAuth 2.0 de três etapas (3-legged OAuth)** para autenticar usuários via LinkedIn. O fluxo geral é:

**2.1. Solicitar Autorização do Usuário (Redirect para LinkedIn):**  
 No backend Python, crie um endpoint (rota) de login, por exemplo `/auth/linkedin`. Quando acessado, ele redireciona o usuário para a página de autorização do LinkedIn. Essa URL de autorização segue o formato:

```
https://www.linkedin.com/oauth/v2/authorization?response_type=code
&client_id={CLIENT_ID}
&redirect_uri={REDIRECT_URI}
&state={STATE_RANDOM}
&scope=r_liteprofile%20r_emailaddress%20w_member_social
```

*   
  `response_type=code` indica que queremos o **Authorization Code**.

* `client_id` é seu Client ID do app LinkedIn.

* `redirect_uri` deve ser exatamente igual a um dos URLs autorizados configurados no app.

* `state` é um valor aleatório que sua aplicação gera para cada solicitação (uma string única, imprevisível). Ele serve para **prevenir ataques CSRF** – você deverá verificar esse mesmo valor no retorno ([LinkedIn 3-Legged OAuth Flow \- LinkedIn | Microsoft Learn](https://learn.microsoft.com/en-us/linkedin/shared/authentication/authorization-code-flow#:~:text=Before%20you%20use%20the%20authorization,error%20code%20in%20response)).

* `scope` lista os escopos solicitados (separados por espaço ou `%20` codificado). Incluímos `r_liteprofile`, `r_emailaddress` e `w_member_social` conforme necessário.

*Exemplo (Flask):*

```py
from urllib.parse import urlencode
from flask import redirect, session

# Configurações
CLIENT_ID = "seu_client_id"
REDIRECT_URI = "https://seuapp.com/auth/linkedin/callback"

@app.route("/auth/linkedin")
def linkedin_login():
    auth_url = "https://www.linkedin.com/oauth/v2/authorization"
    params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "state": generate_random_state(),  # função sua para gerar string aleatória
        "scope": "r_liteprofile r_emailaddress w_member_social"
    }
    # Guarda o estado na sessão para conferência posterior
    session["oauth_state"] = params["state"]
    # Redireciona o usuário para a URL de autorização do LinkedIn
    return redirect(auth_url + "?" + urlencode(params))
```

Quando o usuário for redirecionado, ele fará login (se ainda não estiver) no LinkedIn e verá uma tela solicitando permissões para seu aplicativo (listando os escopos e o nome da sua aplicação). Ao aceitar, o LinkedIn irá **redirecionar de volta** para o `redirect_uri` fornecido, anexando um **código de autorização** na URL.

**2.2. Callback e Obtenção do Código de Autorização:**  
 Implemente um endpoint de callback (por exemplo, `/auth/linkedin/callback`) para capturar os parâmetros retornados pelo LinkedIn. A URL de retorno será algo como:

```
https://seuapp.com/auth/linkedin/callback?code={AUTH_CODE}&state={STATE_RANDOM}
```

No handler desse callback, você deve:

* Verificar se o parâmetro `state` recebido é igual ao valor salvo na sessão na etapa anterior. Isso garante que a resposta é legítima e não foi forjada por terceiros ([LinkedIn 3-Legged OAuth Flow \- LinkedIn | Microsoft Learn](https://learn.microsoft.com/en-us/linkedin/shared/authentication/authorization-code-flow#:~:text=Before%20you%20use%20the%20authorization,error%20code%20in%20response)). Se não bater, deve-se rejeitar a requisição (p.ex. retornando 401 Unauthorized).

* Verificar se há um parâmetro `code`. Caso o usuário tenha negado permissões ou ocorrido algum erro, a URL pode conter `error` em vez de `code`.

*Exemplo (Flask) callback:*

```py
import requests
from flask import request, session

CLIENT_ID = "seu_client_id"
CLIENT_SECRET = "seu_client_secret"
REDIRECT_URI = "https://seuapp.com/auth/linkedin/callback"

@app.route("/auth/linkedin/callback")
def linkedin_callback():
    error = request.args.get("error")
    if error:
        # Tratamento se usuário negou acesso ou ocorreu erro
        return f"Erro na autenticação: {error}", 400

    code = request.args.get("code")
    state = request.args.get("state")
    # Verifica CSRF state
    if state != session.get("oauth_state"):
        return "State inválido (possível CSRF)", 401

    # Trocando o código pelo token de acesso
    token_url = "https://www.linkedin.com/oauth/v2/accessToken"
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }
    resp = requests.post(token_url, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
    token_data = resp.json()
    # token_data conterá access_token e expires_in, e possivelmente refresh_token
    ...
```

**2.3. Trocar o Código por um Token de Acesso:**  
 Conforme o exemplo acima, após receber o código de autorização, fazemos uma requisição POST para o endpoint de token do LinkedIn: `https://www.linkedin.com/oauth/v2/accessToken` com os parâmetros necessários ([LinkedIn 3-Legged OAuth Flow \- LinkedIn | Microsoft Learn](https://learn.microsoft.com/en-us/linkedin/shared/authentication/authorization-code-flow#:~:text=POST%20https%3A%2F%2Fwww)) ([LinkedIn 3-Legged OAuth Flow \- LinkedIn | Microsoft Learn](https://learn.microsoft.com/en-us/linkedin/shared/authentication/authorization-code-flow#:~:text=POST%20%20https%3A%2F%2Fwww)):

* `grant_type=authorization_code` (fluxo de autorização de 3 partes).

* `code` recebido no callback.

* `redirect_uri` (mesmo usado anteriormente).

* `client_id` e `client_secret` da sua aplicação.

Se tudo ocorreu corretamente, o LinkedIn responderá com um JSON contendo o **access token**. Exemplo de resposta:

```
{
    "access_token": "AQX...sTR", 
    "expires_in": 5184000,
    "refresh_token": "...", 
    "refresh_token_expires_in": 31536000,
    "scope": "r_liteprofile r_emailaddress w_member_social"
}
```

Os campos importantes são: `access_token` (token de acesso que será usado para chamadas autenticadas à API) e `expires_in` (segundos até expirar; geralmente \~5184000 segundos \= 60 dias) ([LinkedIn 3-Legged OAuth Flow \- LinkedIn | Microsoft Learn](https://learn.microsoft.com/en-us/linkedin/shared/authentication/authorization-code-flow#:~:text=accommodate%20any%20future%20expansion%20plans,longer%20lifespan%20than%20access%20tokens)). Dependendo da configuração do LinkedIn, pode haver também `refresh_token` e seu prazo (`refresh_token_expires_in`), mas *tokens de refresh programático são disponibilizados apenas para parceiros aprovados* em casos de marketing/empresarial ([Refresh Tokens with OAuth 2.0 \- LinkedIn | Microsoft Learn](https://learn.microsoft.com/en-us/linkedin/shared/authentication/programmatic-refresh-tokens#:~:text=LinkedIn%20offers%20programmatic%20refresh%20tokens,application%20when%20refresh%20tokens%20expire)). Para aplicações comuns com permissões abertas, você normalmente receberá apenas o access token e deverá usar o fluxo de OAuth novamente quando expirar.

**Importante:** Guarde o `access_token` com segurança. Ele tem comprimento \~500 caracteres (pode ser maior no futuro) ([LinkedIn 3-Legged OAuth Flow \- LinkedIn | Microsoft Learn](https://learn.microsoft.com/en-us/linkedin/shared/authentication/authorization-code-flow#:~:text=access_token%20string%20The%20access%20token,day%20lifespan)) e dá acesso à API em nome do usuário. **Não exponha esse token no frontend ou em logs**. Armazene-o no backend (por exemplo, em um banco de dados, associado ao usuário interno) e use apenas em comunicações servidor-servidor com o LinkedIn.

## **3\. Integração com o Sistema de Autenticação Interno**

Após obter o token e identificar o usuário, integre isso ao seu sistema de usuários existente:

* **Recuperar dados básicos do perfil**: Com o access token em mãos, você pode chamar a API do LinkedIn para obter informações do usuário logado, como nome e email, a fim de identificar ou criar a conta local. Por exemplo, uma requisição GET para `https://api.linkedin.com/v2/me` com cabeçalho `Authorization: Bearer {access_token}` retorna o perfil básico do usuário (nome, sobrenome, ID LinkedIn, foto, headline, etc.) ([LinkedIn 3-Legged OAuth Flow \- LinkedIn | Microsoft Learn](https://learn.microsoft.com/en-us/linkedin/shared/authentication/authorization-code-flow#:~:text=)) ([Profile API \- LinkedIn | Microsoft Learn](https://learn.microsoft.com/en-us/linkedin/shared/integrations/people/profile-api#:~:text=%7B%20,%7D)). Para obter o email, use o endpoint `https://api.linkedin.com/v2/emailAddress?q=members&projection=(elements*(handle~))` com o mesmo token, já que solicitamos `r_emailaddress`.

   *Exemplo usando requests:*

```py
headers = {"Authorization": f"Bearer {token_data['access_token']}"}
profile_resp = requests.get("https://api.linkedin.com/v2/me", headers=headers)
profile = profile_resp.json()
email_resp = requests.get("https://api.linkedin.com/v2/emailAddress?q=members&projection=(elements*(handle~))", headers=headers)
email_info = email_resp.json()
user_email = email_info["elements"][0]["handle~"]["emailAddress"]
user_name = profile["localizedFirstName"] + " " + profile["localizedLastName"]
linkedin_id = profile["id"]  # ID único do LinkedIn para este usuário
```

*   
  Aqui obtemos o `linkedin_id` do usuário (ex.: "yrZCpj2Z12"), que corresponde a um identificador único do perfil. O LinkedIn usa URNs para referenciar usuários em algumas chamadas, combinando esse ID com prefixo "urn:li:person:" (por ex., `urn:li:person:yrZCpj2Z12`) ([Share on LinkedIn \- LinkedIn | Microsoft Learn](https://learn.microsoft.com/en-us/linkedin/consumer/integrations/self-serve/share-on-linkedin#:~:text=,)) ([Profile API \- LinkedIn | Microsoft Learn](https://learn.microsoft.com/en-us/linkedin/shared/integrations/people/profile-api#:~:text=match%20at%20L161%20The%20,person%20ID)). Esse URN será necessário para publicar conteúdos mais adiante.

* **Criar ou associar usuário interno**: Com o email ou ID LinkedIn, procure em seu banco de dados um usuário existente.

  * Se encontrar um usuário com o mesmo email, você pode vincular a conta LinkedIn a essa conta (salvando o linkedin\_id e token associados a ela) para futuros logins.

  * Se não existir, crie um novo usuário interno com os dados recebidos (por exemplo, definindo o email, nome e marcando que o login é via LinkedIn).

  * Garanta atualizar em seu banco: o access token (e refresh token se houver) associados ao usuário, a data de obtenção e expiração.

* **Autenticar no sistema interno**: Por fim, considere o usuário como logado na sua aplicação – por exemplo, crie uma sessão ou JWT interno para mantê-lo autenticado, assim como faria após um login tradicional. O LinkedIn em si já autenticou o usuário, mas agora você inicia a sessão na *sua* aplicação com base nessa autenticação bem-sucedida.

**Dica de segurança:** Armazene o **Client Secret** do LinkedIn no backend (por exemplo, em uma variável de ambiente ou arquivo seguro) e **nunca** expose no front. O mesmo vale para os tokens de acesso dos usuários – mantenha-os somente no servidor. Assim você evita riscos de sequestro de sessão via LinkedIn. Além disso, siga as orientações do LinkedIn sobre armazenamento de dados: só mantenha informações do perfil do usuário enquanto tiver permissão e necessidade, e ofereça opção de logout/desconexão que revogue o token se apropriado (o usuário pode também revogar acessos via configurações do LinkedIn).

## **4\. Armazenamento e Renovação de Tokens com Segurança**

Gerenciar os tokens de acesso é crucial para manter a integração funcionando sem interrupções:

* **Banco de Dados de Tokens**: Mantenha uma tabela/coleção que armazene o token LinkedIn de cada usuário, o `linkedin_id` do usuário, data de expiração (`expires_in` convertido para timestamp ou duração) e possivelmente o `refresh_token` se fornecido. Relacione isso à conta interna do usuário. **Nunca** armazene Client ID/Secret ou tokens sensíveis no front-end ou em cookies do cliente – guarde no servidor.

* **Validade do Access Token**: O token fornecido pelo LinkedIn expira em \~60 dias (5184000 segundos) por padrão ([LinkedIn 3-Legged OAuth Flow \- LinkedIn | Microsoft Learn](https://learn.microsoft.com/en-us/linkedin/shared/authentication/authorization-code-flow#:~:text=accommodate%20any%20future%20expansion%20plans,longer%20lifespan%20than%20access%20tokens)). Sem um refresh token, quando esse prazo estiver próximo do fim, é necessário obter um novo token. Boas práticas:

  * **Renovação antecipada**: Monitore a idade do token; por exemplo, quando faltar poucos dias ou horas para expirar, você pode iniciar um novo fluxo OAuth silencioso. O LinkedIn permite que, se o usuário ainda estiver logado no LinkedIn e o token atual não expirou, ele possa obter um novo token sem pedir permissões novamente (o login é invisível) ([LinkedIn 3-Legged OAuth Flow \- LinkedIn | Microsoft Learn](https://learn.microsoft.com/en-us/linkedin/shared/authentication/authorization-code-flow#:~:text=Refreshing%20an%20access%20token%20is,the%20following%20conditions%20are%20met)). Basta redirecionar o usuário pelo fluxo de autorização novamente antes do vencimento – a tela de permissões será pulada automaticamente nesse caso (chamado *Silent Authentication* ou refresh implícito) ([LinkedIn 3-Legged OAuth Flow \- LinkedIn | Microsoft Learn](https://learn.microsoft.com/en-us/linkedin/shared/authentication/authorization-code-flow#:~:text=token%2C%20go%20through%20the%20authorization,the%20following%20conditions%20are%20met)).

  * **Refresh Token (se disponível)**: Algumas integrações aprovadas recebem um `refresh_token` válido por 1 ano ([Refresh Tokens with OAuth 2.0 \- LinkedIn | Microsoft Learn](https://learn.microsoft.com/en-us/linkedin/shared/authentication/programmatic-refresh-tokens#:~:text=LinkedIn%20offers%20programmatic%20refresh%20tokens,application%20when%20refresh%20tokens%20expire)). Se seu app tiver esse token, você pode usá-lo para obter um novo access token via um POST para `/oauth/v2/accessToken` com `grant_type=refresh_token` e fornecendo o refresh token. Isso retornará um novo access token sem interação do usuário ([Refresh Tokens with OAuth 2.0 \- LinkedIn | Microsoft Learn](https://learn.microsoft.com/en-us/linkedin/shared/authentication/programmatic-refresh-tokens#:~:text=Step%202%3A%20Exchanging%20a%20Refresh,for%20a%20New%20Access%20Token)). Lembre-se de atualizar o armazenamento com o novo token e note que o refresh token geralmente permanece o mesmo até expirar (após 1 ano) ([Refresh Tokens with OAuth 2.0 \- LinkedIn | Microsoft Learn](https://learn.microsoft.com/en-us/linkedin/shared/authentication/programmatic-refresh-tokens#:~:text=%2A%20Day%201%20,member%20using%20the%20authorization%20flow)).

  * **Re-autenticação**: Se o token expirar e não conseguir renová-lo (por falta de refresh token ou usuário desconectado), esteja preparado para direcionar o usuário a fazer login novamente via LinkedIn (Fluxo OAuth) para revalidar a conexão.

* **Segurança no Armazenamento**: Considere criptografar tokens sensíveis no banco de dados, ou ao menos protegê-los com camadas de segurança do seu backend, já que quem possuir o access token terá acesso à API em nome do usuário. Além disso, jamais compartilhar o token com outros serviços não confiáveis. Os tokens e dados da API LinkedIn devem ser usados conforme os termos de uso do LinkedIn, somente para as funcionalidades permitidas e com consentimento do usuário ([Profile API \- LinkedIn | Microsoft Learn](https://learn.microsoft.com/en-us/linkedin/shared/integrations/people/profile-api#:~:text=Note)).

* **Proteção do Client Secret**: Conforme já mencionado, o Client Secret deve ficar inacessível externamente. Trate-o como senha de alta sensibilidade. (*Dica: Armazene-o em variáveis de ambiente ou use serviços de vault. Evite commitar em repositórios.*) ([LinkedIn 3-Legged OAuth Flow \- LinkedIn | Microsoft Learn](https://learn.microsoft.com/en-us/linkedin/shared/authentication/authorization-code-flow#:~:text=client_secret%20string%20The%20Secret%20Key,Yes))

## **5\. Publicando Postagens no Perfil do Usuário via LinkedIn API**

Com o usuário autenticado e tokens salvos, podemos usar a **LinkedIn API** para criar postagens em nome dele. O LinkedIn oferece a **UGC Post API** (User Generated Content) para compartilhar conteúdo no feed do usuário autenticado. É necessário ter o escopo `w_member_social` para usar esta API ([Share on LinkedIn \- LinkedIn | Microsoft Learn](https://learn.microsoft.com/en-us/linkedin/consumer/integrations/self-serve/share-on-linkedin#:~:text=New%20members%20Sharing%20on%20LinkedIn,scope)).

**5.1. Preparação – Identificador do Autor:** Todas as requisições de postagem exigem indicar quem é o autor. Isso é feito usando o URN da pessoa. Como vimos, podemos obter o ID único do usuário (ex.: "abcdefg12345") através do `/v2/me`. O URN terá formato `"urn:li:person:{id}"`. Por exemplo: se `profile["id"] = "abcdefg12345"`, então o autor será `"urn:li:person:abcdefg12345"`. Guarde este valor pois será usado em cada chamada de postagem.

**5.2. Formatando a Requisição de Postagem:** Para criar um post simples (apenas texto), faremos uma requisição **POST** para o endpoint `https://api.linkedin.com/v2/ugcPosts`. O corpo da requisição deve conter, no mínimo, os campos abaixo:

* `author`: o URN do autor (seu usuário) ([Share on LinkedIn \- LinkedIn | Microsoft Learn](https://learn.microsoft.com/en-us/linkedin/consumer/integrations/self-serve/share-on-linkedin#:~:text=Field%20Name%20Description%20Format%20Required,Possible%20values)).

* `lifecycleState`: use `"PUBLISHED"` para publicar imediatamente.

* `specificContent`: um objeto definindo o conteúdo. Para uma postagem de texto, usamos o tipo `com.linkedin.ugc.ShareContent` com subcampos:

  * `shareCommentary`: o texto da postagem (campo `text`).

  * `shareMediaCategory`: para só texto, use `"NONE"` ([Share on LinkedIn \- LinkedIn | Microsoft Learn](https://learn.microsoft.com/en-us/linkedin/consumer/integrations/self-serve/share-on-linkedin#:~:text=,)); se fosse um artigo/link seria `"ARTICLE"`, se imagem, `"IMAGE"`, etc.

* `visibility`: define a visibilidade da postagem. Geralmente `"PUBLIC"` para que seja visível para a rede inteira ([Share on LinkedIn \- LinkedIn | Microsoft Learn](https://learn.microsoft.com/en-us/linkedin/consumer/integrations/self-serve/share-on-linkedin#:~:text=,)).

Um exemplo de corpo JSON para uma postagem de texto "Olá mundo\!" pública seria:

```
{
  "author": "urn:li:person:abcdefg12345",
  "lifecycleState": "PUBLISHED",
  "specificContent": {
    "com.linkedin.ugc.ShareContent": {
      "shareCommentary": {
        "text": "Olá, LinkedIn! Esta é uma postagem de teste via API."
      },
      "shareMediaCategory": "NONE"
    }
  },
  "visibility": {
    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
  }
}
```

A chamada deve incluir no header a autenticação: `Authorization: Bearer {access_token}` e também um header especial exigido pela API LinkedIn: `X-Restli-Protocol-Version: 2.0.0` ([Share on LinkedIn \- LinkedIn | Microsoft Learn](https://learn.microsoft.com/en-us/linkedin/consumer/integrations/self-serve/share-on-linkedin#:~:text=Note)). Este header garante a versão correta do protocolo para a API UGC.

*Exemplo de código para postar texto:*

```py
post_url = "https://api.linkedin.com/v2/ugcPosts"
post_data = {
    "author": f"urn:li:person:{linkedin_id}",
    "lifecycleState": "PUBLISHED",
    "specificContent": {
        "com.linkedin.ugc.ShareContent": {
            "shareCommentary": {"text": "Olá, LinkedIn! Post agendado via minha aplicação."},
            "shareMediaCategory": "NONE"
        }
    },
    "visibility": { 
        "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC" 
    }
}
headers = {
    "Authorization": f"Bearer {access_token}",
    "X-Restli-Protocol-Version": "2.0.0",
    "Content-Type": "application/json"  # enviando JSON
}
response = requests.post(post_url, headers=headers, json=post_data)
if response.status_code == 201:
    print("Postagem criada com sucesso!")
else:
    print("Erro ao criar postagem:", response.text)
```

Se a requisição for bem-sucedida, o LinkedIn retornará **201 Created**, possivelmente sem corpo, mas com um header `X-RestLi-Id` contendo o identificador do post recém-criado ([Share on LinkedIn \- LinkedIn | Microsoft Learn](https://learn.microsoft.com/en-us/linkedin/consumer/integrations/self-serve/share-on-linkedin#:~:text=)).

**5.3. Postar Imagens (ou links) junto com Texto:** Para incluir mídia (imagens ou vídeos) na postagem, é necessário um processo em etapas:

* **Registrar o upload da imagem**: Antes de enviar o arquivo binário, você deve solicitar ao LinkedIn uma URL para upload. Faz-se um POST para `https://api.linkedin.com/v2/assets?action=registerUpload` com um corpo indicando que tipo de mídia vai subir e quem é o dono ([Share on LinkedIn \- LinkedIn | Microsoft Learn](https://learn.microsoft.com/en-us/linkedin/consumer/integrations/self-serve/share-on-linkedin#:~:text=%7B%20,%5B)) ([Share on LinkedIn \- LinkedIn | Microsoft Learn](https://learn.microsoft.com/en-us/linkedin/consumer/integrations/self-serve/share-on-linkedin#:~:text=%22registerUploadRequest%22%3A%20%7B%20%22recipes%22%3A%20%5B%20%22urn%3Ali%3AdigitalmediaRecipe%3Afeedshare,urn%3Ali%3AuserGeneratedContent)). Por exemplo, para imagem:

```
{
  "registerUploadRequest": {
    "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
    "owner": "urn:li:person:abcdefg12345",
    "serviceRelationships": [
      {
        "relationshipType": "OWNER",
        "identifier": "urn:li:userGeneratedContent"
      }
    ]
  }
}
```

*   
  Essa requisição, com cabeçalhos de autorização iguais (Bearer token), retornará uma resposta contendo um `uploadUrl` (URL única para enviar o arquivo) e um `asset` URN ([Share on LinkedIn \- LinkedIn | Microsoft Learn](https://learn.microsoft.com/en-us/linkedin/consumer/integrations/self-serve/share-on-linkedin#:~:text=A%20successful%20response%20will%20contain,save%20for%20the%20next%20steps)) ([Share on LinkedIn \- LinkedIn | Microsoft Learn](https://learn.microsoft.com/en-us/linkedin/consumer/integrations/self-serve/share-on-linkedin#:~:text=%22mediaArtifact%22%3A%20%22urn%3Ali%3AdigitalmediaMediaArtifact%3A%28urn%3Ali%3Adigitalme%20diaAsset%3AC5522AQGTYER3k3ByHQ%2Curn%3Ali%3AdigitalmediaMediaArtifactClass%3Afeedshare,)). Guarde ambos.

* **Upload do arquivo**: Em seguida, faça o upload do arquivo de imagem para o `uploadUrl` fornecido. A documentação sugere usar um PUT/POST direto para aquele endpoint, enviando o binário da imagem no corpo da requisição e incluindo o header de Authorization Bearer ([Share on LinkedIn \- LinkedIn | Microsoft Learn](https://learn.microsoft.com/en-us/linkedin/consumer/integrations/self-serve/share-on-linkedin#:~:text=Using%20the%20,to%20upload%20an%20image%20file)). Em Python, você pode usar `requests.put(uploadUrl, data=open('imagem.png','rb'), headers={"Authorization": f"Bearer {token}"})`. Se for um arquivo pequeno, uma única requisição basta (o LinkedIn suporta upload multipart também, mas para simplicidade consideramos direto).

* **Criar a postagem com mídia**: Depois de sucesso no upload (recebendo talvez 201 ou 202), você pode finalmente criar a postagem usando o mesmo endpoint `ugcPosts`. O corpo será parecido com o de texto, mas `shareMediaCategory` será `"IMAGE"` e deve incluir um array `media` com detalhes da mídia ([Share on LinkedIn \- LinkedIn | Microsoft Learn](https://learn.microsoft.com/en-us/linkedin/consumer/integrations/self-serve/share-on-linkedin#:~:text=,)). Use o `asset` URN obtido no registro de upload como identificação da mídia. Exemplo de `specificContent` para imagem:

```
"specificContent": {
  "com.linkedin.ugc.ShareContent": {
    "shareCommentary": { "text": "Meu post com imagem" },
    "shareMediaCategory": "IMAGE",
    "media": [
      {
        "status": "READY",
        "description": { "text": "Descrição da imagem opcional" },
        "media": "urn:li:digitalmediaAsset:ABCDEFG12345", 
        "title": { "text": "Título opcional da imagem" }
      }
    ]
  }
}
```

*   
  Onde `"media"` (dentro de `media`: array) é justamente o URN do asset retornado. Envie a POST com esse JSON e os cabeçalhos como antes. Para vídeos, o processo é similar, apenas usando `"feedshare-video"` no registro e `"VIDEO"` no shareMediaCategory.

**Observação:** Links (URLs externas) podem ser compartilhados usando `shareMediaCategory: "ARTICLE"` e fornecendo dentro de `media` o `originalUrl`, título e descrição do link ([Share on LinkedIn \- LinkedIn | Microsoft Learn](https://learn.microsoft.com/en-us/linkedin/consumer/integrations/self-serve/share-on-linkedin#:~:text=,https%3A%2F%2Fblog.linkedin.com)) ([Share on LinkedIn \- LinkedIn | Microsoft Learn](https://learn.microsoft.com/en-us/linkedin/consumer/integrations/self-serve/share-on-linkedin#:~:text=%7B%20,Official%20LinkedIn%20Blog)). Nesse caso não precisa de upload, o LinkedIn gerará o preview automaticamente a partir da URL fornecida.

## **6\. Agendamento de Postagens**

Para permitir que o usuário agende uma postagem para o futuro, sua aplicação precisará de uma lógica de agendamento no backend. Como o LinkedIn não fornece funcionalidade de "post later" na API, a responsabilidade de postar no horário certo é da sua aplicação. Aqui está como você pode implementar:

* **Interface de Agendamento**: No frontend (Tailwind pode ajudar a estilizar), ofereça um formulário onde o usuário conectado escolhe o conteúdo da postagem (texto e opcionalmente anexa imagem) e uma data/hora futura para publicação.

* **Armazenamento do Agendamento**: Quando o usuário agenda, salve no banco de dados uma nova entrada contendo:

  1. ID do usuário interno (para saber quem agendou),

  2. Conteúdo da postagem (texto, links, paths da imagem a postar ou referência à mídia enviada),

  3. Timestamp de quando publicar,

  4. Status (ex: "pendente").

  5. Qualquer meta necessário, como o URN do autor (ou podemos obter na hora via `linkedin_id` do usuário) e possivelmente o `asset` se o upload já foi realizado antecipadamente. (Uma alternativa é salvar também o arquivo de imagem temporariamente e só fazer o upload próximo da hora).

* **Tarefa assíncrona para publicar**: Configure um mecanismo de **job scheduler** no backend para verificar quando é hora de publicar e realizar a ação:

  1. Você pode usar um **cron job** simples que roda a cada minuto consultando o banco por posts pendentes cuja hora \<= agora e manda publicar.

  2. Ou use uma biblioteca de agendamento como **APScheduler** em Python para agendar um job para aquele timestamp.

  3. Uma solução robusta em ambiente web é utilizar uma fila de tarefas assíncronas como **Celery** ou **RQ**: quando um post é agendado, enfileirar uma tarefa com ETA (tempo de execução) para a data agendada. Por exemplo, com Celery você pode fazer `publish_linkedin_post.apply_async(args=[post_id], eta=data_publicacao)`.

* **Execução da publicação**: A tarefa agendada, ao disparar, irá:

  1. Rechecar no banco se o post ainda está pendente (não foi cancelado pelo usuário).

  2. Opcional: se passar muito tempo desde o login, garantir que o access token do usuário é válido. Se você armazenou a validade, verifique; se expirado, tente usar refresh token se houver. Caso não, a tarefa pode abortar marcando erro e talvez notificar que precisa reautenticar.

  3. Montar o conteúdo da postagem conforme a seção anterior (texto e mídia).

  4. Chamar a API do LinkedIn (endpoint `ugcPosts` e possivelmente `assets` para upload se for imagem) para criar a postagem.

  5. Atualizar o status no banco (por exemplo, "publicado" e guardar o `post ID` retornado ou quaisquer erros ocorridos).

* **Exemplo de código (conceitual) usando Celery:**

```py
from celery import Celery
app = Celery(broker='redis://...', backend='redis://...')

@app.task
def publish_linkedin_post(post_id):
    # Buscar dados do post agendado
    post = db.get_scheduled_post(post_id)
    if not post or post.status != 'pendente':
        return "Post cancelado ou já publicado."
    user = db.get_user(post.user_id)
    token = user.linkedin_access_token
    # Verificar expiração do token
    if token_expired(user):
        if user.refresh_token:
            token = refresh_access_token(user.refresh_token)
            save_new_token(user, token)
        else:
            # Não foi possível renovar
            db.update_post_status(post_id, 'erro', detail='Token expirado')
            return "Token expirado - necessidade de login."

    # Montar requisição LinkedIn
    data = build_linkedin_post_data(post, user.linkedin_id)
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Restli-Protocol-Version": "2.0.0",
        "Content-Type": "application/json"
    }
    resp = requests.post("https://api.linkedin.com/v2/ugcPosts", headers=headers, json=data)
    if resp.status_code == 201:
        db.update_post_status(post_id, 'publicado')
    else:
        db.update_post_status(post_id, 'erro', detail=resp.text)
```

*   
  Você precisaria rodar um scheduler (como **Celery Beat**) para acionar essas tarefas no horário certo ou usar ETA conforme mencionado. Certifique-se de configurar adequadamente o timezone ou usar UTC consistentemente.

* **Cancelar/Editar Agendamento**: Implemente também funcionalidade para o usuário cancelar ou editar uma postagem antes do horário, se desejar. Isso envolve atualizar ou remover o registro do banco e talvez revogar qualquer tarefa pendente (em Celery, pode-se guardar o task id e tentar revogar).

## **7\. Limitações da API do LinkedIn e Boas Práticas**

Ao integrar com a API do LinkedIn em perfis pessoais, é importante conhecer alguns limites e adotar boas práticas para não violar as políticas da plataforma:

* **Rate Limits (Limites de requisições)**: O LinkedIn impõe limites diários de chamadas à API. No contexto de postagens de membro (`w_member_social`), atualmente o limite é de **até 150 requisições por dia por usuário** e **até 100.000 por dia para a aplicação** inteira ([Share on LinkedIn \- LinkedIn | Microsoft Learn](https://learn.microsoft.com/en-us/linkedin/consumer/integrations/self-serve/share-on-linkedin#:~:text=Rate%20Limits)). Isso inclui criar post, editar, deletar, comentar, etc., feitos via API em nome daquele membro. Planeje sua aplicação para respeitar esses limites. Se excedidos, a API retorna erro 429 (Too Many Requests) ([LinkedIn API Rate Limiting \- LinkedIn | Microsoft Learn](https://learn.microsoft.com/en-us/linkedin/shared/api-guide/concepts/rate-limits#:~:text=To%20prevent%20abuse%20and%20ensure,at%20midnight%20UTC%20every%20day)) ([LinkedIn API Rate Limiting \- LinkedIn | Microsoft Learn](https://learn.microsoft.com/en-us/linkedin/shared/api-guide/concepts/rate-limits#:~:text=Rate%20limited%20requests%20will%20receive,will%20return%20to%20normal%20automatically)). Utilize exponenciação de espera (exponential backoff) e tratamento adequado de erros de rate limit.

* **Uso Apropriado de Dados**: As permissões abertas fornecem acesso limitado aos dados do perfil (apenas informações básicas e email do próprio usuário autenticado). Não é possível, por exemplo, obter lista de conexões ou postar em grupos/empresas sem programas especiais. Além disso, os dados obtidos (perfil, email) devem ser usados conforme termos do LinkedIn: somente para oferecer a funcionalidade ao usuário e *com consentimento*. Não armazene ou compartilhe dados do usuário além do necessário ([Profile API \- LinkedIn | Microsoft Learn](https://learn.microsoft.com/en-us/linkedin/shared/integrations/people/profile-api#:~:text=Note)). A API Terms of Use do LinkedIn proíbe usos indevidos, então evite, por exemplo, postar sem autorização do usuário, ou em intervalos muito curtos simulando spam.

* **Restrições de Conteúdo**: Qualquer conteúdo postado deve obedecer as diretrizes do LinkedIn. Embora a API em si não filtre conteúdo (além de possivelmente remover formatação HTML, etc.), postar conteúdo que viole os termos do LinkedIn pode levar a remoção do post ou até suspensão do aplicativo. Oriente os usuários a não agendar nada que viole políticas de uso ou direitos autorais.

* **Validação de Imagens**: Ao fazer upload de imagens, verifique os tamanhos suportados. A documentação do LinkedIn recomenda formatos comuns (PNG, JPEG) e tamanhos não extremamente grandes para feed. Um upload incorreto pode resultar em erro ou timeout.

* **Segurança no OAuth**: Reforçando, use sempre **HTTPS** em seu redirect URI para garantir que o código de autorização não seja interceptado. Utilize o parâmetro `state` e verifique-o rigorosamente ([LinkedIn 3-Legged OAuth Flow \- LinkedIn | Microsoft Learn](https://learn.microsoft.com/en-us/linkedin/shared/authentication/authorization-code-flow#:~:text=Before%20you%20use%20the%20authorization,error%20code%20in%20response)). Nunca inclua segredos (client secret, tokens) em chamadas do lado do cliente ou em código aberto. Revogue tokens se suspeitar de comprometimento.

* **Atualizações da API**: A API do LinkedIn evolui e algumas rotas ou formatos podem mudar. Mantenha-se atualizado através da [documentação oficial do LinkedIn](https://learn.microsoft.com/en-us/linkedin/). Por exemplo, verifique periodicamente se há alterações nos endpoints de UGC Post ou nas políticas de refresh token. No momento, o que cobrimos reflete a documentação até 2025\.

* **Testes**: Use contas de teste ou o modo **OAuth 2.0 Token Generator** no portal do LinkedIn para testar chamadas sem queimar chamadas de produção ([Quick Start \- LinkedIn | Microsoft Learn](https://learn.microsoft.com/en-us/linkedin/marketing/quick-start?view=li-lms-2025-02#:~:text=1,23%20on%20the%20Postman%20Network)). O LinkedIn permite criar até 5 perfis de teste para desenvolvimento ([LinkedIn API Rate Limiting \- LinkedIn | Microsoft Learn](https://learn.microsoft.com/en-us/linkedin/shared/api-guide/concepts/rate-limits#:~:text=In%20this%20article)) – aproveite isso para não usar sua conta pessoal em todos os testes.

Seguindo este guia, você terá implementado uma integração robusta: usuários poderão usar suas credenciais LinkedIn para login, a aplicação obterá os tokens adequados e poderá postar conteúdo no LinkedIn em nome deles (imediatamente ou agendado). Lembre-se sempre de tratar erros da API (respostas 4xx/5xx), informar claramente o usuário sobre as permissões que ele está concedendo e proporcionar meios de desvincular a conta LinkedIn caso desejado. Assim, você garante uma boa experiência ao usuário e conformidade com as políticas do LinkedIn durante toda a integração. Boa codificação\!

**Referências:** Documentação oficial do LinkedIn (OAuth 2.0, Profile API, UGC Post API), LinkedIn Developer Portal e melhores práticas citadas ao longo do texto ([Getting Access to LinkedIn APIs \- LinkedIn | Microsoft Learn](https://learn.microsoft.com/en-us/linkedin/shared/authentication/getting-access#:~:text=Product%2FProgram%20Permission%20Description%20Sign%20in,behalf%20of%20an%20authenticated%20member)) ([Share on LinkedIn \- LinkedIn | Microsoft Learn](https://learn.microsoft.com/en-us/linkedin/consumer/integrations/self-serve/share-on-linkedin#:~:text=New%20members%20Sharing%20on%20LinkedIn,scope)) ([Share on LinkedIn \- LinkedIn | Microsoft Learn](https://learn.microsoft.com/en-us/linkedin/consumer/integrations/self-serve/share-on-linkedin#:~:text=Rate%20Limits)) ([LinkedIn 3-Legged OAuth Flow \- LinkedIn | Microsoft Learn](https://learn.microsoft.com/en-us/linkedin/shared/authentication/authorization-code-flow#:~:text=Before%20you%20use%20the%20authorization,error%20code%20in%20response)), entre outras. Todas as informações técnicas e exemplos são baseados nesses recursos.

