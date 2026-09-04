/**
 * End to end: pick a number that can actually receive, then wait for the code.
 *
 *   BUSYSMS_API_KEY=bsk_live_... node examples/wait-for-code.mjs
 *
 * Run it, then trigger a login somewhere that texts one of your verified
 * numbers. The point of the ordering below is that the wait starts BEFORE you
 * ask the site to send anything: waitForCode only accepts a code that arrives
 * after the call, so starting it afterwards can miss the one you asked for.
 */
import { BusySMS, PaymentRequired, AuthError } from "../sdk/node/busysms.mjs";

const key = process.env.BUSYSMS_API_KEY;
if (!key) {
  console.error("Set BUSYSMS_API_KEY. Create a key at https://busysms.net/dashboard");
  process.exit(1);
}

const sms = new BusySMS(key);

try {
  const numbers = await sms.numbers();
  if (numbers.length === 0) {
    console.error("No numbers yet. Install the Android app, sign in, and verify a SIM.");
    process.exit(1);
  }

  console.log("Your numbers:");
  for (const n of numbers) {
    console.log(`  ${n.phone}  ${n.canReceive ? "ready" : `cannot receive: ${n.reason}`}`);
  }

  const ready = numbers.find((n) => n.canReceive);
  if (!ready) {
    console.error("\nNone can receive right now. Open the app and start the gateway.");
    process.exit(1);
  }

  console.log(`\nWaiting up to 3 minutes for a code on ${ready.phone}…`);
  console.log("Trigger the login now.");

  const hit = await sms.waitForCode({ timeoutMs: 180_000, deviceId: ready.deviceId });
  if (!hit) {
    // Deliberately not falling back to the latest code on record: it is
    // probably the one from a previous attempt, and spending a login attempt
    // on a used code is worse than reporting nothing.
    console.log("\nNothing arrived. Check the site is texting that exact number.");
    process.exit(2);
  }

  console.log(`\nCode: ${hit.code}`);
  console.log(`From: ${hit.message?.serviceLabel || hit.message?.service || "unknown sender"}`);
} catch (err) {
  if (err instanceof PaymentRequired) {
    console.error(`\nBilling: ${err.message}\nResolve it at ${err.billingUrl}`);
    process.exit(3);
  }
  if (err instanceof AuthError) {
    console.error(`\nKey rejected: ${err.message}`);
    process.exit(4);
  }
  throw err;
}
