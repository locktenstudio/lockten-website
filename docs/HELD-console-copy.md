# Held console copy (sitewalkthrough.html)

Publish only after the walkthrough backend branch `feat/console-open-to-all` is live.

These three strings promise that the console comes with every account and that
meeting notes and the punch list are Pro in the console. That is not what ships
today, so they were deliberately left out of the wider-door copy pass on branch
`copy/wider-door-sitewalkthrough` (2026-09-21). The safe console changes on that
branch (the `The console (beta)` label and the `What you captured on site, open
in a browser back at the desk.` section sub) are already applied.

## 1. Console note, replaces the existing `p.console-note`

Current text on the page, unchanged for now:

```
The console is included with the app. Same sign-in, nothing separate to buy.
```

Replacement, ready to paste:

```html
<p class="console-note">The console is in beta and comes with your account. Same six-digit code sign-in, nothing separate to buy. Meeting notes and the punch list are Pro in the console, the same as they are in the app.</p>
```

## 2. New console FAQ, visible HTML

Insert after the Android FAQ (`Does Walkthrough work on Android?`) in the
`div.faq` block:

```html
<details><summary>Is there a version I can use on a laptop?</summary><p>Yes. The console is a web version of what you captured, in a browser. It is in beta, it comes with your account, and you sign in with the same six-digit code. Meeting notes and the punch list are Pro there, the same as they are in the app.</p></details>
```

## 3. New console FAQ, FAQPage JSON-LD

Insert in `mainEntity` in the same position as the visible FAQ (immediately
after the Android entry), so the two lists stay in the same order:

```json
    {
      "@type": "Question",
      "name": "Is there a version I can use on a laptop?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Yes. The console is a web version of what you captured, in a browser. It is in beta, it comes with your account, and you sign in with the same six-digit code. Meeting notes and the punch list are Pro there, the same as they are in the app."
      }
    },
```

Both copies of the FAQ must land in the same commit, or the structured data
goes stale.

## Also gated

Any Field Notes or social copy that repeats "the console comes with your
account" waits on the same backend change.
