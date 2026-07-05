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
| `install.html` | **The Install product page. STAGED, see note below. Live at the URL but NOT linked from the homepage.** |
| `help.html` | Walkthrough help / FAQ center (web-hosted so it updates without an app release). |
| `privacy.html`, `terms.html` | Legal. |
| `styles.css` | All global styling + design tokens (`:root`). Page-specific CSS is inline in a `<style>` in each page's `<head>`. |
| `assets/`, `fonts/` | Images/logos + self-hosted woff2 fonts. |

## Design system (match it, don't invent)

Lock Ten Design System. Tokens live in `styles.css` `:root`.
- **Colors:** gate blue `#1C71C1` (`--brand`), deep navy `#0C1B38` (`--deep-900`) for dark surfaces, cool-grey slate neutrals, pure white ground. **No warm tones, no gradients** in the site itself. `#272260` indigo is the logo color ONLY, never text/neutrals.
- **Fonts (self-hosted in `fonts/`):** Instrument Serif (display/headlines), Geist (UI/body), Geist Mono (labels/spec data).
- Mobile-first responsive; `@media (min-width: ...)` for desktop. Reveal-on-scroll via a small inline IntersectionObserver.

## Analytics

**Cloudflare Web Analytics** beacon is on every page (just before `</body>`), token `cd30115fa535417ca908587b96cd3733`. Free, cookieless, no consent banner. Dashboard: dash.cloudflare.com → Web Analytics → lockten.ai (Josh's account). Hosting stays on Render; Cloudflare only counts. When adding a NEW page, copy the beacon snippet in before `</body>`.

## Walkthrough launch state (current)

Walkthrough is **live on the App Store** as **"Walkthrough: Site Reports"**, store URL `https://apps.apple.com/app/walkthrough-site-reports/id6775347863`. The `/walkthrough` page shows the official Apple **App Store badge** and "Now on the App Store" copy (flipped from the pre-launch notify form on 2026-07-05). The old Beehiiv notify form (`e266c9b9`) was removed from that page at the flip.

## Pricing (single source of truth for the site)

**$24.99 per user / month, or $239.99 / year (about $20/mo).** 3 free walkthroughs, no credit card. It is **per user**, not per seat. iOS billing is Apple In-App Purchase (via RevenueCat); web is Stripe. On the site the price shows in two spots: `walkthrough.html` `#pricing` block and the Walkthrough card in `index.html`. Update both together.

## Contact-email convention

Public pages use **role addresses**: `info@lockten.ai` (general), `support@lockten.ai` (Walkthrough refunds/support). `josh@lockten.ai` is reserved for where a real person must read it (e.g. The Install Concierge inquiry). Keep it that way.

## The Install page (read before touching)

`install.html` is **staged**: it is live at `lockten.ai/install.html` but deliberately **NOT linked** from the homepage nav or footer. Its buy buttons point at `install.lockten.ai` (a separate app; Stripe was in test mode at last note). It is owned by a separate "Install chat." **Do not link it from the homepage or promote it without checking with Josh / that chat first.**

## Beehiiv embeds

- Homepage Field Notes signup: form `a189be07-5f91-4076-ba42-67b8fe520c48` (`#newsletter`).
- Primer PDF capture: form `42f283e6-...` on `primer.html` `#get-pdf`, success-redirects to `/primer-thanks.html`.
- One Beehiiv form embedded twice on a page only renders the first instance.

## Design/architecture specs

The written page specs live in Josh's Drive at `G:\My Drive\AI Business\Deliverables\2. Lockten.ai Website\` (Homepage/About/Walkthrough/Install/Primer/Method/Notes architecture docs). Reference for intent, but the live HTML is the source of truth.
