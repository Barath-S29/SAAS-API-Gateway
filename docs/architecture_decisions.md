# Architecture Decisions - V1

Locked-in decisions for the SaaS API Gateway, with the reasoning and
the trade-off accepted. Anything not listed here is either undecided
(see "Open items") or out of V1 scope.

## Scope

1. **One upstream provider (OpenWeatherMap), no provider abstraction.**
   V1 proves the pipeline end-to-end against one real provider. The
   `endpoint` column on `usage_logs` is the only seam left for V2.

## Identity and security

2. **1 user = 1 tenant.** Auth fields (`email`, `password_hash`) live on
   `tenants`; no `users` table until multi-user accounts are a real need.
3. **Passwords: argon2id via `argon2-cffi`** (replaces Passlib from the
   original spec). Memory-hard, no 72-byte input limit, actively
   maintained. Cost: memory pressure on a small instance, so
   signup/login is a DoS surface (hashing must not run on the event loop).
4. **Emails are stored lowercase**, enforced by a CHECK constraint.
   No email verification and no password reset in V1.
5. **API keys: SHA-256 hash + indexed plaintext prefix.** Raw key shown
   once, never stored or logged. Verification uses a constant-time
   comparison. A fast hash is correct here because keys are
   high-entropy; slow hashing is for low-entropy passwords.

## Billing and usage

6. **Usage-based billing.** `amount = billable_requests x unit_price`,
   computed in integer micro-dollars and rounded to cents once per invoice.
7. **Plans are immutable.** A change is a new row. Invoices snapshot
   `unit_price_micros_charged`. Plan changes are admin-only in V1.
   Seed plans: Free (100/day, $0) and Pro (5,000/day, $0.0005/request).
8. **What counts as usage.** Invalid/missing key (401) and rate-limited
   (429) requests produce metrics only, no `usage_logs` row. Cache hits
   are billed like upstream misses (`cache_hit` is recorded).
9. **Usage logging via FastAPI `BackgroundTasks` writing to Postgres.**
   Known limitation: an event is lost if the process crashes between
   response and write.
10. **Billing period: fixed UTC calendar month.** Idempotency comes from
    `UNIQUE (tenant_id, billing_period_start, billing_period_end)`; the
    job always inserts and treats a unique violation as "already billed".
    Invoice `status` is `pending` -> `generated` | `failed`; no automatic
    retry for stuck `pending` rows in V1.

## Gateway behavior

11. **Rate limiting: sliding window counter** as a single atomic Redis
    Lua script. "Per day" means a rolling 24 hours, not a calendar day.
12. **Cache key = normalized upstream query parameters, never the
    tenant.** Keying by tenant would make every tenant a miss for
    everyone else.

## Deployment

13. **Single EC2 instance** runs Nginx, API, Celery worker, Celery beat,
    and Redis; RDS and S3 are managed services. Splitting the worker onto
    its own instance is a production step, not V1.

## Open items

- Whether upstream 5xx/timeouts vs client-caused 4xx are billable
  (decide in Phase 3 with upstream error handling).
- Cache TTL, to be verified against OpenWeatherMap's documented update
  cadence before hardcoding (Phase 5).
- Nginx rate limit on signup/login: optional hardening.

## Known V1 limitations

- Usage events can be lost on a crash (decision 9).
- No password reset or email verification; free-tier quota farming via
  fake accounts is possible.
- `usage_logs.created_at` is set at write time, so a request near a
  period boundary can land in the next period.