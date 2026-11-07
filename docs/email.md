# Email

The **Email** page (sidebar → Prospecting → Email, or People → Email on a phone) sends one message to many contacts from the owner's own Gmail. Each email goes out as a normal message from the owner, and replies land in their inbox.

## How it works

1. **Who gets it.** Pick Businesses, Specialists or Website sign-ups, search, and tick people. "Email these" on the Businesses page selects every business in the current list that has an email address.
2. **Message.** Start from a template and edit it. Fill-ins: `{first name}`, `{practice}`, `{city}`, `{my name}`. Choose **Plain** (reads like a personal note) or the **Ivory & Slate** design.
3. **Send.** Send a test to yourself first, then send. Or save the emails as Gmail drafts, or download a mail-merge file.

Each business that is emailed gets an email touch in the Touch log and moves to Contacted.

## Rules the page enforces

- **Daily limit.** 50 a day by default, up to 100. Anything over the limit stays selected for the next day.
- **Mailing address and unsubscribe link** are added to the bottom of every email. Sending is blocked until the address is filled in under Sender details.
- **Do not email.** Anyone on the list is always skipped, in sends, drafts and the mail-merge file. One email per address, even if it appears on several records.
- **No health information.** Words such as "diagnosis", "date of birth" or "medical record" block sending. Unfilled `[brackets]` and unknown fill-ins block it too.
- **Demo mode never sends.**
- **Test first.** A blast is allowed only after a test send in the same visit, and again after the message changes.
- **Failures.** If Gmail refuses one email, it's logged as failed and the rest continue. If Gmail doesn't answer, sending stops and asks you to check your Sent folder, because that email may have gone out.

## Templates

| Template | Look | For |
| --- | --- | --- |
| Introduction | Plain | First email to a practice you found |
| Follow-up | Plain | A nudge about a week later |
| Welcome | Ivory & Slate | New website sign-ups |
| Update or event | Ivory & Slate | News or an event (fill in the `[brackets]`) |
| Finish your storefront | Ivory & Slate | A few days after Welcome: the Referral Bridge sign-in link and a nudge to finish their storefront |
| Beta invite | Plain | Inviting someone to Referral Bridge |

Website sign-ups get Welcome first, then Finish your storefront a few days later. Both are sent by hand from the Email page (Website sign-ups → select → template → send). They aren't automatic: the CRM only runs while it's open, and scheduled bots never send email (see docs/decisions.md). The storefront email links to the sign-in portal. The storefront page itself (photo, services, who they serve) isn't built yet.

## Unsubscribes

The link in each email opens `https://eco-bridge.cc-christophercontreras.workers.dev/unsubscribe?e=<address>` (the page is `website/public/unsubscribe.html` in the EcoBridge repo). It sends the address to Formspree form `xgaaqqby` with the subject "Unsubscribe request" (the address is in the `unsubscribe_email` field, so the website's thank-you autoresponse isn't sent to it), so it arrives in the owner's inbox. Add it to Do not email within 10 days, either by pasting it on the Email page or by importing the Formspree export. People can also reply "unsubscribe".

## Website sign-ups

**Import website sign-ups** reads the CSV export from Formspree (form `xgaaqqby`, fields `name`, `email`, `role`, `company`, `message`, `updates`).

- People who ticked "I'd like to get EcoBridge updates" (`updates` = yes) are added as Website sign-ups, tagged "Website".
- People who didn't tick it are left out unless you choose to add them. They're marked "Didn't tick updates" and should get personal replies, not blasts.
- Anyone already on the list is skipped. Unsubscribe requests go to Do not email.

## Publishing (Gmail connection)

The page reaches Gmail through the artifact's `mcp` capability, using the viewer's Gmail connector in claude.ai. When republishing `src/index.html`:

1. The owner connects **Gmail** in claude.ai Settings → Connectors.
2. Declare the capabilities as the full set: the existing ones (`db`, `sample`, `downloads`) plus
   `mcp: {servers: [{server: "Gmail", tools: [<send tool>, "create_draft"]}]}`.
   Use the Gmail connector's real tool names from the publishing session's tool list. The page picks a tool named like `send_message`/`send_email` to send, or `create_draft` followed by `send_draft`, and falls back to drafts only.
3. The page reads each tool's input schema at view time (`describeTool`) and fills `to`, `subject`, the text body and, for the designed look, the HTML body. If Gmail asks for a field it doesn't recognize, it stops and says so instead of guessing.
4. Send a test to yourself and check it arrived, with the address and unsubscribe link at the bottom.

Outside claude.ai (for example the Supabase portal), the page can't reach Gmail. It says so and still offers the mail-merge download.
