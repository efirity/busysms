/**
 * BusySMS API client — read verification codes from phones you own.
 *
 * No dependencies. Node 18+ has fetch, and four HTTP calls do not need a
 * package tree behind them.
 *
 *   import { BusySMS, PaymentRequired } from "./busysms.mjs";
 *
 *   const sms = new BusySMS(process.env.BUSYSMS_API_KEY);
 *   for (const n of await sms.numbers()) {
 *     console.log(n.phone, n.canReceive ? "ready" : n.reason);
 *   }
 *
 *   const hit = await sms.waitForCode({ timeoutMs: 180_000 });
 *   console.log(hit ? hit.code : "nothing arrived");
 *
 * THE ONE RULE WORTH KNOWING: waitForCode resolves only with a code that
 * arrives AFTER you call it. It never hands back the one already sitting
 * there. That is deliberate on the server, and this client keeps the
 * guarantee — see the method for why an old code is worse than none.
 */

export const DEFAULT_BASE_URL = "https://busysms.net";

/** The server caps one long poll at 90s; a longer wait is several in a row. */
const MAX_POLL_MS = 90_000;

export class BusySMSError extends Error {
  constructor(message, status, body) {
    super(message);
    this.name = "BusySMSError";
    this.status = status;
    this.body = body;
  }
}

/** The key is missing, wrong, or revoked. */
export class AuthError extends BusySMSError {
  constructor(...args) {
    super(...args);
    this.name = "AuthError";
  }
}

/**
 * Reading codes needs an active trial or subscription (HTTP 402).
 *
 * Its own class because it is the one error that is not a bug: the key is
 * valid and the request was well formed, and retrying will never fix it.
 */
export class PaymentRequired extends BusySMSError {
  constructor(message, status, body) {
    super(message, status, body);
    this.name = "PaymentRequired";
    this.billingUrl = body?.billingUrl || "https://busysms.net/dashboard";
  }
}

export class BusySMS {
  /**
   * @param {string} apiKey from busysms.net/dashboard
   * @param {{ baseUrl?: string }} [opts]
   */
  constructor(apiKey, opts = {}) {
    if (!apiKey) throw new Error("an API key is required — create one at busysms.net/dashboard");
    this.apiKey = apiKey;
    this.baseUrl = (opts.baseUrl || DEFAULT_BASE_URL).replace(/\/+$/, "");
  }

  async #get(path, params = {}) {
    const url = new URL(this.baseUrl + path);
    for (const [k, v] of Object.entries(params)) {
      if (v !== undefined && v !== null) url.searchParams.set(k, String(v));
    }
    const res = await fetch(url, { headers: { authorization: `Bearer ${this.apiKey}` } });
    const body = await res.json().catch(() => ({}));
    if (res.ok) return body;
    const message = body?.error || `request failed (${res.status})`;
    if (res.status === 402) throw new PaymentRequired(message, res.status, body);
    if (res.status === 401 || res.status === 403) throw new AuthError(message, res.status, body);
    throw new BusySMSError(message, res.status, body);
  }

  /** Your organisation and its billing state, including `canReadCodes`. */
  account() {
    return this.#get("/api/v1/account");
  }

  /** Every enrolled phone: deviceId, name, phone, online, paused, numberVerified. */
  async devices() {
    return (await this.#get("/api/v1/devices")).devices ?? [];
  }

  /**
   * The numbers only, with `canReceive` and a `reason` when it is false.
   *
   * Prefer this when choosing where to expect a code: a number that is
   * verified and billed but whose gateway is off looks identical to a working
   * one in any list reporting only `active`, and picking it means waiting for
   * a code that cannot arrive.
   */
  async numbers() {
    return (await this.#get("/api/v1/numbers")).numbers ?? [];
  }

  /**
   * The most recent code on record, which may be old, or null.
   *
   * Check `message.receivedAt` against whatever you are logging into before
   * trusting it.
   */
  async latestCode({ deviceId, service } = {}) {
    const res = await this.#get("/api/v1/codes", { timeoutMs: 0, deviceId, service });
    return res.code ? res : null;
  }

  /**
   * Resolve when a code ARRIVES, or null at `timeoutMs`.
   *
   * It will not fall back to an earlier code, and neither should you: an OTP
   * you have already seen has very likely been used, and submitting a spent
   * code burns one of the attempts most sites allow.
   *
   * One server poll lasts at most 90 seconds, so a longer wait is several in
   * a row; each accepts only codes newer than itself, which is what keeps the
   * guarantee intact across them.
   */
  async waitForCode({ timeoutMs = 120_000, deviceId, service } = {}) {
    const deadline = Date.now() + timeoutMs;
    for (;;) {
      const remaining = deadline - Date.now();
      if (remaining <= 0) return null;
      const res = await this.#get("/api/v1/codes", {
        timeoutMs: Math.min(remaining, MAX_POLL_MS),
        deviceId,
        service,
      });
      if (res.code) return res;
    }
  }
}
