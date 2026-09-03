# lockten.ai — Lock Ten Studio marketing site

The live marketing website for Lock Ten Studio. **Static HTML + CSS, no build step.** Hosted on Render, custom domain **lockten.ai**. Repo: `github.com/locktenstudio/lockten-website`.

## Deploy

**Push to `main` → Render auto-deploys** (publish dir is the repo root, no build command). A deploy takes roughly 30 seconds to 2 minutes. There is nothing to compile: edit HTML/CSS, commit, push, done.

```bash
git add .; git commit -m "..."; git push
```

## Pages

| File | What it is |
|---|---|
| `index.html` | Homepage. Hero, the two products (Walkthrough + The Install), studio, Field Notes signup, footer. |
| `walkthrough.html` | Walkthrough product page. Hero, how-it-works, modes, compare, pricing, FAQ, final CTA. |
| `primer.html` + `primer-thanks.html` | The Cowork Primer: a readable article with an email-gated PDF. `primer-thanks.html` is the Beehiiv form's success-redirect download page. |
| `install.html` | The Install product page. **PUBLIC** since the 2026-07-05 product-first restructure: linked from the homepage nav, hero and product card. See CTA note below. |
| `architect.html` | Architect Walkthrough product page. **Green-themed**: the page overrides the ramp tokens at `body.arch` level with the app's pine ramp (brand `#1B4D3E`, mint accent `#9FD6BF`); everything else reuses the global kit. Screens in `assets/screens/architect/`, demo video and poster in `assets/video/`. App is **live on the App Store** (released 2026-07-24): both launch stamps say "Now on the App Store" and both CTAs are the store badge linking `https://apps.apple.com/app/id6787164107`. **The homepage stays SILENT on Architect** and that is deliberate, reaffirmed by Josh 2026-08-03: no nav link, no product card, and **no Architect entry in the `index.html` Organization `sameAs`** (it was added and then deliberately backed out). Two reasons: he wants separation between the builder and architect audiences, and Architect may eventually move to its own domain if it gets traction, which `sameAs` would tie to lockten.ai and then have to be unwound. Architect stays reachable by direct URL, sitemap and llms.txt. Do not "fix" this by linking it. |
| `help.html` | Walkthrough help / FAQ center (web-hosted so it updates without an app release). |
| `architect-help.html` | Architect Walkthrough help / FAQ center. Cross-linked with `/architect` and `/help`. |
| `materialmonitor.html` | Material Monitor product page. **Copper-themed**: the page overrides the ramp tokens at `body.mm` level with a slate ground and copper accent ramp (brand `#A85F2B`, copper accents `#C8763C`/`#DE9A66`/`#B5682F`); everything else reuses the global kit. **The homepage stays SILENT on Material Monitor**, by the same reasoning as Architect and Handover: no nav link, no product card, no `sameAs` entry. It stays reachable by direct URL, sitemap and llms.txt. Do not "fix" this by linking it. Email capture is a plain `mailto:info@lockten.ai` button, not a Beehiiv embed, by Josh's decision: no newsletter tool for this page, he tracks founding-list interest in his own spreadsheet. Share image at `assets/og/og-materialmonitor.png`. |
| `privacy.html`, `terms.html` | Legal. |
| `styles.css` | All global styling + design tokens (`:root`). Page-specific CSS is inline in a `<style>` in each page's `<head>`. |
| `assets/`, `fonts/` | Images/logos + self-hosted woff2 fonts. `assets/screens/` holds 640px WebP app screenshots (sourced from `G:\My Drive\AI Business\Walkthrough TikTok Kit\2 - App screens (hero shots)\Raw screenshots`; re-convert with ffmpeg `-noautorotate -map_metadata -1` or they come out rotated). `assets/og/` holds the 1200x630 share cards. |
| `sitemap.xml` | Sitemap (robots.txt points to it). Add new public pages here; keep success/thanks pages out and `noindex`ed. |

## Share images and social

