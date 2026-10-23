# BusySMS

**Turn phones you already own into an SMS gateway, and read their verification
codes from your own code, or from an AI agent.**

BusySMS runs on your Android phones and captures the verification and OTP
messages that arrive on your own SIMs. You read them back over a REST API, over
MCP, or let the Chrome extension fill them into a login form for you.

It is not a rented-number pool. The numbers are yours, the SIMs are yours, and
nobody else's messages are ever in reach.

- Website — <https://busysms.net>
- Android app — [Google Play](https://play.google.com/store/apps/details?id=net.busysms.app)
- Chrome OTP autofill — [Chrome Web Store](https://chromewebstore.google.com/detail/busysms-otp-autofill/ldfcokkihcbnemkcppecagnelblnebbg)
- MCP endpoint — `https://busysms.net/mcp`

This repository is the Claude Code plugin: the MCP connection and the
`busysms-otp` skill. The service itself is closed source.

## Use it from Claude Code

```
/plugin marketplace add efirity/busysms
/plugin install busysms@busysms
```

The first line points Claude Code at this repository; the second installs
from it.

That gives you two things:

- **The MCP server**, connected over OAuth. You sign in once in the browser;
  no key is pasted anywhere and none is stored in this repo.
- **The `busysms-otp` skill**, which teaches the model the workflow that
  actually works: how to wait for a code rather than reuse a stale one, how to
  pick the right phone when you have several, and what to say when nothing
  arrives.

Then ask for what you want in plain language.

> Wait for my verification code and tell me when it lands.

> Why is nothing arriving on my second SIM?

### A credential you give an agent cannot spend or send

An API key used over MCP is **read-only and scope-checked per tool**. It cannot
mint another API key, cannot send an SMS or an email, and cannot reach any
operator tool. A key issued with the narrow `codes:read` scope reads codes and
cannot even list your phone numbers.

Anything that spends money or creates a credential requires a real sign-in, not
a key. So handing a key to an agent gives it exactly the reach you intended.

## Use it from your own code

The same codes are available over a plain REST API with an API key from
<https://busysms.net/dashboard>. Endpoints, long-polling and error handling are
documented at <https://busysms.net/docs> and
<https://busysms.net/sms-gateway-api>.

## The one rule worth knowing

`wait_for_code` returns **only a code that arrives after you call it**. On
timeout it returns nothing rather than the code that was already there.

That is deliberate. An OTP you have already seen has very likely been used, and
submitting a spent code burns one of the handful of attempts most sites allow.
If you want the newest code whatever its age, ask for that explicitly with
`latest_code`, and check its timestamp against what you are logging into.

So: start the wait, *then* trigger the login.

## API

Base URL `https://busysms.net`. Send your key as `Authorization: Bearer bsk_live_…`.

| Endpoint | Returns |
|---|---|
| `GET /api/v1/account` | your organisation and its billing state |
| `GET /api/v1/devices` | every enrolled phone, with `online` and `numberVerified` |
| `GET /api/v1/numbers` | the numbers only, with `canReceive` and a `reason` |
| `GET /api/v1/codes` | the latest code, or a long poll with `timeoutMs` |

`GET /api/v1/codes` takes `timeoutMs` (up to 90000, where 0 means "answer
now"), and optional `deviceId` and `service` filters. A single poll lasts at
most 90 seconds; chain polls for longer waits, which is safe because each one
only accepts codes newer than itself.

**Reading codes requires an active BusySMS plan on the account.** Without one
the API answers `402` with a `billingUrl`. Treat it as its own case rather than
a generic failure: retrying will never fix it.

## What is captured

Verification and OTP messages only, on SIMs you have verified. Not your inbox.
Everything is scoped to your own organisation.

## License

MIT. See [LICENSE](LICENSE).
