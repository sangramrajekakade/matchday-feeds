// MATCHDAY UNITED — slash-command handler (Discord "Interactions Endpoint URL").
// Answers /news /scores /fixtures /table /scorers /quiz /help from the public data file in the GitHub repo.
// Needs ONE setting: DISCORD_PUBLIC_KEY (the app's PUBLIC key — not a secret). No bot token, no API keys.
// Works on Deno Deploy (Deno.serve) and Cloudflare Workers (export default { fetch }).

const REPO_RAW = "https://raw.githubusercontent.com/sangramrajekakade/matchday-feeds/main/data";
const GOLD = 0xd5a83b, RED = 0xd94b42, GREEN = 0x3caa6e, BLUE = 0x4678dc, PURPLE = 0x8c5ad2;
const FOOTER = { text: "MATCHDAY UNITED · independent fan community · data: football-data.org" };
const LEAGUES = { PL: "Premier League", PD: "La Liga", SA: "Serie A", BL1: "Bundesliga", FL1: "Ligue 1", CL: "Champions League" };

// ── signature check (Discord rejects endpoints that don't verify) ─────────────────────────────────
const hex = (h) => new Uint8Array(h.match(/.{2}/g).map((b) => parseInt(b, 16)));
let keyPromise;
async function verify(req, body, publicKey) {
  const sig = req.headers.get("x-signature-ed25519"), ts = req.headers.get("x-signature-timestamp");
  if (!sig || !ts || !publicKey) return false;
  keyPromise ||= crypto.subtle.importKey("raw", hex(publicKey), { name: "Ed25519" }, false, ["verify"]);
  try {
    return await crypto.subtle.verify("Ed25519", await keyPromise, hex(sig), new TextEncoder().encode(ts + body));
  } catch { return false; }
}

// ── data ─────────────────────────────────────────────────────────────────────────────────────────
let cache = { at: 0, snap: null, quiz: null };
async function data() {
  if (Date.now() - cache.at < 60_000 && cache.snap) return cache;
  const bust = `?t=${Math.floor(Date.now() / 60_000)}`;
  const [snap, quiz] = await Promise.all([
    fetch(`${REPO_RAW}/snapshot.json${bust}`).then((r) => (r.ok ? r.json() : null)).catch(() => null),
    cache.quiz ? cache.quiz : fetch(`${REPO_RAW}/quiz.json`).then((r) => (r.ok ? r.json() : [])).catch(() => []),
  ]);
  cache = { at: Date.now(), snap: snap || cache.snap || {}, quiz };
  return cache;
}

const istDate = (d = new Date()) => new Date(d.getTime() + 330 * 60_000).toISOString().slice(0, 10);
const opt = (i, name) => i.data.options?.find((o) => o.name === name)?.value;
const embed = (title, description, color = GOLD, extra = {}) => ({ title, description, color, footer: FOOTER, ...extra });
const line = (m) => {
  const score = m.hs !== null && m.hs !== undefined ? `**${m.hs}–${m.as}**` : "v";
  const live = ["IN_PLAY", "PAUSED"].includes(m.status) ? " 🔴 LIVE" : m.status === "FINISHED" ? " · FT" : "";
  return `\`${m.ist.split("· ")[1] || m.ist}\` ${m.home} ${score} ${m.away}${live}`;
};
const byComp = (ms) => {
  const g = {};
  for (const m of ms) (g[m.compName || m.comp] ||= []).push(m);
  return Object.entries(g).map(([name, list]) => ({ name, value: list.slice(0, 10).map(line).join("\n").slice(0, 1024), inline: false })).slice(0, 10);
};
const stale = (snap) => (snap.updated ? `Updated ${new Date(snap.updated).toLocaleString("en-IN", { timeZone: "Asia/Kolkata", hour: "numeric", minute: "2-digit", day: "numeric", month: "short" })} IST` : "");

