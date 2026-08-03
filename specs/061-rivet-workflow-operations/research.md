# Research

Decision: persist only review metadata in SQLite and rely on runner-owned,
bounded in-memory events for history in this MVP. This keeps project content,
datasets, credentials, and raw logs outside the operations index. A later
durable run ledger requires its own retention and audit design.