- Every top page has a branded 1200x630 `og:image` in `assets/og/` plus `twitter:card summary_large_image`. Source HTML templates for regenerating them live in the session scratchpad, rendered via headless Chrome; rebuild by re-rendering a 1200x630 page in the Lock Ten design system.
- Footers carry Instagram and X icons: both handles are **@locktenstudio** (per `Interim Soft Brand Presence.md` in the AI Business Drive folder).
- The Walkthrough page hero is a 5-shot rotating carousel (`#wt-carousel`) with captions in `#wt-shot-note`; it respects `prefers-reduced-motion`.
- Walkthrough sign-in copy: the app emails a **six-digit code** (confirmed by Josh 2026-07-05). Don't "correct" the FAQ to say magic link.

## URL convention

Render serves extensionless clean URLs (`/walkthrough`, `/install`, `/help`, `/primer`, `/privacy`, `/terms`) alongside the `.html` paths. **Clean URLs are canonical**: every page carries a `rel="canonical"` clean URL, internal links use clean URLs, and the sitemap lists them. Exception: the Beehiiv primer form's success redirect is configured (in Beehiiv) to `/primer-thanks.html`; leave that page reachable at the `.html` path.

## Design system (match it, don't invent)

Lock Ten Design System. Tokens live in `styles.css` `:root`.
- **Colors:** gate blue `#1C71C1` (`--brand`), deep navy `#0C1B38` (`--deep-900`) for dark surfaces, cool-grey slate neutrals, pure white ground. **No warm tones, no gradients** in the site itself. `#272260` indigo is the logo color ONLY, never text/neutrals.
- **Fonts (self-hosted in `fonts/`):** Instrument Serif (display/headlines), Geist (UI/body), Geist Mono (labels/spec data).
- Mobile-first responsive; `@media (min-width: ...)` for desktop. Reveal-on-scroll via a small inline IntersectionObserver.

## Analytics

