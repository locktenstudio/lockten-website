# Material Monitor legal pages: review notes

Branch: `mm-legal`. Files added:

- `materialmonitor-privacy.html` (canonical `https://materialmonitor.app/privacy`)
- `materialmonitor-terms.html` (canonical `https://materialmonitor.app/terms`)

**This is a drafting exercise, not legal advice.** These pages were written by an AI assistant to give a lawyer something concrete to mark up. Nothing here has been reviewed by counsel. Do not publish either page until a lawyer has read it and you have made the business decisions listed below.

Routes are not wired in this branch. Nothing in `sitemap.xml`, `CLAUDE.md` or `render.yaml` was touched.

---

## Decisions that need you or a lawyer

### 1. Governing law and venue (Terms, "Governing law")
Drafted as Maryland law, Maryland courts, as instructed. A lawyer should confirm the venue wording and decide whether to add an arbitration clause, a class action waiver, and a limitations period. Marked with a placeholder note on the page.

### 2. Limitation of liability cap (Terms, "Limitation of liability")
No number is stated. The usual choice for a small SaaS is "the greater of the fees paid in the prior 12 months or $100", but that is your call with counsel, along with the carve outs (fraud, gross negligence, indemnities). Marked with a placeholder note on the page.

### 3. Disclaimers (Terms, "Disclaimers")
Standard "as is" language is drafted. A lawyer should confirm the wording, whether Maryland limits any of it, and whether the "no guarantee that a read is correct" language is strong enough given that the product's core function is reading vendor email. Marked with a placeholder note on the page.

### 4. Subscription, billing and refunds (Terms, "Subscription and cancellation")
Left as a short placeholder per instruction, with an explicit line saying nothing in the terms authorises a charge until the section is complete. You need to decide and then have counsel draft:
- the price and what a company subscription includes;
- renewal, notice before renewal, and whether cancellation is effective immediately or at period end;
- refund policy, including for founding builders;
- what happens to data during a lapse in payment (read only? suspended? deleted?);
- whether the founding builder arrangement is a separate written agreement or a rider on these terms.

### 5. Data retention periods (Privacy, "How long we keep things")
**I assumed these numbers. Confirm or change every one.**

| Item | Assumed |
|---|---|
| Orders, deliveries, photos | Kept while the account is open |
| Vendor email content | Kept alongside the order while the account is open |
| Connected mailbox sign-in tokens | Deleted on disconnect (this one is a stated product fact, not an assumption) |
| Application and server logs | 30 days |
| After account closure | Company data deleted within 30 days |
| Backups | Falls out of routine encrypted backups within a further 35 days |

The 30 day and 35 day figures should be checked against what Render's Postgres backup retention actually is on your plan. If the backup window is longer, the page is wrong and needs the real number.

### 6. Google API Services User Data Policy: Limited Use disclosure (Privacy, "Google user data")
The required sentence is on the page verbatim in a callout box, naming Material Monitor and linking to Google's policy page. Two things to check before you submit for Google's OAuth verification:

- Google's verification reviewers want this disclosure on a **prominent, publicly accessible** privacy page, and they check that the page loads at the exact URL you give them. The route `https://materialmonitor.app/privacy` must be live and indexable before you submit. Both pages are indexable as drafted (no `noindex`).
- Confirm the Gmail scope you actually request is read only, and that the plain English paragraph following the disclosure matches the scope. If the app ever needs a broader scope, the disclosure and that paragraph both change, and Google re-reviews.
- Google may also require a demo video and a security assessment depending on the scope. That is a process question, not a wording question, but it gates the launch of the Gmail connection.

### 7. Microsoft data statement (Privacy, "Microsoft 365 user data")
Microsoft has no equivalent required sentence, so I wrote a parallel plain statement mirroring the Google one. A lawyer should confirm it does not overpromise, and someone should read the Microsoft APIs Terms of Use and the Microsoft Identity Platform policies to check whether publisher verification imposes any specific privacy statement wording on you. If it does, that wording replaces mine.

### 8. Breach notification timing (Privacy, "Security")
The page says we will tell your company "promptly". No number. Maryland's Personal Information Protection Act and several other state laws set specific deadlines, and a business customer will often want a contractual one (72 hours is the common ask). Decide with counsel whether to commit to a number here, in the terms, or in a separate data processing agreement.

### 9. Subprocessor list (Privacy, "Service providers")
Listed: Render, Resend, Anthropic, Microsoft Graph, Google Gmail API, and carrier tracking (17TRACK, UPS, FedEx). Questions:
- Is this list complete? Anything for error monitoring, analytics, session replay, or payments will need adding. The page currently says there is no tracking pixel of our own, which must stay true.
- Do you want to commit to notifying customers before adding a subprocessor? Enterprise customers ask for it; it is a real operational obligation once promised, so it is currently not promised.
- The Anthropic line states that Anthropic's API terms do not permit training on that data. Confirm that is still accurate for the plan and endpoint you are actually calling before publishing.
- The page says data is stored in the United States. Confirm every provider above is configured for US regions, including Resend and the Render database.

### 10. Other things a lawyer should weigh in on
- **Whether you need a Data Processing Agreement.** A builder's office is unlikely to demand one, but vendor mail can contain personal data (names, phone numbers, addresses of homeowners), and once you sell to anyone with a compliance function they will ask.
- **The "who can see your data" promise.** The page says access on our side is limited to the people who run the service and that we do not browse customer data. That is a commitment you have to be able to keep, and ideally log.
- **Human review of AI output.** The privacy page says humans do not read Google or Microsoft mailbox data except with explicit permission, for security, or where required by law. Make sure that stays true operationally, including during debugging. If you ever need to look at a customer's vendor email to fix a parsing bug, you need their permission or a different mechanism.
- **The confirm-before-change carve out.** Terms say an exact tracking number match applies automatically. If that behaviour ever widens, the terms need updating.
- **Children.** Page says not for anyone under 18. Confirm that matches how you want to describe it, since a business tool arguably has no under 18 question at all.
- **Contact address.** Both pages route everything to `info@lockten.ai`. If a jurisdiction requires a postal address on a privacy policy for your customer base, one will need adding.

---

## Notes on how the pages were built

- Both pages use the `body.mm` copper on slate skin, the product lockup in the header linking to `https://materialmonitor.app/`, and the same footer as `materialmonitor.html`. Studio links are absolute `https://lockten.ai/...`.
- Reading copy is set at `1.06rem` (18px against the 17px root), per the Material Monitor page rule.
- No em dashes anywhere, per house style.
- The footer lockup line drops the "Cabin John, Maryland" location string that `materialmonitor.html` carries, to keep client and place names out of these files. Add it back if you want the pages to match the product page exactly.
- Scanned case insensitively for client, vendor and personal names. No hits.
- Neither page carries a "draft pending review" banner, per instruction. The review happens on this branch.
