// This Day in the Pacific War — app
/* global React, ReactDOM, useTweaks, TweaksPanel, TweakSection, TweakRadio, TweakSlider, TweakToggle, TweakColor */
const { useState, useMemo, useEffect, useCallback, useRef } = React;

// ---------- date helpers ----------
const MONTHS = ["JANUARY","FEBRUARY","MARCH","APRIL","MAY","JUNE","JULY","AUGUST","SEPTEMBER","OCTOBER","NOVEMBER","DECEMBER"];
const WEEKDAYS = ["SUNDAY","MONDAY","TUESDAY","WEDNESDAY","THURSDAY","FRIDAY","SATURDAY"];
const DOW = ["S","M","T","W","T","F","S"];
function parseDate(s) { const [y,m,d] = s.split("-").map(Number); return new Date(Date.UTC(y, m-1, d)); }
function iso(y,m,d){ return `${y}-${String(m+1).padStart(2,"0")}-${String(d).padStart(2,"0")}`; }
function fmtDay(s) { return String(parseDate(s).getUTCDate()).padStart(2,"0"); }
function fmtMonth(s) { return MONTHS[parseDate(s).getUTCMonth()]; }
function fmtYear(s) { return parseDate(s).getUTCFullYear(); }
function fmtWeekday(s) { return WEEKDAYS[parseDate(s).getUTCDay()]; }
function titleCase(s){ return s.charAt(0) + s.slice(1).toLowerCase(); }
function dayFrac(s, start, end) {
  const t = parseDate(s).getTime(), a = parseDate(start).getTime(), b = parseDate(end).getTime();
  return Math.max(0, Math.min(1, (t - a) / (b - a)));
}

// ---------- AI ----------
const HAS_AI = typeof window !== "undefined" && window.claude && typeof window.claude.complete === "function";
const NOTE_PARTS = [
  { key: "knew",      label: "WHAT HE KNEW" },
  { key: "didntKnow", label: "WHAT HE DIDN'T YET KNOW" },
  { key: "coming",    label: "WHAT WAS COMING" },
];

function buildPrompt(e) {
  const dateStr = `${fmtDay(e.date)} ${titleCase(fmtMonth(e.date))} ${fmtYear(e.date)}`;
  return [
    "You are a naval historian of the Pacific War (1941-1942), writing for a serious, well-read audience already familiar with the campaign. Your tone is authoritative, precise, and unsentimental.",
    "",
    `Below is a CINCPAC running-summary (\"Graybook\") entry. The officer holding command of the Pacific Fleet on this date is: ${e.command}. Where appropriate, refer to that commander by surname or as \"he\" — do not attribute the entry to a different admiral.`,
    "",
    `DATE: ${dateStr}`,
    `LOCATION: ${e.place}`,
    "ENTRY:",
    `\"\"\"${e.actual.join("\n")}\"\"\"`,
    "",
    "Write an interpretation in exactly three short paragraphs (2-4 sentences each):",
    "1. knew — what the commander knew on this date, given this entry.",
    "2. didntKnow — what he did NOT yet know: consequences, enemy intentions, or facts hidden from him at the time.",
    "3. coming — what was about to happen as a result, looking just ahead from this date.",
    "",
    "Do not merely restate the entry; add the historian's perspective. Do not use the second person. No preamble or closing remarks.",
    "Return ONLY valid JSON, no markdown fences, in exactly this shape:",
    '{"knew":"...","didntKnow":"...","coming":"..."}',
  ].join("\n");
}

function parseNote(raw) {
  if (!raw) throw new Error("empty response");
  let s = String(raw).trim();
  const a = s.indexOf("{"), b = s.lastIndexOf("}");
  if (a >= 0 && b > a) s = s.slice(a, b + 1);
  const o = JSON.parse(s);
  const out = {
    knew:      String(o.knew || "").trim(),
    didntKnow: String(o.didntKnow || o.didnt_know || o.didNotKnow || "").trim(),
    coming:    String(o.coming || "").trim(),
  };
  if (!out.knew || !out.didntKnow || !out.coming) throw new Error("missing fields");
  return out;
}

const CACHE_KEY = "tdpw_ai_v1";
function loadCache() { try { return JSON.parse(localStorage.getItem(CACHE_KEY) || "{}"); } catch { return {}; } }
function saveCache(c) { try { localStorage.setItem(CACHE_KEY, JSON.stringify(c)); } catch {} }

const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "noteFont": "serif",
  "grain": 0.5,
  "accent": "#c0392f",
  "showMarkers": true,
  "uppercaseActual": false
}/*EDITMODE-END*/;