**Cloudflare Web Analytics** beacon is on every page (just before `</body>`), token `cd30115fa535417ca908587b96cd3733`. Free, cookieless, no consent banner. Dashboard: dash.cloudflare.com → Web Analytics → lockten.ai (Josh's account). Hosting stays on Render; Cloudflare only counts. When adding a NEW page, copy the beacon snippet in before `</body>`.

## SEO and indexing

- Every page: unique `<title>`, meta description, `rel="canonical"` clean URL, an OG image in `assets/og/` plus `twitter:card`. Keep this pattern on every new page.
- **Structured data (JSON-LD):** Organization on `index.html` (with `sameAs`: Instagram, X, App Store listing), SoftwareApplication + FAQPage on `walkthrough.html`, FAQPage on `install.html`. **The FAQ schema is generated from the on-page `<details><summary>` FAQ, so if you edit the visible FAQ, regenerate the matching FAQPage JSON-LD** (a small python `<details>` parse builds it) or the two drift.
- `llms.txt` at the root is a plain-markdown site index for AI crawlers (ChatGPT/Claude/Perplexity). Update it when products or pricing change.
- **Indexing (set up 2026-07-05):** verified in Google Search Console (Domain property, auto-verified via the Workspace DNS) and Bing Webmaster Tools (imported from GSC). `sitemap.xml` submitted to both. New public pages just need to be added to `sitemap.xml`; they get crawled on the next pass.

## Walkthrough launch state (current)

Walkthrough is **live on both stores** as **"Walkthrough: Site Reports"**: App Store since 2026-07-07 (`https://apps.apple.com/app/walkthrough-site-reports/id6775347863`), Google Play since 2026-08-01 (`https://play.google.com/store/apps/details?id=com.cabinjohnbuilders.walkthrough`). The old Beehiiv notify form (`e266c9b9`) was removed from `/walkthrough` at the 2026-07-05 store flip.

**Store badges are a matched pair.** Markup is `.store-badges` (add `.store-badges-sm` for the homepage card) wrapping an `a.badge-apple` and an `a.badge-google`; sizing lives in `styles.css`, not per page. Both are official artwork and must never be recolored, cropped, restyled or distorted. Apple's `assets/app-store-badge.svg` is tight to the badge; Google's `assets/google-play-badge.png` (the official generic English web badge, 646x250) bakes Google's required clear space into the image, so it is set about 29% larger to make the two read at the same visual height. Google does not publish an SVG of this badge, which is why one is PNG and one is SVG.

**Google requires the line "Google Play and the Google Play logo are trademarks of Google LLC" in the footer small print of every page that shows the badge** (`index.html`, `walkthrough.html`, `sample-report.html`). Add it to `.footer-legal` on any new page that gains a Play badge. Apple asks for no equivalent line, so there is none.

**Architect Walkthrough is iOS only** and stays that way on the site: `architect.html`, its FAQ, the `architect-help.html` billing copy, the Architect line in `privacy.html` and the Architect entry in `llms.txt` all correctly say App Store / iOS. Do not sweep them into an Android edit.

## Pricing (single source of truth for the site)

**Two tiers since 2026-07-24: Standard $9.99/mo or $99.99/yr (all capture lanes, on-device, unlimited reports) and Pro $24.99/mo or $239.99/yr (adds meeting notes and the persistent punch list).** Trial is all-access: 3 free reports of any kind, no credit card, usage-based, never framed as time-limited or auto-converting. Per user, not per seat. iOS billing is Apple In-App Purchase (via RevenueCat).

Price appears in SEVEN places; update ALL together: `walkthrough.html` `#pricing` block, its FAQPage JSON-LD offers + three FAQ answers, the Walkthrough card in `index.html`, `help.html` billing section, `llms.txt`, and `sample-report.html` price note.

**Architect Walkthrough: $19.99 / month, or $199.99 / year (about $17/mo).** First three SENT reports free (drafts don't count), no credit card. Apple billing only. Shows on `architect.html` `#pricing` and in its FAQ; `architect-help.html` billing section must match.

**The Install (repositioned 2026-08-10, Josh's call): TWO tiers. Lite is FREE (email-gated download, no card) and Plus is $499 one-time.** Concierge and the Recurring subscription are RETIRED: Concierge is deliberately unadvertised (inbound email only), so do not re-add it to any page. The product is positioned as static: no ongoing-skills or new-content promises anywhere in site copy. Install pricing appears in FIVE places; update ALL together: `install.html` (hero, tier cards, FAQ + its FAQPage JSON-LD, final CTA band), the Install card in `index.html`, `llms.txt`, the Install paragraph in `primer.html`, and the refunds list in `terms.html`.

## Contact-email convention

Public pages use **role addresses**: `info@lockten.ai` (general), `support@lockten.ai` (Walkthrough refunds/support). `josh@lockten.ai` is reserved for where a real person must read it; its one remaining public use is the primer's "a real person reads it" line (`primer.html`), which is deliberate. Keep it that way.

## The Install page

`install.html` is **public** (homepage nav, hero and product card link to it since 2026-07-05). Its buy flow lives in the separate intake app at `install.lockten.ai` (repo `locktenstudio/onramp-intake`). Since the 2026-08-10 repositioning: **Lite is free** (`/buy-lite` is an email-gated download, no Stripe) and **Plus is $499** through live Stripe Checkout.

CTA mechanics: the Plus entry route `POST https://install.lockten.ai/intake/start` **rejects GET with a 405**, so every Plus CTA on `install.html` is a `<form method="POST">` button, never a plain `<a href>`. Lite (`/buy-lite`) is a normal page and a normal link. Keep it that way when editing CTAs.

## Beehiiv embeds

- Homepage Field Notes signup: form `a189be07-5f91-4076-ba42-67b8fe520c48` (`#newsletter`).
- Primer PDF capture: form `42f283e6-...` on `primer.html` `#get-pdf`, success-redirects to `/primer-thanks.html`.
- One Beehiiv form embedded twice on a page only renders the first instance.

## Design/architecture specs

The written page specs live in Josh's Drive at `G:\My Drive\AI Business\Deliverables\2. Lockten.ai Website\` (Homepage/About/Walkthrough/Install/Primer/Method/Notes architecture docs). Reference for intent, but the live HTML is the source of truth.

## Lock Ten agent team

Josh runs a Lock Ten agent team with the main Claude session as orchestrator (chief of staff). Charter and routing: `G:\My Drive\AI Business\LOCKTEN_AGENT_TEAM.md`. User-level agents in `~/.claude/agents/`:

- `lockten-reviewer` reviews diffs adversarially. On this repo push-to-main IS a deploy, so run it before every push, not just the risky ones.
- `lockten-support` triages the josh@lockten.ai mailbox; its "help center gap" findings become edits to `help.html`.
- `walkthrough-debugger` covers the Walkthrough apps, not this site.

Autonomy: draft freely; nothing pushed, published or sent without Josh's explicit approval.
