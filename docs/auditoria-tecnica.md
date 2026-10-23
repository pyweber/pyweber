# Auditoria técnica do PyWeber 1.8.3

Revisão estática do código em `pyweber/`, versão declarada em `pyproject.toml`. Critério: aplicação empresarial crítica (banca, RH, ERP, setor público). Data: 22 de outubro de 2026.

Não houve teste de carga. Cada crítica abaixo aponta para código existente.

O PyWeber já tem uma base de segurança real — CSRF com HMAC, escape de texto, jail de estáticos, allowlist de redirects e segredo obrigatório em produção — mas ainda não está ao nível de uma aplicação crítica. O bloqueio principal está no servidor WebSocket embutido, na forma como a sessão reativa é ligada, e em buracos da sanitização que o escape de texto não cobre.

Média das nove notas: **5.7 / 10**. A barra para um sistema crítico fica à volta de 8.

## Achados

| ID | Prioridade | Área | Achado |
|---|---|---|---|
| WS-01 | Crítica | WebSocket | Frame sem tamanho máximo no servidor embutido |
| WS-02 | Alta | Sessões | O session id do cliente vale mais do que o cookie HttpOnly |
| CK-01 | Alta | Cookies | O valor do cookie não é codificado |
| CK-02 | Alta | Cookies | `Secure` depende de `https_enabled`, não do pedido |
| UP-01 | Alta | Uploads | `validate_uploads` não rejeita ficheiros |
| XSS-01 | Alta | Templates | `sanitize=True` não cobre atributos perigosos nem URLs |
| AU-01 | Alta | Autenticação | Login é um cookie assinado sem revogação |
| AU-02 | Alta | Autenticação | Security scheme sem `verify` aceita qualquer credencial |
| RL-01 | Alta | Rate limit | Limitador desligado, em memória e sem teto de chaves |
| CFG-01 | Alta | Deploy | Defeitos de desenvolvimento no `config.toml` de projeto |
| HO-01 | Alta | Sessões | Handoff não está ligado ao cookie e é consumido cedo |
| PF-01 | Alta | Performance | Handlers síncronos correm no event loop |
| CSP-01 | Média | Headers | CSP por defeito permite inline e qualquer origem HTTPS |
| CSRF-01 | Média | CSRF | Isenções por prefixo sem fronteira de caminho |
| PW-01 | Média | Passwords | PBKDF2-SHA256 a 260 000 iterações, sem teto de tamanho |
| ORM-01 | Média | ORM | Camada fina; URL por defeito em memória |
| TPL-01 | Média | Templates | Loader de HTML sem raiz confinada |
| DOM-01 | Média | Templates | O DOM do browser é fundido na árvore do servidor |
| WS-03 | Média | WebSocket | Ping respondido com ping; sem verificação de Origin |
| ARCH-01 | Média | Arquitetura | Estado global de processo |
| DX-01 | Baixa | DX | Superfície inconsistente e módulos duplicados por typo |
| HDR-01 | Baixa | Headers | Faltam Permissions-Policy, COOP e CORP |

### O que já está sólido

- CSRF double-submit com HMAC e `SameSite=Strict`, activo por defeito. `compare_digest` na assinatura.
- Texto HTML escapado quando `sanitize=True`.
- `safe_join` nos estáticos. `Window.open` e redirects absolutos passam por allowlist.
- `/docs` fica oculto em produção salvo `expose_in_production`.
- Corpo limitado a 10 MiB.
- ORM delega em SQLAlchemy 2 async: não há API de SQL concatenado.
- `session_scope` faz rollback. Cookies de sessão são `HttpOnly`.
- CORS só reflecte origens da allowlist, nunca `*`.
- Caminho ASGI, Redis opcional para sessões reativas, Alembic no CLI.
- Cobertura configurada falha abaixo de 88%.

---

## 1. Arquitetura

