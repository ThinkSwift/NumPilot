# numpilot.com

Marketing homepage for **NumPilot** — describe a physics setup in plain words; a verified on-device solver computes it.

Served via GitHub Pages with the custom domain `numpilot.com` (see `CNAME`).

## Pages

- `index.html` — landing page (includes a live in-browser finite-difference heat solve in the hero)
- `m.html` — share-link landing page (`numpilot.com/m?r=<base64url recipe>`); mirrors `web/index.html` in the app repo
- `privacy.html` / `terms.html` — linked from the app's Settings screen (`/privacy`, `/terms`)
- `404.html` — not-found page
- `.well-known/apple-app-site-association` — universal links for `/m*` (note: `TEAMID` placeholder must be replaced with the real Apple Team ID before universal links work)

No build step — plain static HTML, self-contained (no external assets or CDNs).
