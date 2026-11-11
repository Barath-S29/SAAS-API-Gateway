# Identity API Contract (V1)

Account signup, login, and API-key management. This contract is written
before the code. If implementation shows a problem, the change is
explained, approved, and made here first.

Gateway (weather) endpoints get their own contract in Phase 3.

## Conventions

- Base path `/api/v1`. JSON request and response bodies (UTF-8).
  Timestamps are ISO 8601 UTC (`2026-11-09T14:03:21Z`). IDs are UUID strings.
- Two credential types, never interchangeable:
  - **Access token (JWT)** for account management:
    `Authorization: Bearer <access_token>`.
  - **API key** for gateway calls (header name fixed in the Phase 3
    contract; `X-API-Key` is proposed).
- Every response that contains a secret (signup, login, key creation)
  sends `Cache-Control: no-store`.
- Every error response has this shape and nothing more:

  ```json
  { "error": { "code": "machine_readable_code", "message": "Generic, human-readable text" } }
  ```

  Validation errors add `"details": [{ "field": "password", "issue": "too short" }]`.
  `issue` text never echoes submitted values. A `request_id` field is added
  when the logging foundation lands (additive, non-breaking).
- `401` responses include `WWW-Authenticate: Bearer`.
- No stack traces, SQL, or internal identifiers in any error.

## Endpoints

| Method | Path | Auth | Success |
|---|---|---|---|
| POST | `/api/v1/auth/signup` | none | `201` |
| POST | `/api/v1/auth/login` | none | `200` |
| POST | `/api/v1/keys` | access token | `201` |
| GET | `/api/v1/keys` | access token | `200` |
| DELETE | `/api/v1/keys/{key_id}` | access token | `204` |

### POST /api/v1/auth/signup

Request:

```json
{ "email": "dev@example.com", "password": "at-least-12-characters" }
```

- `email`: valid address, max 254 characters, trimmed and lowercased by the server.
- `password`: 12 to 128 characters. Length is the only rule (no composition rules).

Success `201`:

```json
{
  "tenant": { "id": "uuid", "email": "dev@example.com", "plan": "free", "created_at": "..." },
  "api_key": { "id": "uuid", "key": "gw_live_...", "key_prefix": "gw_live_xxxxxxxx", "created_at": "..." }
}
```

`api_key.key` is the only time the plaintext key is ever returned.

| Status | Code | When |
|---|---|---|
| 409 | `email_already_registered` | email exists (enforced by the unique constraint, not a prior lookup) |
| 422 | `validation_error` | malformed email, password length, missing fields |

Behavior: the password is hashed (argon2id, off the event loop) first. The
tenant (Free plan) and the first API key are then inserted in **one
transaction**. A unique violation rolls back both and returns `409`.

### POST /api/v1/auth/login

Request: `{ "email": "...", "password": "..." }`. Only shape is validated
(strings, password max 128), so a changed password policy never locks out
existing tenants.

Success `200`:

```json
{ "access_token": "<jwt>", "token_type": "bearer", "expires_in": 900 }
```

| Status | Code | When |
|---|---|---|
| 401 | `invalid_credentials` | unknown email, wrong password, **or deactivated tenant**. Always the message `Invalid email or password`. |
| 422 | `validation_error` | wrong shape or types |

Unknown emails still run a full argon2 verification against a precomputed
dummy hash (same parameters as real hashes, generated once at startup), so
response time does not reveal whether an email exists.

### POST /api/v1/keys

Auth: access token. No request body.

Success `201`: `{ "id": "uuid", "key": "gw_live_...", "key_prefix": "gw_live_xxxxxxxx", "created_at": "..." }`

| Status | Code | When |
|---|---|---|
| 401 | `token_expired` / `invalid_token` | see Access token below |
| 403 | `account_disabled` | tenant deactivated |
| 409 | `key_limit_reached` | tenant already has `MAX_ACTIVE_KEYS_PER_TENANT` active keys (default 5) |

Behavior: the key is generated and hashed **before** the transaction.
Inside it: lock the tenant row (`SELECT ... FOR UPDATE`), **then** count
active keys, then insert. Locking before counting is what makes concurrent
requests unable to exceed the cap.