O pacote está partido em áreas reconhecíveis: `core` (elemento, template, eventos), `connection` (HTTP e WebSocket), `models` (rotas, pedido, resposta), `services` (pipeline, estáticos, OpenAPI), `auth`, `db`, `session_store`, `cli`. Há um comentário em `pyweber.py` a dizer que a migração de mixins para composição está planeada, e parte disso já aconteceu (`ResponsePipeline`, `StaticFilesService`, `OpenAPISetup`, `TemplateService`).

O problema é que `Pyweber` (~900 linhas), `websocket.py` (~900), `routes.py` (~900) e `openapi.py` (~1000) continuam a concentrar demasiadas razões para mudar. Por cima disso, o estado é de processo, não de aplicação: `EventBook`, `sessions`, `handoff_registry`, `RoleRegistry`, o engine SQLAlchemy e o rate limiter são singletons. Duas apps no mesmo interpretador partilham papéis, sessões e eventos.

**Impacto.** Manutenção de um bug de WebSocket obriga a ler o servidor, o protocolo, a sessão e o diff de DOM no mesmo ficheiro. Escalar para vários workers deixa de ser uma configuração e passa a ser um desenho diferente (Redis + sticky sessions), que hoje não é o defeito.

**Prioridade: Alta** para os singletons em produção multi-processo; **Média** para o tamanho das classes.

Direção para 2.0: um `AppState` injectado (sessões, papéis, engine, limiter) e o servidor de sockets só no modo de desenvolvimento. O caminho ASGI (`uvicorn main:app`) já existe e é o que a documentação de deploy recomenda.

---

## 2. API do framework

A API reativa é coerente com a ideia do produto: `Element`, `Template`, eventos Python, `e.update()`. Rotas no estilo Flask (`@app.route`), OpenAPI no estilo FastAPI e `login_required` no estilo Django convivem sem um modelo mental único.

O que devia encolher:

- `Route.__init__` aceita grupo, métodos, middleware, status, content-type, OpenAPI, CSRF e `**kwargs` de uma vez. Um `RouteSpec` (ou parâmetros só no decorator) tornava a assinatura aprendível.
- `childs` em vez de `children`, `normaize_path` (ainda exportado, com aviso de remoção em 2.0) e `strem_stats.py` ao lado de `stream_stats.py`.
- `JWTAlgorithms` é só um enum. O próprio módulo diz que não há encode, decode nem verify. Quem importa isto à espera de PyJWT leva um falso positivo de funcionalidade.
- Mensagens de erro misturam português e inglês (`must be a Request instances`).

**Prioridade: Média** (DX, não segurança). A API é utilizável; não é estável o suficiente para ser o contrato de uma major sem uma limpeza explícita.

---

## 3. Segurança

