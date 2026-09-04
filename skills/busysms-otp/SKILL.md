---
name: busysms-otp
description: Retrieve a one-time verification code that arrived on a phone the user owns, through their BusySMS gateway. Use when the user is waiting on a login, 2FA or signup code, asks you to check for a code, or says a code has not arrived. Also covers why no code appears — an offline phone, an unverified SIM, or a lapsed trial.
---

# Getting a verification code from the user's own phone

BusySMS captures verification SMS on phones **the user owns**. It is not a
rented-number pool, so the code you fetch belongs to a SIM they control, and
you only ever see their own organisation's devices.

## The one thing to get right

`wait_for_code` returns **only a code that arrives after you call it**. On
timeout it answers `code: null`, never the code that was already sitting
there. That is deliberate: handing back a code the user already used makes
them submit it again, and on a site that counts attempts, that spends one for
nothing.

So the two tools are not interchangeable:

| Tool | Answers with |
|---|---|
| `wait_for_code` | the next code to arrive, or nothing |
| `get_latest_code` | the newest code on record, however old |

**Never reuse a code across attempts, and never type one out that did not come
from a tool result in this conversation.**

## The sequence

1. **Has the code been sent yet?**
   - Not yet: call `wait_for_code` *first*, then tell the user to press send.
     It polls for up to 90 seconds (`timeoutMs`, default 60000).
   - Just now: call `get_latest_code` and check `message.receivedAt`. If it
     predates their attempt, it is the wrong code — call `wait_for_code`.
2. **More than one phone or several codes at once?** Narrow it. Call
   `list_my_devices` to see the verified numbers, then pass `deviceId` for a
   specific handset, or `service` to match the sender.
3. **Nothing arrives?** Call `diagnose_my_gateway`. It returns the live counts
   of enrolled, verified and online devices plus `canReadCodes`, which is the
   whole answer in one call. See `references/troubleshooting.md` for what each
   state means and what to tell the user.

Do not loop `wait_for_code` silently. If the first wait times out, say so and
ask whether to wait again, so the user can re-trigger the SMS instead.

## Scope and privacy, which are not negotiable

- Only the caller's own organisation's devices and messages. Never imply access
  to anyone else's phone.
- Only verification and OTP messages are captured. There is no access to the
  rest of the inbox, so do not offer to read other SMS.
- `send_sms_to_me` and `send_email_to_me` reach only the number and address on
  the caller's own account. They take no recipient, so never promise to message
  anyone else. SMS is capped per hour.
- Reading codes needs an active trial or subscription. Past that, reads return
  `402 payment_required` and the fix is billing, not retrying.

Exact arguments, return shapes and limits: `references/tools.md`.