// ---------- small components ----------
function Stamp({ accent }) {
  return (
    <div className="stamp" style={{ "--stamp": accent }}>
      <span>DECLASSIFIED</span>
      <em>E.O. 13526</em>
    </div>
  );
}

function NavArrow({ dir, disabled, onClick }) {
  return (
    <button className="navarrow" data-dir={dir} disabled={disabled} onClick={onClick}
            aria-label={dir === "prev" ? "Previous entry" : "Next entry"}>
      <svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true">
        {dir === "prev"
          ? <path d="M15 5 L8 12 L15 19" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="square"/>
          : <path d="M9 5 L16 12 L9 19" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="square"/>}
      </svg>
    </button>
  );
}

// ---------- calendar popover ----------
function Calendar({ entries, currentDate, onPick, onClose }) {
  const { start, end } = window.WAR_TIMELINE;
  const startD = parseDate(start), endD = parseDate(end);
  const cur = parseDate(currentDate);
  const [view, setView] = useState({ y: cur.getUTCFullYear(), m: cur.getUTCMonth() });
  const entryDates = useMemo(() => new Set(entries.map(e => e.date)), [entries]);

  const minYM = startD.getUTCFullYear()*12 + startD.getUTCMonth();
  const maxYM = endD.getUTCFullYear()*12 + endD.getUTCMonth();
  const curYM = view.y*12 + view.m;
  const step = (delta) => {
    const v = curYM + delta;
    if (v >= minYM && v <= maxYM) setView({ y: Math.floor(v/12), m: ((v%12)+12)%12 });
  };

  useEffect(() => {
    const onKey = (e) => { if (e.key === "Escape") onClose(); };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [onClose]);

  const firstDow = new Date(Date.UTC(view.y, view.m, 1)).getUTCDay();
  const daysInMonth = new Date(Date.UTC(view.y, view.m+1, 0)).getUTCDate();
  const cells = [];
  for (let i = 0; i < firstDow; i++) cells.push(null);
  for (let d = 1; d <= daysInMonth; d++) cells.push(d);

  const inRange = (d) => {
    const t = parseDate(iso(view.y, view.m, d)).getTime();
    return t >= startD.getTime() && t <= endD.getTime();
  };

  return (
    <React.Fragment>
      <div className="cal-backdrop" onClick={onClose}></div>
      <div className="cal" role="dialog" aria-label="Jump to date">
        <div className="cal-list-label">Transcribed entries</div>
        <div className="cal-list">
          {entries.map((e, i) => (
            <button key={e.date}
              className={"cal-li" + (e.date === currentDate ? " is-cur" : "")}
              onClick={() => { onPick(e.date); onClose(); }}>
              <span className="cal-li-date">{fmtDay(e.date)} {fmtMonth(e.date).slice(0,3)} <em>{String(fmtYear(e.date)).slice(2)}</em></span>
              <span className="cal-li-event">{e.event}</span>
            </button>
          ))}
        </div>
        <div className="cal-or">or pick any date</div>
        <div className="cal-head">
          <button className="cal-nav" onClick={() => step(-1)} disabled={curYM <= minYM} aria-label="Previous month">‹</button>
          <div className="cal-title">{titleCase(MONTHS[view.m])} <span>{view.y}</span></div>
          <button className="cal-nav" onClick={() => step(1)} disabled={curYM >= maxYM} aria-label="Next month">›</button>
        </div>
        <div className="cal-dow">{DOW.map((d,i) => <span key={i}>{d}</span>)}</div>
        <div className="cal-grid">
          {cells.map((d, i) => {
            if (d === null) return <span key={"e"+i} className="cal-cell cal-empty"></span>;
            const dateStr = iso(view.y, view.m, d);
            const hasEntry = entryDates.has(dateStr);
            const isCur = dateStr === currentDate;
            const ok = inRange(d);
            return (
              <button key={dateStr}
                className={"cal-cell" + (hasEntry ? " has-entry" : "") + (isCur ? " is-cur" : "")}
                disabled={!ok}
                onClick={() => { onPick(dateStr); onClose(); }}
                title={hasEntry ? "Transcribed entry" : "Jump to nearest entry"}>
                {d}{hasEntry && <span className="cal-mark"></span>}
              </button>
            );
          })}
        </div>
        <div className="cal-foot">
          <span className="cal-key"><span className="cal-mark cal-mark-static"></span> transcribed entry</span>
          <span className="cal-hint">other dates jump to nearest</span>
        </div>
      </div>
    </React.Fragment>
  );
}

// ---------- header ----------
function Header({ entries, entry, onPrev, onNext, atStart, atEnd, accent, onPick }) {
  const [calOpen, setCalOpen] = useState(false);
  return (
    <header className="hdr">
      <div className="hdr-left">
        <div className="hdr-title">This Day in the Pacific War</div>
        <div className="hdr-sub">CINCPAC GRAYBOOK · RUNNING ESTIMATE & SUMMARY · VOL. I</div>
      </div>

      <div className="hdr-date">
        <NavArrow dir="prev" disabled={atStart} onClick={onPrev} />
        <div className="date-wrap">
          <button className="datebox" onClick={() => setCalOpen(o => !o)} aria-expanded={calOpen} aria-haspopup="dialog">
            <div className="date-day">{fmtDay(entry.date)}</div>
            <div className="date-my">
              <span className="date-month">{fmtMonth(entry.date)}</span>
              <span className="date-year">{fmtYear(entry.date)}</span>
            </div>
            <div className="date-weekday">{fmtWeekday(entry.date)}</div>
          </button>
          <button className="date-jump" onClick={() => setCalOpen(o => !o)} aria-label="Jump to date">
            <svg viewBox="0 0 24 24" width="13" height="13" aria-hidden="true">
              <rect x="3" y="4.5" width="18" height="16" rx="1" fill="none" stroke="currentColor" strokeWidth="1.5"/>
              <path d="M3 9 H21 M8 2.5 V6 M16 2.5 V6" stroke="currentColor" strokeWidth="1.5"/>
            </svg>
            <span>JUMP TO DATE</span>
          </button>
          {calOpen && <Calendar entries={entries} currentDate={entry.date}
                                onPick={onPick} onClose={() => setCalOpen(false)} />}
        </div>
        <NavArrow dir="next" disabled={atEnd} onClick={onNext} />
      </div>

      <div className="hdr-right">
        <Stamp accent={accent} />
      </div>
    </header>
  );
}

// ---------- actual panel ----------
function ActualPanel({ entry, grain, uppercase }) {
  return (
    <section className="panel panel-actual" style={{ "--grain": grain }}>
      <div className="panel-label">
        <div className="panel-label-row">
          <span className="panel-kicker">CINCPAC ACTUAL</span>
          <span className="panel-meta">CINCPAC FILE · VOL. I</span>
        </div>
        <div className="panel-title">{entry.place}</div>
      </div>

      <div className="panel-scroll">
        <div className={"typed" + (uppercase ? " upper" : "")}>
          <div className="typed-head">
            <span>FROM: {entry.command}</span>
            <span>SECRET — RUNNING SUMMARY</span>
          </div>
          {entry.actual.map((p, i) => (
            <p key={i} className="typed-p"><span className="lineno">{String(i+1).padStart(2,"0")}</span>{p}</p>
          ))}
          <div className="typed-foot">— END OF ENTRY —</div>
        </div>
      </div>

      <div className="panel-cite">
        <span className="cite-dot"></span>
        <span className="cite-main">SOURCE — GRAYBOOK VOL. I, p.&nbsp;{entry.page}</span>
        <span className="cite-src">Nimitz Graybook · declassified</span>
      </div>

      <div className="panel-grain" aria-hidden="true"></div>
    </section>
  );
}

// ---------- note panel ----------
function NoteStatus({ state, source, onRegenerate }) {
  let chip;
  if (state === "loading") chip = <span className="note-chip loading">GENERATING<span className="cursor">▌</span></span>;
  else if (source === "ai") chip = <span className="note-chip live"><span className="led"></span>CLAUDE · LIVE</span>;
  else if (source === "error") chip = <span className="note-chip off">OFFLINE — ARCHIVE</span>;
  else chip = <span className="note-chip archive">ARCHIVE</span>;

  return (
    <div className="note-status">
      {chip}
      {HAS_AI && state !== "loading" && (
        <button className="note-regen" onClick={onRegenerate} title="Regenerate interpretation" aria-label="Regenerate">
          <svg viewBox="0 0 24 24" width="13" height="13" aria-hidden="true">
            <path d="M20 11 a8 8 0 1 0 -.6 4" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/>
            <path d="M20 5 V11 H14" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </button>
      )}
    </div>
  );
}

function NotePanel({ font, data, state, source, onRegenerate }) {
  return (
    <section className="panel panel-note" data-font={font}>
      <div className="panel-label">
        <div className="panel-label-row">
          <span className="panel-kicker">HISTORIAN'S NOTE</span>
          <NoteStatus state={state} source={source} onRegenerate={onRegenerate} />
        </div>
        <div className="panel-title">INTERPRETATION · WHAT HE KNEW, AND WHAT WAS COMING</div>
      </div>

      <div className="panel-scroll">
        <div className="note-body">
          {state === "loading"
            ? NOTE_PARTS.map(p => (
                <div className="note-part" key={p.key}>
                  <div className="note-part-label">{p.label}</div>
                  <div className="sk sk-1"></div>
                  <div className="sk sk-2"></div>
                  <div className="sk sk-3"></div>
                </div>
              ))
            : NOTE_PARTS.map((p, i) => (
                <div className="note-part" key={p.key}>
                  <div className="note-part-label">{p.label}</div>
                  <p className={i === 0 ? "note-lead" : ""}>{data[p.key]}</p>
                </div>
              ))}

          <div className="note-sig">
            <span className="note-sig-rule"></span>
            <span>{source === "ai"
              ? "HISTORIAN'S NOTE · GENERATED BY CLAUDE"
              : source === "error"
                ? "HISTORIAN'S NOTE · OFFLINE — ARCHIVE PLACEHOLDER"
                : "HISTORIAN'S NOTE · ARCHIVE PLACEHOLDER"}</span>
          </div>
        </div>
      </div>
    </section>
  );
}

// ---------- timeline ----------
function Timeline({ entries, index, onSelect, showMarkers, accent }) {
  const { start, end } = window.WAR_TIMELINE;
  const cur = entries[index];
  const frac = dayFrac(cur.date, start, end);

  const ticks = useMemo(() => {
    const out = [];
    let d = parseDate(start);
    d = new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), 1));
    const last = parseDate(end);
    while (d.getTime() <= last.getTime() + 1) {
      const isoStr = `${d.getUTCFullYear()}-${String(d.getUTCMonth()+1).padStart(2,"0")}-01`;
      out.push({ frac: dayFrac(isoStr, start, end), label: MONTHS[d.getUTCMonth()].slice(0,3) });
      d = new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth()+1, 1));
    }
    return out;
  }, [start, end]);

  return (
    <footer className="timeline" style={{ "--accent": accent }}>
      <div className="tl-cap tl-cap-l">
        <span className="tl-cap-d">07 DEC 1941</span>
        <span className="tl-cap-t">PEARL HARBOR</span>
      </div>

      <div className="tl-track-wrap">
        <div className="tl-track" style={{ "--prog": `${frac*100}%` }}>
          {ticks.map((t, i) => (
            <div key={i} className="tl-tick" style={{ left: `${t.frac*100}%` }}>
              <span className="tl-tick-line"></span>
              <span className="tl-tick-label">{t.label}</span>
            </div>
          ))}

          {showMarkers && entries.map((e, i) => i !== index && (
            <button key={e.date} className="tl-dot" style={{ left: `${dayFrac(e.date, start, end)*100}%` }}
                    onClick={() => onSelect(i)}
                    title={`${fmtDay(e.date)} ${fmtMonth(e.date).slice(0,3)} ${fmtYear(e.date)}`}
                    aria-label={`Go to ${fmtMonth(e.date)} ${fmtDay(e.date)}`}></button>
          ))}

          <div className="tl-marker" style={{ left: `${frac*100}%` }}>
            <span className="tl-marker-flag">{fmtDay(cur.date)} {fmtMonth(cur.date).slice(0,3)}</span>
            <span className="tl-marker-stem"></span>
            <span className="tl-marker-head"></span>
          </div>
        </div>
      </div>

      <div className="tl-cap tl-cap-r">
        <span className="tl-cap-d">01 SEP 1942</span>
        <span className="tl-cap-t">END VOL. I</span>
      </div>
    </footer>
  );
}