Comparado com o [OWASP ASVS](https://owasp.org/www-project-application-security-verification-standard/) e com o [Cheat Sheet Series](https://cheatsheetseries.owasp.org/), o quadro é misto. O que está bem feito não é cosmético.

**Já presente.** CSRF double-submit activo por defeito (`pyweber_csrf`, campo `_csrf`, header `X-CSRF-Token`), assinatura HMAC-SHA256 com `hmac.compare_digest`. Cookie de sessão `HttpOnly` + `SameSite=Strict`. Headers `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy`, CSP com `frame-ancestors 'none'`, HSTS quando `https_enabled`. CORS só reflecte origens da allowlist (nunca `*`) e exige credenciais só nesse caso. `safe_join` recusa segmentos absolutos e `..` que saiam da raiz. `Window.open` / redirects absolutos passam por `ensure_safe_redirect_url`. `/docs` e `/openapi.json` não se registam em produção salvo `expose_in_production`. Corpo limitado a 10 MiB com resposta 413. Traceback completo não vai para o HTML em produção. Queries passam pelo SQLAlchemy, sem API de SQL concatenado no framework.

### Crítica — frame WebSocket sem teto (WS-01)

`receive_frame` aceita um comprimento de 64 bits e lê esse número de bytes:

```python
# pyweber/connection/websocket.py
elif payload_len == 127:
    extended_payload = await self.read_exact(8)
    payload_len = int.from_bytes(extended_payload, byteorder='big')

masking_key = await self.read_exact(4)
payload = await self.read_exact(payload_len)
```

**Impacto.** Negação de serviço por memória no servidor de `pyweber run`. O uvicorn tem limites próprios; este caminho é o defeito do CLI. OWASP: unbounded resource consumption.

**Correcção.** Recusar `payload_len` acima de um teto (por exemplo 1 MiB, alinhado com `max_body_size`) antes de `read_exact`, e fechar a ligação.

### Alta — o id de sessão do cliente passa à frente do cookie (WS-02)

`get_session_id` documenta que o id do cliente não é confiável. `bind_session_id` faz o contrário se o id já estiver na tabela:

```python
# pyweber/connection/websocket.py
if connection_id and connection_id in sessions.all_sessions:
    return connection_id, False

if client_session_id and client_session_id in sessions.all_sessions:
    return client_session_id, False

resolved = self.get_session_id(
    session_id=client_session_id,
    cookies=cookies or {},
)
```

O id é `token_urlsafe(32)`, portanto não é adivinhável. É enviado ao browser em `setSessionId` e vive em JavaScript, fora do cookie `HttpOnly`. Quem o obtiver (XSS, extensão, máquina partilhada, frame WS sem TLS) dispara os handlers Python dessa sessão. CWE-384.

**Correcção.** A ligação só é válida se `unsign_value(cookie)` for igual ao id reivindicado. O `connection_id` já preso a esse socket pode continuar a resolver a corrida do handshake, desde que tenha nascido dessa verificação.

### Alta — handoff consumido cedo (HO-01)

O token é um `uuid4` num `<meta>`, e `consume` faz `pop` antes de verificar rota e TTL (`pyweber/models/handoff.py`). Quem vir o HTML nos 300 segundos fica com a instância `Template`, handlers incluídos. Uma rota errada apaga o handoff da vítima.

**Correcção.** Ligar o token ao `pyweber_sid` e só remover a entrada depois das validações.

### Alta — injeção no Set-Cookie (CK-01)

```python
# pyweber/models/cookies.py
cookie = f'{cookie_name}={cookie_value}; Path={path};'
```

`login_user` mete JSON (id, papéis, `data`) nesse valor. Um campo com `;` ou `\r\n` parte o cabeçalho. RFC 6265 exige codificação.

```python
from urllib.parse import quote

cookie = f"{quote(cookie_name, safe='')}={quote(cookie_value, safe='')}; Path={path};"
```

Recusar `\r`, `\n` e `;` no nome. `SameSite=None` nem é aceite (só `Strict` e `Lax`); o defeito é o mais seguro. Falta o prefixo `__Host-` (`Path=/`, `Secure`, sem `Domain`).

### Alta — Secure depende da config (CK-02)

`secure` vem de `https_enabled()`, cujo defeito é `false`. Atrás de um reverse proxy TLS o cookie segue sem `Secure`. A resposta ainda escreve `X-Forwarded-Proto`, que é cabeçalho de pedido, não de resposta, e não há lista de proxies confiáveis.

**Correcção.** Ler `X-Forwarded-Proto` só de proxies configurados e falhar o arranque em produção se o cookie de sessão puder sair sem `Secure`.

### Alta — autenticação sem revogação (AU-01)

`pyweber_user` é HMAC, `HttpOnly`, `SameSite=Strict`, 14 dias. `logout_user` só expira o cookie desse browser. Não há store de servidor, rotação no login, idle timeout, nem invalidação quando os papéis mudam. Permissões em `data['permissions']` viajam no cookie até expirar. Os nomes de papel são resolvidos no `RoleRegistry` a cada pedido — isso está certo.

`hash_password` usa PBKDF2-HMAC-SHA256 com sal e 260 000 iterações (`pyweber/auth/passwords.py`). OWASP 2023 pede 600 000 para este algoritmo, ou Argon2id. Não há teto de comprimento: uma password enorme é negação de serviço de CPU. **Prioridade: Média** para o algoritmo (PW-01); **Alta** para a ausência de revogação em sistemas financeiros.

### Alta — scheme sem verify (AU-02)

Não existe implementação JWT. `HTTPBearer` só extrai o token. Se `verify` for `None`, qualquer credencial não vazia passa:

```python
# pyweber/models/security.py
user = None
if scheme.verify is not None:
    result = self._call_verify(scheme.verify, credentials, request, scopes)
    ...
    if result is not True:
        user = result

auth_contexts.append(
    AuthContext(
        scheme=scheme_name,
        credentials=credentials,
        user=user,
        scopes=list(scopes or []),
    )
)
```

Os scopes OpenAPI são entregues ao callback e não são impostos pelo framework. Scheme sem `verify` devia falhar fechado. `APIKeyQuery` mete segredos na query string (logs, Referer). É uma opção; não deve ser o exemplo da documentação.

RBAC (`register_roles`, `*`, `ns:*`, `@permission_required`) é claro e testado. É um mapa em memória, sem auditoria, sem multi-tenant e sem revalidação contra a base.

### Alta — rate limit (RL-01)

Defeito `rate_limit_enabled = false`. O balde é um `dict` sem evicção, chave `ip:path`. Atrás de um proxy todos caem no IP do proxy (um utilizador esgota a quota de todos, ou um atacante distribui chaves e enche a RAM). Não há limite por rota nem por conta. OWASP: brute force e denial of service.

### XSS (XSS-01)

O texto do elemento é escapado com `html.escape` quando `sanitize=True` (defeito). Isto cobre o caso comum. Não cobre:

- o nome do atributo, emitido cru (`onerror`, ou uma chave com aspas);
- `href="javascript:..."` (não tem caracteres que o escape altere);
- o corpo de `<script>` e `<style>`, de propósito, para não partir `if (n > 0)`.

```python
# pyweber/models/element.py
for key, value in element.attrs.items():
    if value is not None:
        if value and value not in [True, False]:
            html += f' {key}="{esc_attr(value)}"'
        else:
            html += f" {key}"

escape_text = element.sanitize and tag not in {'script', 'style'}
```

**Correcção.** Allowlist de nomes de atributo, recusar `on*`, e bloquear `javascript:`, `data:` e `vbscript:` em `href` / `src`. Conteúdo de utilizador dentro de `script` tem de ser proibido pela API, não só pela documentação.

### CSRF (CSRF-01)

CSRF está bem desenhado para o pedido clássico (cookie + token, métodos inseguros, isenção quando há `Authorization` e não há `Cookie`). Duas falhas de fronteira:

- `path.startswith(prefix)` faz com que `/api` isente `/apiv2`;
- todo o prefixo `/_pyweber/` está isento, incluindo `POST /_pyweber/file_chunk`, que completa um futuro de upload se o `file_id` for conhecido.

O cookie CSRF não é `HttpOnly` (o formulário injeta o token no servidor; o JS do Swagger lê o cookie). **Prioridade: Média.**

### Clickjacking e CSP (CSP-01)

Clickjacking está coberto (`X-Frame-Options: DENY` e `frame-ancestors 'none'`). A CSP por defeito é fraca para XSS:

```python
# pyweber/utils/security.py
DEFAULT_CSP = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' https:; "
    ...
    "frame-ancestors 'none'; "
)
```

`unsafe-inline` e `https:` existem para Bootstrap e CDNs. Num banco isso devia ser opt-in. **Prioridade: Média.**

### Outros controlos

- **SSRF.** O framework não faz pedidos HTTP de saída. O redirect no browser está na allowlist. Não há achado de SSRF no núcleo.
- **Path traversal nos estáticos.** `safe_join` está correcto. O loader de templates não usa essa jail (secção 6).
- **Debug (CFG-01).** Com `session.env=development` (valor do `config.toml` gerado) a página 500 inclui a mensagem da exceção e a linha. O traceback completo vai para o log, o que é adequado. Produção só recusa o placeholder `TOKEN_HEX` se `PYWEBER_ENV` for `production` ou `prod`. Esquecer a variável deixa a app em modo de desenvolvimento, à escuta em `0.0.0.0`. **Prioridade: Alta.** Falhar o arranque se o host for público e o ambiente não for produção.
- **Headers (HDR-01).** `Server: Pyweber/1.0`. Faltam `Permissions-Policy`, `Cross-Origin-Opener-Policy` e `Cross-Origin-Resource-Policy`. **Prioridade: Baixa.**
- **Validação de input.** Conversão de parâmetros de rota existe (`ParameterConversionError` → 400). Não há um modelo de validação obrigatório (Pydantic é opcional, via OpenAPI). O corpo JSON faz `json.loads` sem schema.
- **CLI.** Em Windows, `subprocess.run(['python', file], shell=True)`. Com `shell=True`, um caminho de projeto com metacaracteres é interpretação da shell. **Prioridade: Média.** Passar a lista e `shell=False`.

---

## 4. Performance

Gargalos observáveis no código, sem benchmark:

| Zona | O que o código faz | Prioridade |
|---|---|---|
| Event loop | Handler síncrono é chamado directo em `_process_templates` | Alta |
| HTTP embutido | `Connection: Close` em todas as respostas; cada pedido abre e fecha TCP | Alta |
| WebSocket | Unmasking byte a byte em Python; `asyncio.sleep(0.01)` no read e no iterador | Alta |
| DOM | Cada mensagem com HTML faz parse completo e `merge_client_dom` | Média |
| Render | `to_html` reconstrói a árvore por concatenação de strings | Média |
| Sessão | Defeito em memória; o snapshot Redis guarda o HTML inteiro | Média |
| Gzip | Compressão síncrona no pedido, nível 6, a partir de 500 bytes | Baixa |
| ORM | Pool 5, sem `pool_pre_ping`, sem cache de queries | Média |

Não há cache de aplicação. `__cache_templates` é lido e limpo, e não há escrita — código morto, não uma fuga entre utilizadores. O diff de template (em vez de reenviar a página) é o ponto mais maduro desta área. `lxml` é extra opcional; o defeito é `html.parser`, correcto para serverless e lento em páginas grandes.

O caminho certo em produção é ASGI com uvicorn/gunicorn, já documentado. O servidor de sockets com pool de 100 threads e busy-wait não deve servir tráfego crítico.

---

## 5. ORM

É um extra (`pyweber[db]`): `DeclarativeBase`, `create_async_engine`, `session_scope` com commit opcional e rollback na exceção, `get` / `scalars` por cima da sessão actual. Migrações via `pyweber db` a chamar Alembic. Não há concatenação de SQL no framework; a parametrização é a do SQLAlchemy. Isso evita a classe de bugs de ORM caseiro.

Falhas para um ERP:

- Sem URL, `load_database_settings` cai em `sqlite+aiosqlite:///:memory:`. O `config.toml` de projeto traz o mesmo defeito. Reiniciar apaga os dados. **Prioridade: Alta** (integridade operacional).
- `auto_commit` defeito `false` está certo. Não há isolamento explícito, savepoints documentados, nem `pool_pre_ping`.
- O modelo não acrescenta constraints, soft delete, auditoria nem paginação. `__tablename__` é o nome da classe em minúsculas.
- `echo=True` regista SQL. Tem de ficar desligado em produção (já é o defeito).

**Prioridade geral do desenho: Média.** Para banca, usar SQLAlchemy/Alembic directamente e tratar esta camada como conveniência, até haver URL obrigatória e testes de migração.

---

## 6. Sistema de templates

Componentes (`Form`, inputs) e reutilização por subclasses de `Element` são o ponto forte de DX. O escape por defeito do texto está correcto e há testes.

Limites:

- Sanitização incompleta (secção 3, XSS-01). **Alta.**
- `Element.read_file` abre qualquer caminho que termine em `.html` através de `LoadStaticFiles` sem `allowed_roots`. Com raízes vazias, `_is_allowed` devolve `True`. **Média** (inclusão de ficheiro se o caminho vier de input).
- `merge_client_dom` copia `value` / `checked` / `disabled` e enxerta subárvores cujo uuid o browser inventou. Os handlers Python passam a ver estado que o cliente controla. Autorização tem de viver no servidor, nunca no DOM. **Média**, e é estrutural neste modelo reativo.
- Não há partials com cache, nem herança de layout para além de injectar head/script do framework. Cada `e.update()` serializa de novo.

---

## 7. Routing

Flexível: parâmetros `{id}`, grupos, `RedirectRoute`, middleware `before` / `after` / onion, `csrf_exempt`, metadados OpenAPI no decorator. A organização por `RouteManager` é clara. A documentação em `docs/routing/` existe.

Não há versionamento (`/api/v1` é só uma string). Não há dependências por rota no sentido FastAPI, nem rate limit por rota. Middleware é uma lista de callables, sem pipeline tipado de `Request → Response`.

**Prioridade: Média** para versionamento e para partir `routes.py`. A funcionalidade actual chega para aplicações médias.

---

## 8. Sessões e cookies

Há dois sistemas:

1. `pyweber_sid` — sessão reativa (DOM, eventos). Assinada, `HttpOnly`, `SameSite=Strict`, `Secure` só se `https_enabled`. Store em memória ou Redis (TTL 3600 no config).
2. `pyweber_user` — login. O mesmo esquema de assinatura, 14 dias, papéis dentro do payload. Sem store de servidor.

Isolamento entre utilizadores no caso reativo depende do id não ser aceite de outro socket (hoje é — WS-02). O Redis guarda o HTML da template; com o mesmo segredo, os workers partilham snapshots, não o `EventBook` local. Handlers continuam a ser objectos Python do processo que criou a sessão. Sticky session continua necessária para a reatividade, mesmo com Redis.

Não há regeneração de id no login. O id de login é outro cookie, por isso fixation clássica do `sid` não rouba a identidade — rouba a UI e os handlers. **Prioridade: Alta** no conjunto WS-02 + ausência de revogação.

Codificação e flag `Secure`: secção 3.

---

## 9. Uploads

Tamanho: o corpo HTTP pára nos 10 MiB. Não há limite por ficheiro distinto do corpo.

HTTP multipart: `secure_filename` fica `uuid + nome` com caracteres reduzidos a `[A-Za-z0-9_.-]`, o que corta path traversal no nome. O framework não grava em disco; quem grava é a aplicação, e não há helper com jail de directório.

MIME: `validate_uploads` vem desligado. Quando se liga, o retorno é ignorado e `allowed` não é passado, logo `validate_upload` não levanta:

```python
# pyweber/models/field_storage.py
if validate:
    from pyweber.utils.mime import validate_upload

    validate_upload(
        field.value if isinstance(field.value, bytes) else b'',
        filename=field.filename,
        declared_type=declared,
    )
```

A heurística trata qualquer UTF-8 como `text/plain` e qualquer ZIP como docx/xlsx. SVG, HTML e polyglots não estão no modelo de ameaça. O caminho WebSocket (`insert_values`) cria `File` com o nome enviado pelo browser, sem `secure_filename` nem sniff. **Prioridade: Alta.**

Contrato que a flag devia ter:

```python
validate_upload(
    data,
    filename=field.filename,
    declared_type=declared,
    allowed=["image/png", "image/jpeg", "application/pdf"],
)
```

E só então guardar com `safe_join(upload_root, secure_filename(...))`, fora da árvore de estáticos.

---

## 10. Developer experience

Pontos fortes reais: CLI `create-new` / `run --reload`, hot reload com restore se o import falhar (changelog 1.8.2), cliente de teste com helpers CSRF, cobertura mínima 88%, guias de auth, deploy, sessões e base de dados, mensagens de depreciação com versão de remoção.

Fricção: typos na API pública, erros bilingues, `JWTAlgorithms` que não assina, defeitos perigosos silenciosos (`:memory:`, `env=development`, `validate_uploads` que não valida), e um modelo mental que não é Flask nem React. Autocomplete existe onde há type hints; muitos atributos usam anotações antigas (`dict[str, (str, float)]`) que o type checker não entende. A curva é baixa para um contador e alta para auth + ORM + WebSocket em produção.

**Nota de DX: 6.5.** Boa para um framework jovem com documentação; fraca como plataforma em que um programador novo não dispara um defeito inseguro.

---

## 11. Comparação

| | Onde o PyWeber está à frente | Onde ainda tem de evoluir |
|---|---|---|
| Django | Reatividade sem JavaScript, hot reload, diff de DOM, CSRF ligado sem apps extra | Auth de servidor, admin, forms, migrações, ORM, revisão de segurança de anos |
| Flask | Headers, CSRF, RBAC, OpenAPI e sessões assinadas de origem | Ecossistema, WSGI maduro, extensões, clareza do núcleo pequeno |
| FastAPI | UI reativa no mesmo processo Python | Pydantic obrigatório, DI, async de ponta a ponta, OpenAPI gerado a partir de tipos |
| Laravel | Modelo componente + evento num só language | Policies, queues, encryption, notificações, convenção de pastas |
| ASP.NET Core | Arranque com pouca configuração | Data Protection (rotação de chaves), antiforgery, Identity, Kestrel, DI |

Para um CRUD empresarial, Django ou ASP.NET Core continuam a escolha com menos risco. O PyWeber ganha quando o produto é uma UI viva controlada em Python e a equipa aceita operar o WebSocket como parte do modelo de segurança.

---

## 12. Funcionalidades ausentes

Padrão hoje em frameworks usados em produção crítica, e ausente aqui:

- Store de sessão de login com revogação, rotação e idle timeout
- Argon2id, política de password, bloqueio de conta
- JWT com allowlist de algoritmos (ou remoção do enum)
- 2FA, OAuth/OIDC como cliente
- Filas e tarefas em background
- i18n e timezones
- Admin gerado
- Validação de schema obrigatória no corpo
- Versionamento de API
- Métricas, tracing, request id, logs estruturados
- Proxies confiáveis
- Keep-alive / HTTP/2 no servidor próprio (ou retirá-lo de produção)
- Permissões por objecto (não só papel global)
- Trilho de auditoria
- Storage de uploads com raiz, cota e antivírus
- Testes de migração e fixtures de base de dados
- `Permissions-Policy` e CSP com nonce

---

## 13. Roadmap

### 1.8.5 — correções

1. Teto de frame WebSocket e fecho da ligação.
2. `bind_session_id` só aceita o id do cookie assinado.
3. Percent-encoding em `Set-Cookie`; recusar CRLF.
4. `validate_uploads` com allowlist obrigatória; o mesmo no caminho WS.
5. Scheme de segurança sem `verify` falha fechado.
6. Arranque em produção falha se `env` não for production, se o segredo for placeholder (já acontece), ou se `Secure` estiver desligado num bind não-local.
7. Handoff: validar rota, TTL e `sid` antes do `pop`.
8. `subprocess` sem `shell=True`.

### 1.9 — controlos de produção

Argon2id e teto de password. Sessão de login no servidor (Redis já é dependência opcional) com `logout` a invalidar todas as cópias. Rate limit com máximo de chaves e IP só via proxy confiável. CSP sem `unsafe-inline` por defeito. `Origin` no upgrade WebSocket. Jail de `templates/`. Allowlist de atributos HTML. Rate limit no login. Pong correcto (opcode `0xA`).

### 2.0 — arquitetura

Partir `Pyweber`, `websocket.py` e `routes.py`. Estado por instância de app. Servidor embutido marcado como desenvolvimento; produção só ASGI. Remover `childs`, `normaize_path`, `strem_stats` e `JWTAlgorithms` se não houver implementação. DI simples para db, auth e limiter. Versionamento de rotas. Contrato de "o DOM do cliente não é fonte de autorização" na API, com os campos sincronizados reduzidos a value/checked.

---

## 14. Refatorações

- **Duplicado:** `strem_stats.py` / `stream_stats.py`; lógica de cookie repetida entre `CookieManager`, pipeline e `auth/session.py`; leitura de config booleana (`csrf_enabled`, `rate_limit_enabled`, `gzip`, `https_enabled`) copiada várias vezes.
- **Classes grandes:** `Pyweber`, `WebsocketServer` + `BaseWebsockets` + `WebsocketManager` no mesmo módulo, `Route` / `RouteManager`, `OpenAPIBuilder`, `ElementConstrutor.to_html`.
- **Funções densas:** `get_response` / `_produce_response`, `receive_frame` + `manage_connection`, `to_html`, `enforce` do `SecurityEnforcer`.
- **Módulos a separar:** protocolo WS (frames) vs sessão vs eventos; geração OpenAPI vs runtime de security; CLI de certificados vs CLI de projecto.
- **Arquitetura:** singletons → objectos no `app`. Handlers síncronos para um executor com limite, ou exigência de `async def` em 2.0.

---

## 15. Qualidade geral

Escala 0–10. A barra de um sistema crítico fica à volta de 8. Média das nove notas: **5.7**.

| Dimensão | Nota | Justificação |
|---|---|---|
| Arquitetura | 6.0 | Pacotes claros e serviços já extraídos. God objects e singletons limitam multi-app e multi-worker. |
| Segurança | 5.0 | CSRF, HMAC, jail de estáticos, headers e open-redirect são trabalho a sério. WS sem teto, sessão desligada do cookie, cookie sem encoding e sanitização incompleta impedem nota mais alta. |
| Performance | 4.5 | Connection close, handlers síncronos no loop, unmasking e parse de DOM por mensagem. O diff de template é o contra-peso. |
| Escalabilidade | 4.0 | Cookie de login escala; a sessão reativa não, sem sticky session. Redis é opcional e não move os handlers. |
| Qualidade do código | 6.0 | Testes, cobertura 88%, changelog honesto (1.8.3 corrigiu cache público de JSON). Typos, código morto e ficheiros de 900 linhas. |
| API | 6.5 | Agradável no caso reativo. Assinaturas grandes e nomes inconsistentes. |
| DX | 6.5 | CLI, reload, docs e cliente de teste. Defeitos inseguros fáceis de deixar ligados. |
| Documentação | 7.0 | Guias de deploy, auth, sessões e base de dados, mais site. Não chega à referência do Django, e o enum JWT promete mais do que entrega. |
| Maturidade | 5.5 | 1.8.3 com ritmo de correções de segurança visível no changelog. Ainda não tem o histórico de exploração e de operação dos frameworks com que foi comparado. |

Para um produto interno de UI reativa, com ASGI, `PYWEBER_ENV=production`, segredo forte, HTTPS terminado de forma consciente e sem confiar no DOM para autorização, o framework é utilizável depois da 1.8.5. Para banca ou setor público, não o colocaria em produção crítica até a 1.9 fechar revogação de sessão, uploads e a CSP.
