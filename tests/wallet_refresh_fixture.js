"use strict";
// Runs the actual inline wallet script in a sandbox with fake DOM, clock and RPC.
// Fixture balances are invented for testing only; no network or wallet is used.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const html = fs.readFileSync(path.join(__dirname, "..", "wallet.html"), "utf8");
const script = html.match(/<script>([\s\S]*?)<\/script>/)[1];
const text = id => html.match(new RegExp(`id="${id}"[^>]*>([^<]*)<`))[1];
let now = "2026-01-02T03:04:05.000Z", mode = "success", calls = [];
const elements = Object.fromEntries(["sol", "vzla", "balance-status"].map(id => [id, {textContent: text(id)}]));
const initial = {sol: elements.sol.textContent, vzla: elements.vzla.textContent, status: elements["balance-status"].textContent};
let click;
elements.refresh = {addEventListener: (event, handler) => { assert.equal(event, "click"); click = handler; }};
class FakeDate extends Date { constructor(...args) { super(...(args.length ? args : [now])); } }
const sandbox = {
  document: {getElementById: id => {assert.ok(elements[id], id); return elements[id];}},
  Date: FakeDate, AbortController, setTimeout: () => 1, clearTimeout: () => {},
  fetch: async (url, options) => {
    const body = JSON.parse(options.body);
    assert.equal(url, "https://solana.api.pocket.network");
    assert.equal(options.method, "POST");
    assert.deepEqual(Object.keys(options.headers), ["content-type"]);
    assert.equal(options.headers["content-type"], "application/json");
    assert.ok(["getBalance", "getTokenAccountsByOwner"].includes(body.method));
    assert.equal(body.params[0], "GGSqpEPw3WDvfqJRj6frvrTz1C2wcUz28Sgfdg2NNJiD");
    if (body.method === "getTokenAccountsByOwner") assert.equal(body.params[1].mint, "GDYcemcZozG9ijhEZioRLRgNMtoxh1BBuV7nvdf1pump");
    calls.push(body.method);
    if (mode === "network") throw new Error("TEST_OFFLINE");
    if (mode === "http" || (mode === "partial" && body.method === "getTokenAccountsByOwner")) return {ok: false, status: 503};
    if (mode === "rpc-error") return {ok: true, json: async () => ({error: {code: -1}})};
    if (mode === "malformed") return {ok: true, json: async () => ({result: {value: null}})};
    const sol = mode === "success2" ? 2000000000 : 12345678900;
    const token = mode === "success2" ? "77.25" : "42.5";
    const result = body.method === "getBalance" ? {value: sol} : {value: [{account: {data: {parsed: {info: {tokenAmount: {uiAmountString: token}}}}}}]};
    return {ok: true, json: async () => ({result})};
  }
};
vm.runInNewContext(script, sandbox, {timeout: 2000});
const state = () => ({sol: elements.sol.textContent, vzla: elements.vzla.textContent, status: elements["balance-status"].textContent});
const run = async value => { mode = value; calls = []; await click(); assert.deepEqual(calls.sort(), ["getBalance", "getTokenAccountsByOwner"].sort()); return state(); };
const hasFailure = data => assert.match(data.status, /لم ينجح تحديث RPC من المتصفح؛ الأرصدة الظاهرة لم تتجدد/);
const hasSuccessSourceAndTime = (data, timestamp) => {
  assert.match(data.status, /آخر قراءة ناجحة من Solana RPC/);
  assert.ok(data.status.includes("https://solana.api.pocket.network"));
  assert.ok(data.status.includes("وقت الاستلام حسب ساعة جهازك: \u2066" + timestamp + "\u2069"));
};

(async () => {
  const scenario = process.argv[2];
  if (scenario === "initial-failure") {
    const failure = await run("http");
    hasFailure(failure);
    assert.equal(failure.sol, initial.sol); assert.equal(failure.vzla, initial.vzla);
    assert.ok(failure.status.endsWith(initial.status));
    assert.match(failure.status, /Nova\/Solana Tracker/);
    assert.match(failure.status, /20 نوفمبر 2026 07:31 UTC/);
  } else if (scenario === "success-failure") {
    const success = await run("success");
    assert.equal(success.sol, "12.3456789"); assert.equal(success.vzla, "42.5");
    hasSuccessSourceAndTime(success, now);
    now = "2026-01-03T06:07:08.000Z";
    const failure = await run("http");
    hasFailure(failure); hasSuccessSourceAndTime(failure, "2026-01-02T03:04:05.000Z");
    assert.equal(failure.sol, success.sol); assert.equal(failure.vzla, success.vzla);
    assert.ok(failure.status.endsWith(success.status)); assert.ok(!failure.status.includes(now));
    const again = await run("network"); assert.equal(again.status, failure.status);
  } else if (scenario === "partial-and-invalid") {
    const success = await run("success");
    now = "2026-01-03T06:07:08.000Z";
    for (const fault of ["partial", "rpc-error", "malformed", "network"]) {
      const failure = await run(fault);
      hasFailure(failure); assert.equal(failure.sol, success.sol); assert.equal(failure.vzla, success.vzla);
      assert.ok(failure.status.endsWith(success.status)); assert.ok(!failure.status.includes(now));
    }
  } else if (scenario === "recovery") {
    const first = await run("success");
    await run("http"); now = "2026-01-03T06:07:08.000Z";
    const next = await run("success2");
    assert.equal(next.sol, "2"); assert.equal(next.vzla, "77.25"); hasSuccessSourceAndTime(next, now);
    assert.ok(!next.status.includes(first.status)); assert.ok(!next.status.includes("لم ينجح"));
    const failure = await run("http"); assert.ok(failure.status.endsWith(next.status));
  } else { throw new Error("Unknown scenario: " + scenario); }
  console.log("PASS", scenario, "(fake RPC only)");
})().catch(e => { console.error(e); process.exitCode = 1; });