### GET /api/v1/keys

Auth: access token.

Success `200`:

```json
{ "keys": [ { "id": "uuid", "key_prefix": "gw_live_xxxxxxxx", "is_active": true,
              "created_at": "...", "revoked_at": null } ] }
```

Newest first. Includes revoked keys. Never returns a key or hash. Only the
authenticated tenant's keys are ever returned. Errors: `401`, `403` as above.

### DELETE /api/v1/keys/{key_id}

Auth: access token. Revokes the key (`is_active=false`, `revoked_at` set).

| Status | Code | When |
|---|---|---|
| 204 | none | revoked, **or already revoked** (DELETE is idempotent; `revoked_at` is not overwritten) |
| 404 | `key_not_found` | no such key **or the key belongs to another tenant** (404, not 403, so other tenants' keys are never confirmed to exist) |
| 422 | `validation_error` | `key_id` is not a UUID |

## Access token

- JWT, **HS256**, verified with an allowed-algorithm list pinned in code.
- Claims, all required: `sub` (tenant UUID), `iss`, `aud`, `iat`, `exp`.
  Nothing else. No emails, no secrets.
- Lifetime 15 minutes (`JWT_ACCESS_TTL_SECONDS`, default 900). No refresh tokens in V1.
- Verification order on every account endpoint: signature and algorithm,
  `exp`, `iss`, `aud`, required claims, then the database: the tenant must
  exist and be active.

| Condition | Status | Code |
|---|---|---|
| missing, malformed, bad signature, wrong `iss`/`aud`, missing claims, unknown tenant | 401 | `invalid_token` |
| expired | 401 | `token_expired` |
| valid token, tenant deactivated | 403 | `account_disabled` |

## Gateway authentication (preview, finalized in Phase 3)

| Condition | Status | Code | Counts toward |
|---|---|---|---|
| missing, unknown, or revoked API key | 401 | `invalid_api_key` | `auth_failures_total` (metric only, no `usage_logs` row) |
| valid key, tenant deactivated | 403 | `account_disabled` | metric only |

The key, tenant, and plan are resolved in one query, so the active checks
cost no extra round trip.

## Configuration introduced

| Setting | Secret? | Default |
|---|---|---|
| `JWT_SECRET_KEY` | **yes**, 32+ random bytes, `.env` only | none (startup fails if missing) |
| `JWT_ISSUER` | no | `saas-api-gateway` |
| `JWT_AUDIENCE` | no | `gateway-account-api` |
| `JWT_ACCESS_TTL_SECONDS` | no | `900` |
| `MAX_ACTIVE_KEYS_PER_TENANT` | no | `5` |

## Security requirements

- Secrets (JWT secret, database password, upstream API key) come only from
  the environment. Never in code, never committed, never logged.
- Never logged: passwords, password hashes, plaintext API keys, JWTs,
  `Authorization` headers, or auth request bodies. Logs reference keys by
  `api_key_id`, never by prefix.
- Passwords: argon2id. API keys: 32 random bytes from the OS CSPRNG, stored
  as SHA-256 plus a lookup prefix, compared in constant time.
- Responses containing secrets are `Cache-Control: no-store`.
- Error messages are generic and identical across the cases listed above.

## Invariants

- A tenant can only list or revoke its own keys.
- A plaintext key exists in exactly one response and nowhere else.
- A tenant never exceeds the active-key cap, even under concurrent requests.
- A deactivated tenant cannot obtain a token or use an existing one.
- Signup never leaves a tenant without a first key, or a key without a tenant.

## Future (not V1)

- `POST /auth/refresh` and `POST /auth/logout` (with the frontend)
- Email verification, a generic `202` signup response, password reset
- Idempotency keys for key creation
- Key list pagination, `GET /me`, breached-password checks, per-key scopes

## Known V1 limitations

- Signup `409` reveals which emails are registered.
- No server-side logout: a token is valid until it expires (at most 15 minutes).
- A lost signup response means a created, never-seen key. The tenant logs in
  and creates another, and the cap bounds the damage.
- Revoked keys accumulate, and the key list is not paginated.