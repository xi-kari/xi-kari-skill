# Maintaining the project page

The website reads its research outline from `data/research-topics.json` and its
shared progress from `data/research-progress.json`. Both files are committed
project data. Publishing the same files gives every visitor the same progress.
Checking a topic locally changes the progress source file; it does not publish
the website automatically.

## Edit research progress locally

From the repository root, run:

```text
python scripts/serve_project_page.py
```

Open `http://127.0.0.1:4389/` in a browser. The local editor saves each checkbox
change to `docs/data/research-progress.json`. Review the resulting file change,
commit it, and publish the project page through the repository's normal website
publishing process. Visitors to the static website can read the published
progress; they cannot change the repository file.

Use `--port 4390` to select a different port. `--directory` can point to another
page directory containing the same two data files, for example when testing a
temporary copy. The server binds only to `127.0.0.1`. It does not support remote
editing, cross-origin requests, or a remote authentication service. Run one
maintenance server per checkout, and stop it with Ctrl+C when finished.

The server serializes concurrent checkbox changes and replaces the progress
file atomically. A failed save leaves the previous file intact. If the progress
file is malformed, editing fails instead of silently resetting it. Restore or
correct the file before retrying.

## Public data formats

`research-topics.json` contains only:

```json
{
  "schemaVersion": 1,
  "title": "Research outline",
  "modules": [
    {
      "id": "01",
      "title": "Domain",
      "topics": [
        { "id": "01.01", "title": "Topic", "question": "What should be studied?" }
      ]
    }
  ]
}
```

Keep topic IDs unique and stable. The public file must not include private
research paths, local source inventories, credentials, or internal audit fields.
After changing the outline, restart the local server so its known topic IDs are
refreshed. Remove obsolete completed IDs when removing topics.

`research-progress.json` starts with no completed topics:

```json
{
  "schemaVersion": 1,
  "updatedAt": null,
  "completed": {}
}
```

A completed topic is stored as an ID mapped to an ISO 8601 UTC timestamp, such
as `"01.01": "2026-01-01T00:00:00.000Z"`. Unchecking removes that ID. Every
successful edit updates `updatedAt`. An absent ID means incomplete. A published
completion records the maintainer's research status; it does not by itself mean
that a theory has been adopted into the framework or that historical claims
have been independently verified.

## Local editor API

- `GET /api/project-editor` returns
  `{ "editable": true, "token": "...", "progress": { ... } }`.
- `POST /api/research-progress` accepts exactly
  `{ "id": "01.01", "completed": true }` or the same object with `false`.
  Send `Content-Type: application/json` and `X-Project-Token` with the token from
  the editor endpoint. The browser supplies the same-origin `Origin` header;
  other clients must supply it explicitly. The origin must match the request's
  loopback host and port. A successful response is the complete progress object,
  not a wrapper around it.
- Requests must have an allowed loopback `Host`. Writes also require a matching
  `Origin`, the current editor token, a known topic ID, an actual JSON boolean,
  and a body of at most 4096 bytes. Invalid requests do not change progress.
- Error responses contain `{ "error": "..." }`. Status codes are `400` for
  invalid input, `403` for host/origin/token rejection, `404` for unknown API
  paths, `413` for body size, `415` for content type, and `500` for read/save
  failure. Keep the displayed state unchanged or restore it when a save fails.
- Static files, including `/data/research-progress.json`, remain readable.
  Local responses use `Cache-Control: no-store`; no CORS headers are enabled.
  If the editor endpoint is absent on static hosting, the page is read-only.

The random editor token lasts only for the local server instance. It is an
in-memory CSRF protection value, never part of public data or the Skill runtime.
Refresh the page after restarting the server to obtain a new token.

## Verification

```text
python -m unittest tests.test_project_page_progress -v
```

The API tests use temporary page directories and ephemeral loopback ports. They
exercise persistence, unchecking, request rejection, concurrent updates, restart
behavior, and recovery after a failed save without editing published progress.