// ── commands ─────────────────────────────────────────────────────────────────────────────────────
const COMMANDS = {
  async help() {
    return { embeds: [embed("📖 MATCHDAY UNITED commands", [
      "`/scores` — today's scores, live games and latest results",
      "`/fixtures` — upcoming matches (pick a league or all)",
      "`/table` — league table (PL, La Liga, Serie A, Bundesliga, Ligue 1, UCL)",
      "`/scorers` — top scorers for a league",
      "`/news` — latest football headlines (all, transfers or women's)",
      "`/quiz` — a random football quiz question",
      "", "All times IST. Data refreshes every 30 minutes.",
    ].join("\n"))] };
  },

  async scores(i, { snap }) {
    const ms = snap.matches || [];
    const today = istDate(), yday = istDate(new Date(Date.now() - 86_400_000));
    const live = ms.filter((m) => ["IN_PLAY", "PAUSED"].includes(m.status));
    const todays = ms.filter((m) => m.istDate === today);
    const recent = ms.filter((m) => m.status === "FINISHED" && (m.istDate === yday || m.istDate === today));
    const pick = live.length ? live : todays.length ? todays : recent.length ? recent : ms.filter((m) => m.status === "FINISHED").slice(-10);
    const title = live.length ? "🔴 Live now" : todays.length ? "⚽ Today's matches" : recent.length ? "🏁 Latest results" : "🏁 Most recent results";
    if (!pick.length) return { embeds: [embed("No matches right now", "Nothing in the tracked leagues. Try `/fixtures`.", RED)] };
    return { embeds: [embed(title, stale(snap), RED, { fields: byComp(pick) })] };
  },

  async fixtures(i, { snap }) {
    const lg = opt(i, "league");
    const ms = (snap.matches || []).filter((m) => ["SCHEDULED", "TIMED"].includes(m.status) && (!lg || m.comp === lg)).slice(0, 25);
    if (!ms.length) return { embeds: [embed("No upcoming fixtures found", "Check back after the next refresh.", BLUE)] };
    const fields = byComp(ms).map((f) => ({ ...f, value: ms.filter((m) => (m.compName || m.comp) === f.name).slice(0, 10).map((m) => `\`${m.ist}\` ${m.home} v ${m.away}`).join("\n").slice(0, 1024) }));
    return { embeds: [embed(`📅 Upcoming fixtures${lg ? " · " + LEAGUES[lg] : ""}`, `All times IST · ${stale(snap)}`, BLUE, { fields })] };
  },

  async table(i, { snap }) {
    const lg = opt(i, "league") || "PL";
    const t = snap.tables?.[lg];
    if (!t) return { embeds: [embed("Table not available yet", "It appears after the next data refresh.", GREEN)] };
    const rows = t.rows.slice(0, 20).map((r) => `${String(r.pos).padStart(2)} ${r.team.slice(0, 15).padEnd(15)} ${String(r.p).padStart(2)} ${String(r.gd > 0 ? "+" + r.gd : r.gd).padStart(4)} ${String(r.pts).padStart(3)}`);
    return { embeds: [embed(`📊 ${t.name} table${t.matchday ? " · matchday " + t.matchday : ""}`, "```\n #  Team            P   GD Pts\n" + rows.join("\n") + "\n```", GREEN)] };
  },

  async scorers(i, { snap }) {
    const lg = opt(i, "league") || "PL";
    const t = snap.scorers?.[lg];
    if (!t?.rows?.length) return { embeds: [embed("Top scorers not available yet", "They appear after the next data refresh.", GREEN)] };
    return { embeds: [embed(`👟 ${t.name} top scorers`, t.rows.map((p, n) => `\`${String(n + 1).padStart(2)}\` **${p.player}** (${p.team}) — ${p.goals} ⚽${p.assists ? ` · ${p.assists} 🅰️` : ""}`).join("\n"), GREEN)] };
  },

  async news(i, { snap }) {
    const kind = opt(i, "type") || "all";
    let items = snap.news || [];
    if (kind !== "all") items = items.filter((n) => n.kind === kind);
    items = items.slice(0, 6);
    if (!items.length) return { embeds: [embed("No headlines right now", "Try again in a few minutes.", BLUE)] };
    const label = { all: "Latest football news", transfers: "Latest transfer news", womens: "Latest women's football news" }[kind];
    return { embeds: [embed(`📰 ${label}`, items.map((n) => `• [${n.title}](${n.url}) — *${n.source}*`).join("\n").slice(0, 4000), BLUE)] };
  },

  async quiz(i, { quiz }) {
    if (!quiz?.length) return { content: "Quiz is warming up — try again in a minute." };
    const q = quiz[Math.floor(Math.random() * quiz.length)];
    const letters = ["🇦", "🇧", "🇨", "🇩"];
    return { embeds: [embed("🧠 Football quiz", `**${q.q}**\n\n${q.options.map((o, n) => `${letters[n]} ${o}`).join("\n")}\n\nAnswer: ||${q.options[q.answer]} — ${q.why || ""}||`, PURPLE)] };
  },
};

// ── HTTP entry ───────────────────────────────────────────────────────────────────────────────────
async function handle(req, env) {
  if (req.method === "GET") return new Response("MATCHDAY UNITED commands are running ⚽", { headers: { "content-type": "text/plain; charset=utf-8" } });
  if (req.method !== "POST") return new Response("Method not allowed", { status: 405 });
  const body = await req.text();
  if (!(await verify(req, body, env.DISCORD_PUBLIC_KEY))) return new Response("Bad signature", { status: 401 });
  const i = JSON.parse(body);
  const json = (o) => new Response(JSON.stringify(o), { headers: { "content-type": "application/json" } });
  if (i.type === 1) return json({ type: 1 });                                   // PING
  if (i.type === 2) {                                                           // slash command
    const fn = COMMANDS[i.data.name];
    let reply;
    try { reply = fn ? await fn(i, await data()) : { content: "Unknown command. Try `/help`." }; }
    catch (e) { reply = { content: "Something went wrong fetching data — try again in a minute." }; }
    return json({ type: 4, data: { ...reply, allowed_mentions: { parse: [] } } });
  }
  return json({ type: 4, data: { content: "Not supported." } });
}

// Cloudflare Workers
export default { fetch: (req, env) => handle(req, env || {}) };
// Deno Deploy
if (typeof Deno !== "undefined" && Deno.serve) {
  Deno.serve((req) => handle(req, { DISCORD_PUBLIC_KEY: Deno.env.get("DISCORD_PUBLIC_KEY") }));
}
