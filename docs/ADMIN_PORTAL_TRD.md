# Rather Know — Admin Portal TRD (organisations, white-labelling, users)

**Status:** requirements locked with the product owner, August 2026. Build in the RK repo.
**Relationship to the consumer product:** this is a SECOND identity plane laid on top of an anonymous-by-default consumer product. Nothing in this document weakens the consumer boundary in HANDOFF §5c.

---

## 1. Non-negotiable boundaries

1. **Consumers stay anonymous by default.** Taking any mirror never requires an account, an email, or a name. The FAQ/landing copy changes from "no account" to "**no account required**" — that is the only copy change this feature is allowed to cause.
2. **Consumer accounts are OPTIONAL and opt-in** (Phase 2, see §7): their only purposes are (a) keeping results across devices/browsers, (b) holding report entitlements (§5c grants). Never a gate in front of an assessment or a result.
3. **Organisations see COUNTS ONLY — decided.** An org never sees an individual's answers, results, or identity. Not with consent, not on request. If this is ever revisited it is a new product decision, not a portal setting.
4. **Payment/identity separation from §5c still holds**: entitlements attach to sessions/tokens; account linkage is the consumer's choice.

## 2. Roles

| Role | Who | Gets |
|---|---|---|
| **Super-admin** | Product owner | Everything in §3 |
| **Org-admin** | A partner org's own people (coaches, recruiters, HR) | Self-serve slice in §4 |
| **Consumer account** (optional, Phase 2) | Any taker who opts in | §7 only — NOT a portal role |

## 3. Super-admin portal (P0)

Mirror the MM admin portal pattern (reference: MM `routes/admin.py`, `org.py`, `user_auth.py`, `invitations.py`; frontend `pages/admin/*` — patterns, not code-paste):
- **Organisations**: create / edit / archive. Fields: name, logo (object storage), partner code(s), contact email, notes, status.
- **Org users**: invite by email (time-limited invite token), deactivate/reactivate, **trigger password reset**, change role within org, view last-login.
- **Partner codes**: issue/revoke `/r/{code}` codes per org; a code maps to exactly one org; codes are revocable without deleting history.
- **Counts dashboards**: per org and global — starts/completions per instrument, per day/week; Closeness pilot counter (progress toward the 300-completion gate).
- **Audit log**: every admin/org-admin auth event and mutating action (who, what, when, before/after where cheap). Read-only, filterable.
- **Entitlement lookup** (once commerce ships): find an entitlement by token/receipt to support refunds — WITHOUT joining to assessment content.
- Explicitly ABSENT: any browser over assessment responses/results. The anonymous data plane has no admin UI.

## 4. Org-admin portal (P1)

- **Their branding**: org name + logo upload; preview of the branded assessment intro.
- **Their link**: the `/r/{code}` URL, copyable, with a QR.
- **Their counts**: starts/completions per instrument via their code(s), time series. Nothing else.
- **Their team**: invite/remove fellow org users (org-admin role only), self password reset.
- No pricing, no results, no member list of takers (takers are anonymous).

## 5. White-labelling (LIGHT — decided)

- Entry: `/r/{code}` sets org context (server-validated, then localStorage) and redirects to `/`.
- Branded surfaces: assessment intro + result pages show org logo + name with the fixed attribution line: **“in partnership with Rather Know”**. No colour/theme changes. Locked copy stays locked (HANDOFF §5a).
- **Disclosure line on branded intros (required, verbatim):** “{Org} can see how many people started and finished — never your answers, your results, or who you are.”
- Data effect: sessions started under a code carry `partner_code` (one extra field on `mirror_v2_sessions`). That field feeds counts and NOTHING else.

## 6. Auth requirements

- Email + password (bcrypt), JWT access tokens, short-lived, HttpOnly-refresh or re-login (agent's call), rate-limited login, generic error messages.
- **Password reset**: email token flow (time-limited, single-use) for org users and super-admin; super-admin can also force-reset any org user (sends them a reset email — admin never sees/sets a password directly).
- Email delivery: pick Resend or SendGrid via the integration playbook — do NOT hand-roll SMTP.
- **The build agent MUST consult its auth integration playbook before writing any auth code.** Seed exactly one super-admin from env vars (idempotent seed); record credentials in the job's test_credentials memory file.
- Audit-log every: login success/failure, invite issued/accepted, reset requested/completed, org/user/code mutation.

## 7. Consumer accounts (P2 — optional, opt-in)

- Register/login (same auth stack). On login, offer to **claim** anonymous sessions present in the browser (`mi2.sessions`) into the account; claiming copies the linkage, never rewrites the session's anonymous provenance.
- Account page: their results list, their entitlements, **delete account** (GDPR — severs linkage; anonymous sessions revert to unowned).
- Never prompted mid-assessment; the only surfaces that may mention accounts are result pages ("keep this result") and the entitlement/report flow.

## 8. Data model sketch (new collections, RK database)

- `organisations` {id, name, logo_url, status, contact_email, created_at}
- `org_users` {id, org_id, email, password_hash, role: org_admin, status, last_login_at}
- `partner_codes` {code, org_id, status, created_at, revoked_at}
- `admin_users` {id, email, password_hash, role: super_admin}
- `auth_tokens` (invites + password resets) {token_hash, purpose, subject_id, expires_at, used_at}
- `audit_logs` {actor_type, actor_id, action, subject, meta, at}
- `consumer_users` (P2) {id, email, password_hash, created_at}
- `session_claims` (P2) {session_id, consumer_user_id, claimed_at}
- Change to existing: `mirror_v2_sessions.partner_code` (optional string).

## 9. Routes

- Portal UI: `/admin/*` (login, dashboard, organisations, org detail, users, codes, audit). Org-admins log in at the same door; RBAC decides the nav. Everything noindex + robots-disallowed.
- API: `/api/admin/*` (super), `/api/org/*` (org-admin), `/api/r/{code}` (public code resolution). Consumer auth (P2): `/api/account/*`.

## 10. Phasing & acceptance

- **P0**: super-admin auth + orgs + org users (invite/reset/deactivate) + partner codes + counts + audit log. Accept: seeded super-admin logs in; creates org; invites org user; org user accepts invite, logs in, resets password; `/r/{code}` stamps a session; counts move; every step audited.
- **P1**: org-admin self-serve (branding, link, counts, team). Accept: org-admin sees only their org; cannot reach any other org's data by ID manipulation (test this explicitly).
- **P2**: consumer accounts + claiming + delete. Accept: assessment flow untouched when logged out; claim round-trips; delete severs.
