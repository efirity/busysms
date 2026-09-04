"""
BusySMS API client — read verification codes from phones you own.

No dependencies. The standard library is enough for four HTTP calls, and a
client you can read in one sitting is worth more than one that pulls a tree of
packages into somebody's build.

    from busysms import BusySMS, PaymentRequired

    sms = BusySMS("bsk_live_...")          # key from busysms.net/dashboard
    for n in sms.numbers():
        print(n["phone"], "ready" if n["canReceive"] else n["reason"])

    code = sms.wait_for_code(timeout=180)  # blocks until one arrives
    print(code["code"] if code else "nothing arrived")

THE ONE RULE WORTH KNOWING: `wait_for_code` returns only a code that arrives
AFTER you call it. It never hands back the one that was already sitting there.
That is deliberate on the server, and this client keeps the guarantee — see the
method's own docstring for why reusing an old code is worse than getting none.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

__all__ = ["BusySMS", "BusySMSError", "AuthError", "PaymentRequired"]

DEFAULT_BASE_URL = "https://busysms.net"

# The server caps a single long poll at 90 seconds. Asking for more in one
# request does not extend it, so a longer wait is several polls in a row.
MAX_POLL_MS = 90_000


class BusySMSError(Exception):
    """Any non-2xx answer from the API."""

    def __init__(self, message: str, status: int, body: Any = None) -> None:
        super().__init__(message)
        self.status = status
        self.body = body


class AuthError(BusySMSError):
    """The key is missing, wrong, or revoked."""


class PaymentRequired(BusySMSError):
    """
    Reading codes needs an active trial or subscription (HTTP 402).

    Its own class because it is the one error that is not a bug: the key is
    valid and the request was well formed, and retrying will never fix it.
    `billing_url` is where a human resolves it.
    """

    def __init__(self, message: str, status: int, body: Any = None) -> None:
        super().__init__(message, status, body)
        self.billing_url = (body or {}).get("billingUrl", "https://busysms.net/dashboard")


class BusySMS:
    """A thin client over the BusySMS REST API, scoped to your own devices."""

    def __init__(self, api_key: str, base_url: str = DEFAULT_BASE_URL, timeout: float = 100.0) -> None:
        if not api_key:
            raise ValueError("an API key is required — create one at busysms.net/dashboard")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    # ---- HTTP ------------------------------------------------------------
    def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        query = {k: v for k, v in (params or {}).items() if v is not None}
        url = f"{self.base_url}{path}"
        if query:
            url += "?" + urllib.parse.urlencode(query)
        req = urllib.request.Request(url, headers={"authorization": f"Bearer {self.api_key}"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as res:
                return json.loads(res.read().decode("utf-8") or "{}")
        except urllib.error.HTTPError as err:
            raw = err.read().decode("utf-8", "replace")
            try:
                body = json.loads(raw)
            except ValueError:
                body = {"error": raw[:200]}
            message = body.get("error") or f"request failed ({err.code})"
            if err.code == 402:
                raise PaymentRequired(message, err.code, body) from None
            if err.code in (401, 403):
                raise AuthError(message, err.code, body) from None
            raise BusySMSError(message, err.code, body) from None

    # ---- Reads -----------------------------------------------------------
    def account(self) -> dict:
        """Your organisation and its billing state, including `canReadCodes`."""
        return self._get("/api/v1/account")

    def devices(self) -> list[dict]:
        """
        Every enrolled phone: deviceId, name, phone, online, paused,
        numberVerified, lastSeenAt.
        """
        return self._get("/api/v1/devices").get("devices", [])

    def numbers(self) -> list[dict]:
        """
        The numbers only, with `canReceive` and a `reason` when it is False.

        Prefer this over `devices()` when you are choosing where to expect a
        code: a number that is verified and billed but whose gateway is off
        looks identical to a working one in any list that reports only
        `active`, and picking it means waiting for a code that cannot arrive.
        """
        return self._get("/api/v1/numbers").get("numbers", [])

    def latest_code(self, device_id: str | None = None, service: str | None = None) -> dict | None:
        """
        The most recent code on record, which may be old. Returns None when
        there is none. Check `receivedAt` against whatever you are logging into
        before you trust it.
        """
        res = self._get("/api/v1/codes", {"timeoutMs": 0, "deviceId": device_id, "service": service})
        return res if res.get("code") else None

    def wait_for_code(
        self,
        timeout: float = 120.0,
        device_id: str | None = None,
        service: str | None = None,
    ) -> dict | None:
        """
        Block until a code ARRIVES, then return {"code", "message"}.

        Returns None if nothing arrived before `timeout`. It will not fall back
        to an earlier code, and neither should you: an OTP you have already
        seen has very likely been used, and submitting a spent code burns one
        of the attempts most sites allow you.

        A single server poll lasts at most 90 seconds, so longer waits are
        several polls in a row. Each new poll only accepts codes newer than
        itself, which is what keeps the guarantee above intact across them.
        """
        deadline = time.monotonic() + timeout
        while True:
            remaining_ms = int(max(0.0, deadline - time.monotonic()) * 1000)
            if remaining_ms <= 0:
                return None
            res = self._get(
                "/api/v1/codes",
                {"timeoutMs": min(remaining_ms, MAX_POLL_MS), "deviceId": device_id, "service": service},
            )
            if res.get("code"):
                return res
