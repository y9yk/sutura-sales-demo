# Which October sales? — a real sutura demonstration

A small reader-facing product demonstration accompanying [the article](https://y9yk.bearblog.dev/ai-sales-query-metric-definition-experiment/). Every run executes the actual pinned **sutura 0.11.0** binary against synthetic commerce data. No live LLM, model key or external database is needed.

## Live demonstration

[Open the public demo](https://sutura-sales-demo.vercel.app/) or its [compact surface](https://sutura-sales-demo.vercel.app/embed).

Production was built on Vercel Container Runtime from a Git archive of commit `d4fc631`, uploaded through Vercel Drop. All seven actual-engine public HTTP scenarios were checked. This deployment is not connected to Git autodeploy; connect the repository or use Vercel CLI for subsequent releases.

## Run locally

Docker must already be running.

```sh
docker compose up --build
```

Open http://localhost:8080. The compact embeddable surface is `/embed`.

Tests:

```sh
python3 -m unittest discover -s tests -p 'test_*.py'
node --test tests/test_ui.mjs
```

## What to try

- **October net sales:** an intentionally incomplete SQL control returns$470; the declared net metric returns$375.
- **Regional net / WIDGET orders:** correct controls and product results should match. This is not evidence of a product accuracy advantage.
- **Scope change / undefined profit:** inspect actual product refusals rather than a fabricated answer.
- **Empty December:** compare a scalar zero control with the product's empty rows. They remain visibly different.
- **Anchor drift:** deliberately add10USD to one prepared net value in a temporary copy. The uncontrolled SQL reads$385; the product rejects the$375known-answer mismatch.

Controls are manually written teaching comparisons, not observed AI mistakes. Liveproduct runs are distinct from the article's earlier 108 model trials.

## What we prepare; what the product does

`source-fixture.json` contains14 invented orders, customer, line and refund records. `commerce-v1/data` contains one prepared row per order: net amounts already subtract associated refunds and the WIDGET membership flag already selects the whole-order cohort. `is_production` derives from the source test flag for the supported`is_true` predicate. Sutura does not choose the refundpolicy or repair the source joins automatically.

The markdown catalog defines metrics, fixed filters, dimensions, relationships, glossary/caveats and known-answer anchors. Sutura compiles/executes those requests, provides a definition digest, rejects unsupported requests and verifies anchors. The wrapper exposes only fixed scenarios and compares them with SQLite controls over the same prepared data.

## Deploy to Vercel

This repository is a Container Runtime project: `vercel.json` selects the Container framework preset. The root Dockerfile copies the official image'sNix closure/binary into aPython standard-library HTTP server image; no pip/npm dependencies are installed. The server respects `PORT` and defaults to8080.

Import thisrepository intoVercel. No application secrets are required. Container Runtime is currently aVercel beta: confirm feature availability and deployment limits in your account. See [Container Runtime](https://vercel.com/docs/functions/runtimes/container) and [Services](https://vercel.com/docs/services). Real deployment status belongs in the release/receipt, not this setup guide.

The embedded page sets no application cookies. HTTPresponses permit framing by the article'sBearblog origin and self. A standalone demo link should accompany any iframe in case the parent blog strips third-party frames.

## Reproducibility and scope

Officialruntimeimage: `ghcr.io/telekom/sutura@sha256:51a04d86c1d87049f01fb80fd6218bbebc21dce6180bbf97693cd741bce4bb2f` (amd64/arm64 manifest). Release version 0.11.0. Catalogschema consulted atupstream commit02da429c9191805d11878a7c5e5be73b14147dcc. Allfixtures are synthetic. An explicit demo-v1 label identifies this app's catalog release; engine catalog digests carry actual content identity.

This is a small single-step metrics demonstration. No claim of higher LLM accuracy, production authorization, fresh data or historical snapshot storage is made. Shared public fixture access is not end-user row-level security.

## Licenses

Original application code and synthetic fixture: MIT. Sutura is Apache-2.0; its LICENSE/NOTICE/VENDOR information is preserved under `third_party/sutura`. The pinned runtime includes third-party components under their respective licenses; its full source and dependency declarations remain in the [upstream repository](https://github.com/telekom/sutura).
