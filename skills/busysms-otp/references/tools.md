# Tool contracts

The five tools this workflow uses, with the behaviour that is not obvious from
the schema. Every one is scoped to the caller's own organisation.

## `wait_for_code`

Long-polls for the **next** code.

| Argument | Meaning |
|---|---|
| `timeoutMs` | how long to wait, default 60000, capped at 90000 |
| `deviceId` | restrict to one enrolled device |
| `service` | restrict to codes whose sender or body matches a service |

Returns `{ ok, code, message, note }`. On timeout, `code` is `null` and `note`
explains that none arrived. It never falls back to an earlier code, so a null
means "none arrived", not "none exists".

## `get_latest_code`

One shot, no waiting. Returns `{ ok, code, message }` for the most recent code,
which may be hours old. Read `message.receivedAt` before trusting it against a
login the user started a moment ago. Takes the same `deviceId` and `service`
filters.

## `list_my_devices`

Each device carries `numberVerified`, `online`, `sharing`, `phone`, `name` and
`lastSeenAt`. Codes are only captured on a device that is verified, online and
sharing. Use it to pick a `deviceId`, or to tell the user which phone to go and
wake up.

## `list_messages`

Recent captured messages, newest first, with `deviceId`, `service` and `limit`
(max 200). Useful for "did anything arrive at all?" when a wait times out.
Verification messages only.

## `diagnose_my_gateway`

The one call that explains silence. Returns live counts of `enrolled`,
`verified`, `online` and `verifyPending`, plus `canReadCodes`, `billingStatus`,
a device summary and `tips` written for the user. Prefer it over guessing from
the other tools.

## Not part of this workflow

`create_api_key` returns a one-time `revealUrl` for the browser and never the
secret itself, so never ask the user to paste a key back. `send_sms_to_me` and
`send_email_to_me` deliver only to the caller's own contact details.
