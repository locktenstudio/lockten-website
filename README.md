# lockten.ai

The live marketing website for **Lock Ten Studio**, maker of AI tools for custom builders (Walkthrough and The Install).

Static HTML + CSS, **no build step**. Hosted on Render, auto-deploys on every push to `main`. Custom domain: **lockten.ai**.

## Quick facts

- **Deploy:** `git push` to `main`, Render rebuilds in ~30s to 2min. No build command, publish directory is the repo root.
- **Pages:** `index.html` (home), `walkthrough.html`, `install.html` (staged, not linked), `primer.html` + `primer-thanks.html`, `help.html`, `privacy.html`, `terms.html`.
- **Styling:** `styles.css` holds global tokens and styles; each page has its own scoped `<style>` block for page-specific components.
- **Design system:** Lock Ten. Gate blue `#1C71C1`, deep navy `#0C1B38`, cool-grey neutrals, white ground. Instrument Serif / Geist / Geist Mono, self-hosted in `fonts/`.
- **Analytics:** Cloudflare Web Analytics beacon on every page (cookieless).
- **No JS framework, no dependencies.** A little inline vanilla JS for scroll reveals; Beehiiv forms load their own embeds.

## For future edits

**Read `CLAUDE.md`** in this repo first. It documents pricing (the single-source-of-truth spots), the App Store launch state, the contact-email convention, the staged Install page caveat, the Beehiiv form IDs, and where the design specs live. It's the operational guide for making changes safely.

Repo: `github.com/locktenstudio/lockten-website`. Page design specs: `G:\My Drive\AI Business\Deliverables\2. Lockten.ai Website\`.