// ---------- app ----------
function App() {
  const entries = window.ENTRIES;
  const [t, setTweak] = useTweaks(TWEAK_DEFAULTS);

  const [index, setIndex] = useState(() => {
    const saved = Number(localStorage.getItem("tdpw_index"));
    return Number.isInteger(saved) && saved >= 0 && saved < entries.length ? saved : 0;
  });
  useEffect(() => { localStorage.setItem("tdpw_index", String(index)); }, [index]);

  const [aiCache, setAiCache] = useState(loadCache);
  const [status, setStatus] = useState({});       // date -> 'loading' | 'error'
  const aiCacheRef = useRef(aiCache);
  useEffect(() => { aiCacheRef.current = aiCache; }, [aiCache]);

  const runGenerate = useCallback((entry) => {
    if (!HAS_AI) return Promise.resolve();
    const d = entry.date;
    setStatus(s => ({ ...s, [d]: "loading" }));
    return window.claude.complete({ messages: [{ role: "user", content: buildPrompt(entry) }] })
      .then(raw => {
        const parsed = parseNote(raw);
        setAiCache(c => { const nc = { ...c, [d]: parsed }; saveCache(nc); return nc; });
        setStatus(s => { const ns = { ...s }; delete ns[d]; return ns; });
      })
      .catch(() => setStatus(s => ({ ...s, [d]: "error" })));
  }, []);

  // auto-generate on date change (skip if cached)
  useEffect(() => {
    const entry = entries[index];
    if (!HAS_AI) return;
    if (aiCacheRef.current[entry.date]) return;
    let cancelled = false;
    setStatus(s => ({ ...s, [entry.date]: "loading" }));
    window.claude.complete({ messages: [{ role: "user", content: buildPrompt(entry) }] })
      .then(raw => {
        if (cancelled) return;
        const parsed = parseNote(raw);
        setAiCache(c => { const nc = { ...c, [entry.date]: parsed }; saveCache(nc); return nc; });
        setStatus(s => { const ns = { ...s }; delete ns[entry.date]; return ns; });
      })
      .catch(() => { if (!cancelled) setStatus(s => ({ ...s, [entry.date]: "error" })); });
    return () => { cancelled = true; };
  }, [index]); // eslint-disable-line

  const go = useCallback((n) => setIndex(i => Math.max(0, Math.min(entries.length-1, n))), [entries.length]);
  const prev = useCallback(() => go(index-1), [go, index]);
  const next = useCallback(() => go(index+1), [go, index]);

  const pickDate = useCallback((dateStr) => {
    const target = parseDate(dateStr).getTime();
    let best = 0, bestDiff = Infinity;
    entries.forEach((e, i) => {
      const diff = Math.abs(parseDate(e.date).getTime() - target);
      if (diff < bestDiff) { bestDiff = diff; best = i; }
    });
    setIndex(best);
  }, [entries]);

  useEffect(() => {
    const onKey = (e) => {
      if (e.target && /^(INPUT|TEXTAREA)$/.test(e.target.tagName)) return;
      if (e.key === "ArrowLeft") prev();
      else if (e.key === "ArrowRight") next();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [prev, next]);

  useEffect(() => { document.documentElement.style.setProperty("--accent", t.accent); }, [t.accent]);

  const entry = entries[index];
  const aiData = aiCache[entry.date];
  const st = status[entry.date];
  const noteState = st === "loading" ? "loading" : "ready";
  const noteData = aiData || entry.note;
  const noteSource = aiData ? "ai" : (st === "error" ? "error" : "archive");

  return (
    <div className="app">
      <Header entries={entries} entry={entry} onPrev={prev} onNext={next}
              atStart={index===0} atEnd={index===entries.length-1}
              accent={t.accent} onPick={pickDate} />

      <main className="main">
        <ActualPanel entry={entry} grain={t.grain} uppercase={t.uppercaseActual} />
        <div className="seam" aria-hidden="true"></div>
        <NotePanel font={t.noteFont} data={noteData} state={noteState}
                   source={noteSource} onRegenerate={() => runGenerate(entry)} />
      </main>

      <Timeline entries={entries} index={index} onSelect={go}
                showMarkers={t.showMarkers} accent={t.accent} />

      <TweaksPanel>
        <TweakSection label="Historian's Note" />
        <TweakRadio label="Note typeface" value={t.noteFont} options={["serif","sans"]}
                    onChange={(v)=>setTweak("noteFont", v)} />
        <TweakSection label="Document" />
        <TweakSlider label="Paper grain" value={t.grain} min={0} max={1} step={0.05}
                     onChange={(v)=>setTweak("grain", v)} />
        <TweakToggle label="Force uppercase entry" value={t.uppercaseActual}
                     onChange={(v)=>setTweak("uppercaseActual", v)} />
        <TweakSection label="Interface" />
        <TweakColor label="Accent" value={t.accent}
                    options={["#c0392f","#b6883f","#3f7a86","#8a8f99"]}
                    onChange={(v)=>setTweak("accent", v)} />
        <TweakToggle label="Timeline event markers" value={t.showMarkers}
                     onChange={(v)=>setTweak("showMarkers", v)} />
      </TweaksPanel>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
