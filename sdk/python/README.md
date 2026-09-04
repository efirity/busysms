# BusySMS for Python

Dependency-free client for the BusySMS API. Python 3.9+.

```bash
pip install .
```

Or copy `busysms.py` into your project; it imports only the standard library.

```python
from busysms import BusySMS, PaymentRequired

sms = BusySMS("bsk_live_...")     # a key from busysms.net/dashboard
hit = sms.wait_for_code(timeout=180)
print(hit["code"] if hit else "nothing arrived")
```

`wait_for_code` returns only a code that arrives after the call — never the one
already on record. See the module docstring and the repository README for why
that matters.

Methods: `account()`, `devices()`, `numbers()`, `latest_code()`,
`wait_for_code()`. Errors: `AuthError`, `PaymentRequired` (billing, HTTP 402),
`BusySMSError`.
