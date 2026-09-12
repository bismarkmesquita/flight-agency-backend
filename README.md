# Flight Agency — API

REST API for a travel agency back-office: client and supplier registration, flight network (airlines and airports), sales, reservations, and a dashboard with performance indicators by period.

> This is the **backend** repository. The interface (Next.js) is located in
> [flight-agency-frontend](https://github.com/bismarkmesquita/flight-agency-frontend).

## The problem the system solves

Smaller travel agencies often track sales and bookings using spreadsheets—with a tab for each month,
manual formulas to calculate commissions and profits, and no easy way to cross-reference information such as
"which suppliers we sold the most of last quarter" or "which salesperson performed best
this year."

This system replaces spreadsheets with a centralized record-keeping setup: each sale is linked to a customer, a salesperson, a reservation, and the corresponding flights, keeping the complete history in one place. This facilitates data maintenance (eliminating duplicate or outdated files), searching (using filters and search functions instead of "Ctrl+F" in a spreadsheet), and analysis (via a dashboard featuring KPIs, charts, and salesperson rankings calculated directly from the data).

## Demo

🔗 https://flight-agency-frontend.vercel.app/ (frontend deployed on Vercel, consuming this API)

- Login (manager): `manager@agency.dev` / `manager123`
- Login (seller): `seller@agency.dev` / `seller123`

> **The data displayed in the demo is fictitious** and automatically generated (names, emails, companies,
> flights, sales, etc., via [Faker](https://faker.readthedocs.io/)) — it does not correspond to any
> real agency, client, or transaction.
>
> **The demo is read-only.** The users above have `access_level = DEMO`: they can navigate and
> view all modules, but any create/edit/delete operation is rejected by the API
> (`403`) so that the public database is not altered by visitors.

## Stack

- **Django 4.2** + **Django REST Framework**
- **PostgreSQL**
- **django-rest-knox** — token-based authentication
- Deploy: **Railway**

## Architecture

"Vanilla" REST API: one DRF `APIView` per resource, with explicit routes (`path()`), no routers
and no DRF serializers for request/response bodies — each view builds its JSON response by hand.
This keeps each endpoint's payload under direct control, without the implicit conventions of a
`ModelSerializer`/`ViewSet`.

Every response follows a single envelope:

```json
// success
{ "success": true, "message": "...", "data": { ... } }

// business error (HTTP 200 — the client branches on the "success" field, not the status code)
{ "success": false, "message": "...", "reason": "SOME_FAILURE_REASON", "errors": null }
```

Django apps, by domain:

| App | Responsibility |
|---|---|
| `core/` | Project configuration, shared base (`BaseModel`, `BaseAdmin`, utils) |
| `users/` | Authentication, users, roles (admin/manager/seller) and audit log |
| `flights/` | Airlines, airports and flights |
| `agency/` | Customers, suppliers, sales, reservations and the dashboard |

Authorization in two layers:
- **Role** (`admin` / `manager` / `seller`) — controls which screens/actions each profile can see.
- **Access level** (`FULL` / `DEMO`) — independent of role, blocks any write for demo users.

## Running locally

Requires a local PostgreSQL instance (`agency` / `agency` / `agency` on `localhost:5432`, or
`DATABASE_URL`).

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py populate_local     # DEBUG only: populates the local database with test data
python manage.py runserver          # http://localhost:8000
```

Logins created by `populate_local`: `agency@agency.com` / `agency` (admin),
`manager@agency.dev` / `manager123` (manager), `seller@agency.dev` / `seller123` (seller).

## Testing

```bash
python manage.py test --parallel
```
