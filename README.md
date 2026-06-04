# lockten.ai , v0 Landing Page

The v0 website for Lock Ten Studio, built to support the Stripe account application. Pure static HTML + CSS, no build step. Designed for deployment as a Render Static Site.

## What's here

| File | Purpose |
|---|---|
| `index.html` | The single-page landing site (hero, two products, trust, newsletter signup, footer) |
| `privacy.html` | Basic privacy policy (Stripe requires) |
| `terms.html` | Basic terms of service (Stripe requires) |
| `styles.css` | All styling. Uses the warm palette + Crimson Pro + Source Sans 3 visual system established in the Pyramid PDF and marketing hub. |
| `robots.txt` | Allow search indexing |
| `.gitignore` | Standard ignores for editor / OS files |
| `README.md` | This file |

## Status

**v0, pre-launch.** This is the temporary version to support Stripe account application and DNS pointing. Will be replaced when Shannon's visual identity work lands (probably late June 2026). Architecture for the full v1 site is specified in:

- `Deliverables/2. Lockten.ai Website/Homepage Architecture v3.md`
- `Deliverables/2. Lockten.ai Website/About Page Architecture v3.md`
- `Deliverables/2. Lockten.ai Website/Walkthrough Product Page Architecture.md`
- `Deliverables/2. Lockten.ai Website/Install Product Page Architecture.md`
- `Deliverables/2. Lockten.ai Website/Notes Page Architecture.md`
- `Deliverables/2. Lockten.ai Website/Method Page Architecture.md`
- `Deliverables/2. Lockten.ai Website/Primer Page Architecture.md`

(All paths relative to `G:\My Drive\AI Business\`.)

## To swap in the Beehiiv signup form

When the Beehiiv embed code is ready, find this block in `index.html`:

```html
<div class="newsletter-form" id="beehiiv-embed-slot">
  <!-- BEEHIIV EMBED GOES HERE... -->
  <p class="newsletter-fallback">
    ...
  </p>
</div>
```

Replace the entire contents inside `<div class="newsletter-form" id="beehiiv-embed-slot">...</div>` with the iframe / script tag Beehiiv provides. The CSS already styles iframes inside `.newsletter-form` to be responsive.

Commit the change, push to GitHub, Render auto-deploys.

## Deployment , Render Static Site

### One-time setup

1. **Create a new Git repo locally** in this folder:
   ```bash
   cd C:\Dev\lockten-website
   git init -b main
   git add .
   git commit -m "v0 landing page"
   ```

2. **Create a new GitHub repo** in the `locktenstudio` org (or your personal account if Lock Ten Studio doesn't have a GitHub org yet): `locktenstudio/lockten-website` or `JLR-cjb/lockten-website`. Don't initialize it with anything (no README, no .gitignore).

3. **Connect local to GitHub:**
   ```bash
   git remote add origin https://github.com/locktenstudio/lockten-website.git
   git branch -M main
   git push -u origin main
   ```

4. **Create the Render Static Site:**
   - Log in to render.com
   - "New +" → "Static Site"
   - Connect the `lockten-website` GitHub repo
   - Settings:
     - **Branch:** main
     - **Build Command:** (leave blank , no build step)
     - **Publish Directory:** `.` (just a period; this is the repo root)
   - Create Static Site

   Render will deploy on every push to main. First deploy takes ~30 seconds.

5. **Add custom domain (lockten.ai) in Render:**
   - In the Static Site's "Settings" tab, scroll to "Custom Domains"
   - Add `lockten.ai` and `www.lockten.ai`
   - Render displays the DNS records to configure (an A record for the apex domain, a CNAME for www)

6. **Configure DNS at Porkbun:**
   - Log in to Porkbun
   - Find lockten.ai → DNS Records
   - Add/update the records Render specified:
     - An **A record** for `@` pointing to Render's IP (Render gives you the value)
     - A **CNAME record** for `www` pointing to the `.onrender.com` hostname Render gives you
   - Save. Propagation usually completes within 5-30 minutes.

7. **Verify in Render:** the Custom Domains section will turn green when DNS resolves and SSL is provisioned. Render handles SSL automatically via Let's Encrypt; you don't have to do anything.

### Updating the site after deployment

Once set up, deployment is automatic on every git push:

```bash
# Edit a file
git add .
git commit -m "Description of change"
git push
```

Render rebuilds and republishes in ~30 seconds.

## v1 plans (not in this version, but useful to know)

When the full v1 site replaces this v0:

- **Multi-page site** with /walkthrough, /install, /about, /method, /primer, /notes per the architecture specs
- **Branded design** using whatever Shannon delivers (logo, palette, type if different from current)
- **Real product images** from Walkthrough App Store screenshots + Cowork screenshots
- **Real testimonials** once they exist
- **Possibly a small backend** (Render Web Service) for forms, Stripe checkout integration, Plus tier intake questionnaire
- **Blog / content surface** at /blog for the Field Notes archive (or Beehiiv-hosted; TBD)

The v0 here is intentionally minimal so v1 is a fresh build, not a refactor.

## Notes

- **No build step on purpose.** No npm install, no Webpack, no Vite. Pure HTML/CSS that any browser renders directly. Easy to maintain, fast to deploy, hard to break.
- **No JS dependencies.** Beehiiv's iframe handles its own form; otherwise no JavaScript on the page. Faster load, no third-party tracking unless we add it explicitly.
- **Mobile-first responsive.** The CSS is structured with mobile defaults and `@media (min-width: 760px)` breakpoints for desktop layout.
- **SVG favicon inline.** No separate favicon file to deploy; it's a data URI in the `<head>`. Renders as a walnut-colored "L" in browser tabs.
