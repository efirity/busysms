# When no code arrives

Call `diagnose_my_gateway` first. Its fields map to one cause each, and the
order below is the order to check them, because each state makes the ones after
it irrelevant.

| State | What it means | What to tell the user |
|---|---|---|
| `enrolled` is 0 | The app is not on any phone yet | Install BusySMS from Google Play on the phone holding the SIM, then sign in with the same account |
| `verified` is 0 | The app is installed but no SIM is confirmed | Open the app and complete SIM verification. Codes to an unverified number are never captured |
| `verifyPending` above 0 | A verification is mid-flight | Wait for the confirmation SMS on the handset, then retry |
| `online` is 0 | The phone is not reporting in | Open the app and start the gateway. Keep the persistent notification, allow SMS and notification permissions, and set battery use to unrestricted. On Xiaomi, Oppo and OnePlus also enable Autostart |
| `canReadCodes` is false | Trial ended with no active subscription | Reads return `402 payment_required` until billing is set up, on the web dashboard. Retrying will not help |
| Everything healthy, still nothing | The service is texting a number that is not the verified one, or the message is not recognised as a verification | Check which number the service has on file. Use `list_messages` to see whether anything arrived at all |

## Distinguishing "not captured" from "not arrived"

`list_messages` shows what BusySMS actually holds. If it is empty for the
window in question, the SMS never reached a verified SIM on an online phone.
If it holds the message but `get_latest_code` returns nothing useful, the text
did not parse as a verification code, which is worth reporting rather than
guessing at digits in the body.

## What not to do

- Do not retry `wait_for_code` in a loop without telling the user. Each wait can
  hold for up to 90 seconds, and silence looks like a hang.
- Do not fall back to an older code when a wait times out. It is very likely
  spent, and submitting it can burn a login attempt.
- Do not suggest a different phone number or a rented number. The product only
  reads SIMs the user owns and has verified.
- Do not offer to remotely start the gateway. The server can ask a phone to
  start, with a notification the person taps, but nothing flips it from here.
