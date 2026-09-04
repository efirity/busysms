# BusySMS for Node.js

Dependency-free client for the BusySMS API. Node 18+.

```bash
npm install .
```

Or copy `busysms.mjs` into your project; it uses only built-in `fetch`.

```js
import { BusySMS } from "busysms";

const sms = new BusySMS(process.env.BUSYSMS_API_KEY);
const hit = await sms.waitForCode({ timeoutMs: 180_000 });
console.log(hit ? hit.code : "nothing arrived");
```

`waitForCode` resolves only with a code that arrives after the call — never the
one already on record. See the module comment and the repository README for why
that matters.

Methods: `account()`, `devices()`, `numbers()`, `latestCode()`,
`waitForCode()`. Errors: `AuthError`, `PaymentRequired` (billing, HTTP 402),
`BusySMSError`.
