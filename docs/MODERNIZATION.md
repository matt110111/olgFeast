# Event tablet modernization

Purpose: volunteer-operated Android browser terminals for nonprofit dinners.
Tickets are sold elsewhere. This app records portions ordered, tickets owed and
collected, and recipe-based estimated ingredient/supply use for each event.

Implementation checklist
- [x] Session refresh, Argon2 password upgrade, password change, WebSocket authorization
- [x] Atomic, retry-safe checkout with permanent ticket/recipe snapshots
- [x] Event setup, menu ticket values, consumables, recipes, stock and CSV reports
- [x] Tablet order station, kitchen workflow, clear connection/error states
- [x] Vite build, dependency locks, required CI checks and browser tests
- [x] Versioned database migration, backup/restore verification, deployment

Existing deployment source and database were backed up before changes. The
existing order is preserved; historical orders without recipe snapshots cannot
reconstruct past consumable use reliably.

Validation: 68 backend tests, 18 frontend tests, two tablet browser workflows,
PostgreSQL concurrent checkout checks, and restored/fresh database migrations.
TLS/domain setup and physical tablet testing remain site-specific follow-up work.

## Confirmed workflow: guests and volunteers

The user confirmed both tablet audiences, both portion counts and recipe-based
consumables, and physical ticket collection. Guest accounts now use event ordering
and hand orders to a volunteer ticket desk. Only staff can confirm collection;
confirmation is idempotent and records collector and time. Awaiting orders are
excluded from kitchen queues and depletion. Migration 0003 preserves existing orders.
Guest tablet accounts can be created from Setup. Shared tablets use a shared account
history; table numbers are recommended instead of personal guest information.

Validation for the guest handoff: 71 backend tests, 19 frontend unit tests,
frontend lint/typecheck/build, and four browser scenarios across both tablet
sizes passed. PostgreSQL checks verified 12 simultaneous ticket confirmations
record collection once. A current production backup restored into an isolated
database migrated from 0002 to 0003 and retained its existing order.

## Separate rooms and concurrent stations

Events can now contain rooms with their own assigned menus, tablet carts, ticket
queues, kitchen queues, stock records, and reports. Whole-event reporting includes
all rooms and shared stock. A room is an operational filter; staff can deliberately
switch rooms. New orders must select a room once rooms exist, and the server rejects
items outside its menu and actions scoped to a different room. Migration 0004 leaves
older orders and stock unassigned rather than inventing historical room assignments.

Read-only event views no longer lock the event row. Order notifications skip unused
legacy WebSocket feeds, avoiding a full kitchen/report rebuild for every tablet write.
Number allocation and checkout retries still use the transactional database lock.

Validation: 74 backend tests, 20 frontend tests, lint/typecheck/build, and six browser
scenarios across 1024×600 and 800×1280 passed. Separate browser contexts verified
room menus, drafts, guest collection, kitchen isolation, and aggregate reports.
Fresh PostgreSQL migration and a restored production backup upgrade to 0004 passed,
preserving the existing event and historical order.

On this Raspberry Pi, an isolated PostgreSQL test used 48 distinct authenticated
volunteer accounts across two rooms. A simultaneous burst produced 48 unique orders
with zero errors; 48 retries produced no duplicates. Checkout p95 was 1.048 seconds
(max 1.098 seconds). Three refresh waves and all 144 kitchen status transitions
passed; room and whole-event tickets, portions, and consumables reconciled exactly.
See room-load-results.json. This is an API simulation on the server, not a Wi-Fi or
physical-tablet capacity guarantee, and not a long-duration soak test.
