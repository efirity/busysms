"""
End to end: pick a number that can actually receive, then wait for the code.

    BUSYSMS_API_KEY=bsk_live_... python examples/wait_for_code.py

Run it, then trigger a login somewhere that texts one of your verified numbers.
The ordering matters: the wait starts BEFORE you ask the site to send anything,
because wait_for_code only accepts a code that arrives after the call, so
starting it afterwards can miss the one you asked for.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "sdk", "python"))

from busysms import AuthError, BusySMS, PaymentRequired  # noqa: E402

key = os.environ.get("BUSYSMS_API_KEY")
if not key:
    print("Set BUSYSMS_API_KEY. Create a key at https://busysms.net/dashboard", file=sys.stderr)
    raise SystemExit(1)

sms = BusySMS(key)

try:
    numbers = sms.numbers()
    if not numbers:
        print("No numbers yet. Install the Android app, sign in, and verify a SIM.", file=sys.stderr)
        raise SystemExit(1)

    print("Your numbers:")
    for n in numbers:
        state = "ready" if n["canReceive"] else f"cannot receive: {n.get('reason')}"
        print(f"  {n['phone']}  {state}")

    ready = next((n for n in numbers if n["canReceive"]), None)
    if not ready:
        print("\nNone can receive right now. Open the app and start the gateway.", file=sys.stderr)
        raise SystemExit(1)

    print(f"\nWaiting up to 3 minutes for a code on {ready['phone']}…")
    print("Trigger the login now.")

    hit = sms.wait_for_code(timeout=180, device_id=ready["deviceId"])
    if not hit:
        # Deliberately not falling back to the latest code on record: it is
        # probably from a previous attempt, and spending a login attempt on a
        # used code is worse than reporting nothing.
        print("\nNothing arrived. Check the site is texting that exact number.")
        raise SystemExit(2)

    message = hit.get("message") or {}
    print(f"\nCode: {hit['code']}")
    print(f"From: {message.get('serviceLabel') or message.get('service') or 'unknown sender'}")

except PaymentRequired as err:
    print(f"\nBilling: {err}\nResolve it at {err.billing_url}", file=sys.stderr)
    raise SystemExit(3) from None
except AuthError as err:
    print(f"\nKey rejected: {err}", file=sys.stderr)
    raise SystemExit(4) from None
