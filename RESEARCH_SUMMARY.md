# Research Summary — Standalone Email-Signature System

**Goal:** A standalone app where the admin designs one branded company signature that is
auto-applied to every employee's email, automatically filled with each sender's own name
and email — no per-agent mailbox connection or manual setup.

**Research/decision:** Reviewed how the industry does this (Exclaimer/CodeTwo gateway
injection, client-side push, directory+API). Chosen approach = Google Workspace `sendAs`
API: one Google Cloud project + a delegated service account authorized by the Workspace
super-admin, which fetches staff details from the Directory API and writes each user's
personalized signature into their Gmail (re-synced on change/new hire).

**Hard requirement:** Only works if the office is on paid Google Workspace (custom domain
+ admin console); free @gmail.com accounts can't be managed this way. Pending confirmation
of Workspace before writing the full implementation plan.
