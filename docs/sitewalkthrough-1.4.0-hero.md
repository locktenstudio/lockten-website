# sitewalkthrough.com: the 1.4.0 hero, ready to apply

**Status: NOT APPLIED.** The served page still carries the 1.3.0
voice-first hero, which is correct while 1.3.0 is what is on the stores.
On 1.4.0 release day, apply the diff below to `sitewalkthrough.html` and
push. It is one commit.

1.4.0 is the camera-first release (ratified 2026-09-05): the walkthrough
opens in a camera, the shutter is the primary action, and voice annotates
the shot instead of carrying the whole capture. The hero has to say that,
or the page sells a product the app no longer is.

**Scope note.** This applies to `sitewalkthrough.html` only, the page at
the product's own domain. `walkthrough.html` is the lockten.ai copy and
carries the same 1.3.0 hero; Josh is redoing lockten.ai separately, so
decide then whether that copy gets the same flip, a different one, or a
redirect. Do not sweep both in one pass without asking.

## Do not apply this early

Every line below describes behaviour that only exists once 1.4.0 is live
on both stores. If the flip lands before the release, the page is a false
claim in the one place a buyer reads first. Wait for the store listing.

---

## The diff

Three hunks, all in `sitewalkthrough.html`. Copy the "after" text exactly,
including the `<em>` placement, which is what puts the Instrument Serif
italic on the last two words.

### Hunk 1: meta description

```diff
-<meta name="description" content="Walk the site, talk, send. Walkthrough turns a jobsite walk into a clean PDF you text to your sub. Daily logs with the weather filled in, trade lists, punch lists.">
+<meta name="description" content="Shoot the job, say what matters, send. Walkthrough turns a phone full of jobsite photos into a clean PDF you text to your sub, with the photos filed in your own Drive or Dropbox.">
```

### Hunk 2: og:description

```diff
-<meta property="og:description" content="Site reports for builders. No portal. No logins for your subs. Three free reports to try it, every feature unlocked.">
+<meta property="og:description" content="Shoot the job. Say what matters. The report writes itself. No portal, no logins for your subs, photos in your own Drive or Dropbox.">
```

### Hunk 3: the hero headline and subhead

```diff
-          <h1 class="hero-headline">Walk the site. Talk. <em>Send.</em></h1>
-          <p class="hero-subhead">Site reports for builders. No portal. No logins for your subs. Photos to your own Google Drive or Dropbox. Three free reports to try it, every feature unlocked.</p>
+          <h1 class="hero-headline">Shoot the job. Say what <em>matters.</em></h1>
+          <p class="hero-subhead">Open the camera and shoot. Zoom in on the thing you are worried about, say a word about the shots that need one, label them in the words you already use. Photos land in your own Google Drive or Dropbox and on the console on your laptop, and the report writes itself when you want one. Three free reports to try it, every feature unlocked.</p>
```

The headline keeps its three beats and its length: `hero-headline` is
capped at `14ch`, and "Shoot the job. Say what matters." wraps the same
way "Walk the site. Talk. Send." does.

---

## What has to move in the same commit, or shortly after

The hero is the smallest part of the flip. None of these are in the diff
above, because each needs a decision or an asset that does not exist yet.

1. **The hero screenshots.** `#wt-carousel` runs five 1.3.0 shots from
   `assets/screens/`, and the first one is the record screen. A
   camera-first hero that shows a record screen argues with itself.
   Re-shoot at least the first two, re-convert with the ffmpeg flags in
   CLAUDE.md, and rewrite the `labels` array in the inline script at the
   bottom of the page (it still says "Talk while you walk"). Those files
   are shared with `walkthrough.html`, so replacing them in place changes
   both pages; add new files instead if you only want one to move.
2. **How it works.** The three steps are Walk / Talk / Send. Steps 01 and
   02 become Shoot / Say what matters, or the section contradicts the
   hero two screens down.
3. **The "Voice-first, not type-first" card** in `#different`. That card
   is the old identity stated outright. It becomes the photo card, or it
   goes.
4. **The trial sentence.** 1.4.0 counts a photo-only capture against the
   three free walkthroughs once it is saved anywhere, not at generation.
   If the wording changes from "three free reports" to something like
   "three free captures", it changes in all seven pricing places listed
   in CLAUDE.md at once, not just here.
5. **The console section.** Already on this page, and it gets stronger in
   1.4.0 because a zero-word capture's main exits are Save to Drive, Save
   to Dropbox and Manage on the console. Consider promoting it above the
   proof band on release day.
6. **`llms.txt`** is lockten.ai's file and still describes Walkthrough as
   walk-and-talk, pointing at `lockten.ai/walkthrough`. It belongs to the
   lockten.ai rework, not to this flip, but it will be wrong the same day.
7. **The store listings and screenshots** are the gate on all of it. The
   site should not flip before they do.

---

## Why this wording

- "Shoot the job" is the reflex the release is chasing. The trigger for
  the whole direction was a builder reaching for another app for a photo
  job, so the first three words have to be about photos.
- "Say what matters" keeps voice in the product without promising a
  speech. Narration is a toggle in 1.4.0, so the hero cannot imply that
  talking is the price of entry.
- "The report writes itself" is the payoff, and it is the honest version
  of it: generation is optional on Done in 1.4.0, so the report is
  something the app will do, not something it makes you do.
- "Label them in the words you already use" is the trade-vocabulary
  ruling stated for a buyer. It is a real differentiator against tools
  with a fixed trade list, and it costs one clause.
