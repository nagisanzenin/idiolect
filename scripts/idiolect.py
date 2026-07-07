#!/usr/bin/env python3
"""idiolect — voice-true writing engine.

Dependency-free CLI behind the idiolect plugin (Claude Code / Codex / opencode).
Everything measurable lives here; the skills orchestrate, this verifies.

Subcommands (all machine outputs via --json are strict JSON):
  scan         AI-tell lint of a draft (score 0-100, per-hit coordinates, human-texture report)
  fingerprint  descriptive stylometry of a corpus (feeds voice synthesis)
  voices       list roster (built-in + custom [+ self])
  show         print one voice profile
  validate     enforce docs/VOICE-SPEC.md on profiles
  distance     pairwise voice-distance matrix; flags look-alike pairs
  pick         rank voices for a brief (platform, formality, topic keywords)
  conform      measure a draft against a voice's declared parameters
  overlap      cross-draft n-gram overlap (campaign dedup)
  ledger       structure-rotation memory (variance guard)
  self         the user's own voice: capture, corpus, fingerprint, on/off
  synth-scaffold  emit a prefilled profile skeleton from a fingerprint
  selftest     internal test suite
  doctor       environment checks
  path         print resolved directories

State lives under $IDIOLECT_HOME (default ~/.claude/idiolect); the shipped
roster and tell lexicon are read-only relative to this script. Free text must
reach this tool via --file or stdin, never inlined into shell commands.
"""

import argparse
import json
import math
import os
import re
import sys
import hashlib
import tempfile
from datetime import datetime, timezone

# ---------------------------------------------------------------- paths

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(ROOT, "data")
VOICES_DIR = os.path.join(ROOT, "voices")
TELLS_PATH = os.path.join(DATA_DIR, "tells.json")

HOME = os.environ.get("IDIOLECT_HOME") or os.path.join(
    os.path.expanduser("~"), ".claude", "idiolect")
CUSTOM_VOICES_DIR = os.path.join(HOME, "voices")
LEDGER_PATH = os.path.join(HOME, "ledger.jsonl")
SELF_DIR = os.path.join(HOME, "self")
SELF_CORPUS = os.path.join(SELF_DIR, "corpus.jsonl")
SELF_OFF_FLAG = os.path.join(SELF_DIR, "off")
LOCAL_TELLS = os.path.join(HOME, "tells.local.json")

SELF_CORPUS_MAX_ENTRIES = 2500
SELF_CORPUS_MAX_BYTES = 2_000_000
SELF_ENTRY_MAX_CHARS = 2000
SELF_MIN_WORDS = 15

ISO = "%Y-%m-%dT%H:%M:%SZ"


def now_iso():
    return datetime.now(timezone.utc).strftime(ISO)


def ensure_home():
    for d in (HOME, CUSTOM_VOICES_DIR, SELF_DIR):
        os.makedirs(d, exist_ok=True)


def die(msg, code=2):
    print(f"idiolect: error: {msg}", file=sys.stderr)
    sys.exit(code)


def read_text_arg(args):
    """Standard text input: --file PATH | --file - (stdin). Never inline argv."""
    path = getattr(args, "file", None)
    if not path:
        die("provide --file PATH (or --file - for stdin)")
    if path == "-":
        return sys.stdin.read()
    if not os.path.exists(path):
        die(f"no such file: {path}")
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def out(args, human_str, obj):
    if getattr(args, "json", False):
        print(json.dumps(obj, ensure_ascii=False, indent=2))
    else:
        print(human_str)


# ---------------------------------------------------------------- mini-YAML
# Strict subset parser for voice frontmatter (docs/VOICE-SPEC.md):
# 2-space indents, `key: value`, inline lists [a, b], inline maps {a: 1},
# nested block maps and block lists ("- item"), quoted strings, no anchors.

def _scalar(tok):
    tok = tok.strip()
    if tok == "":
        return ""
    if len(tok) >= 2 and tok[0] == tok[-1] and tok[0] in "\"'":
        return tok[1:-1]
    low = tok.lower()
    if low in ("true", "yes"):
        return True
    if low in ("false", "no"):
        return False
    if low in ("null", "~"):
        return None
    try:
        return int(tok)
    except ValueError:
        pass
    try:
        return float(tok)
    except ValueError:
        pass
    return tok


def _split_inline(s, opener, closer):
    """Split an inline list/map body on commas not inside quotes."""
    body = s.strip()
    assert body.startswith(opener) and body.endswith(closer)
    body = body[1:-1]
    parts, depth, cur, q = [], 0, "", None
    for ch in body:
        if q:
            cur += ch
            if ch == q:
                q = None
            continue
        if ch in "\"'":
            q = ch
            cur += ch
        elif ch in "[{":
            depth += 1
            cur += ch
        elif ch in "]}":
            depth -= 1
            cur += ch
        elif ch == "," and depth == 0:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    if cur.strip():
        parts.append(cur)
    return [p.strip() for p in parts]


def _value(tok):
    tok = tok.strip()
    if tok.startswith("[") and tok.endswith("]"):
        return [_value(p) for p in _split_inline(tok, "[", "]")]
    if tok.startswith("{") and tok.endswith("}"):
        d = {}
        for p in _split_inline(tok, "{", "}"):
            if ":" not in p:
                raise ValueError(f"bad inline map entry: {p!r}")
            k, v = p.split(":", 1)
            d[_scalar(k)] = _value(v)
        return d
    return _scalar(tok)


def parse_yaml_subset(text):
    lines = [ln.rstrip() for ln in text.splitlines()]
    root = {}
    # stack of (indent, container)
    stack = [(-1, root)]
    i = 0
    while i < len(lines):
        raw = lines[i]
        i += 1
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        line = raw.strip()
        while stack and indent <= stack[-1][0]:
            stack.pop()
        if not stack:
            raise ValueError(f"indentation error at: {raw!r}")
        container = stack[-1][1]
        if line.startswith("- "):
            if not isinstance(container, list):
                raise ValueError(f"list item outside list: {raw!r}")
            container.append(_value(line[2:]))
            continue
        if ":" not in line:
            raise ValueError(f"expected 'key: value': {raw!r}")
        key, rest = line.split(":", 1)
        key = _scalar(key)
        rest = rest.strip()
        if not isinstance(container, dict):
            raise ValueError(f"mapping entry inside list: {raw!r}")
        if rest == "":
            # block map or block list follows; sniff next significant line
            j = i
            child = {}
            while j < len(lines):
                nxt = lines[j]
                if nxt.strip() and not nxt.lstrip().startswith("#"):
                    nin = len(nxt) - len(nxt.lstrip(" "))
                    if nin > indent and nxt.strip().startswith("- "):
                        child = []
                    break
                j += 1
            container[key] = child
            stack.append((indent, child))
        else:
            container[key] = _value(rest)
    return root


def parse_profile(text, path="<memory>"):
    m = re.match(r"\A---\s*\n(.*?)\n---\s*\n?(.*)\Z", text, re.S)
    if not m:
        raise ValueError(f"{path}: no frontmatter block")
    fm = parse_yaml_subset(m.group(1))
    return fm, m.group(2)


# ---------------------------------------------------------------- text stats

ABBREV = {"mr", "mrs", "ms", "dr", "prof", "sr", "jr", "st", "vs", "etc",
          "e.g", "i.e", "approx", "dept", "inc", "ltd", "co", "corp", "ft",
          "oz", "lb", "lbs", "hr", "hrs", "min", "u.s", "u.k", "no", "vol"}

WORD_RE = re.compile(r"[A-Za-z0-9''’-]+")
EMOJI_RE = re.compile(
    "[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF⬀-⯿️]")
CODEBLOCK_RE = re.compile(r"```.*?```", re.S)
INLINECODE_RE = re.compile(r"`[^`\n]+`")
QUOTE_RE = re.compile(r"\"[^\"\n]{3,240}\"|“[^”\n]{3,240}”")
CONTRACTION_RE = re.compile(r"\b\w+[''’](?:s|t|re|ve|ll|d|m)\b", re.I)
HASHTAG_RE = re.compile(r"(?<!&)#\w{2,}")
BOLD_RE = re.compile(r"\*\*[^*\n]+\*\*")
HEADING_RE = re.compile(r"(?m)^#{1,4}\s+(.+)$")
TRIAD_RE = re.compile(r"\b[\w''’-]+, [\w''’-]+,? and [\w''’-]+\b")


def strip_code(text):
    return INLINECODE_RE.sub(" ", CODEBLOCK_RE.sub(" ", text))


def mask_quotes(text):
    return QUOTE_RE.sub(lambda m: " " * len(m.group(0)), text)


def words_of(text):
    return WORD_RE.findall(text)


def sentences_of(text):
    """Regex sentence splitter with a small abbreviation guard. Linter-grade."""
    text = re.sub(r"\s+", " ", text.replace("\n", " ")).strip()
    if not text:
        return []
    parts, buf = [], ""
    i = 0
    while i < len(text):
        ch = text[i]
        buf += ch
        if ch in ".!?…":
            # lookbehind word
            tail = re.search(r"([\w.]+)[.!?…]$", buf)
            word = (tail.group(1).lower().rstrip(".") if tail else "")
            nxt = text[i + 1:i + 3]
            # suppress split only for known abbreviations ("Dr. Smith") and
            # decimals ("3.5 stars" — digit immediately after, no space).
            # Lowercase after a period is a SPLIT: lowercase-native writers
            # are half the point of this tool.
            if word in ABBREV or re.match(r"^\d", nxt or " "):
                i += 1
                continue
            parts.append(buf.strip())
            buf = ""
            while i + 1 < len(text) and text[i + 1] in " \"'”)":
                i += 1
                if text[i] in "\"'”)":
                    if parts:
                        parts[-1] += text[i]
            i += 1
            continue
        i += 1
    if buf.strip():
        parts.append(buf.strip())
    return [p for p in parts if words_of(p)]


def paragraphs_of(text):
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]


def cv(values):
    vals = [v for v in values if v is not None]
    if len(vals) < 2:
        return None
    mean = sum(vals) / len(vals)
    if mean == 0:
        return None
    var = sum((v - mean) ** 2 for v in vals) / len(vals)
    return math.sqrt(var) / mean


def text_stats(text):
    body = strip_code(text)
    w = words_of(body)
    sents = sentences_of(body)
    paras = paragraphs_of(body)
    slens = [len(words_of(s)) for s in sents]
    plens = [len(words_of(p)) for p in paras]
    n_words = max(len(w), 1)
    em_dashes = body.count("—") + body.count("–") + len(re.findall(r"\s--\s", body))
    ellipses = body.count("…") + len(re.findall(r"\.\.\.", body))
    exclaims = body.count("!")
    questions = body.count("?")
    emoji = len(EMOJI_RE.findall(body))
    hashtags = len(HASHTAG_RE.findall(body))
    contractions = len(CONTRACTION_RE.findall(body))
    lower_starts = sum(1 for s in sents if s and s[0].islower())
    caps_words = sum(1 for t in w if len(t) >= 3 and t.isupper())
    frag_short = sum(1 for L in slens if L <= 3)
    return {
        "words": len(w),
        "sentences": len(sents),
        "paragraphs": len(paras),
        "sent_mean": round(sum(slens) / len(slens), 2) if slens else None,
        "sent_cv": round(cv(slens), 3) if cv(slens) is not None else None,
        "para_cv": round(cv(plens), 3) if cv(plens) is not None else None,
        "em_dash_per_100w": round(em_dashes * 100 / n_words, 3),
        "ellipsis_count": ellipses,
        "exclaims_per_100w": round(exclaims * 100 / n_words, 3),
        "questions": questions,
        "emoji_count": emoji,
        "emoji_per_100w": round(emoji * 100 / n_words, 3),
        "hashtag_count": hashtags,
        "contractions_per_100w": round(contractions * 100 / n_words, 3),
        "lowercase_sentence_starts_pct": round(lower_starts * 100 / len(sents), 1) if sents else 0.0,
        "allcaps_words": caps_words,
        "short_fragments": frag_short,
        "sent_lens": slens,
    }


# ---------------------------------------------------------------- tells / scan

def load_tells():
    with open(TELLS_PATH, encoding="utf-8") as f:
        tells = json.load(f)
    if os.path.exists(LOCAL_TELLS):
        try:
            with open(LOCAL_TELLS, encoding="utf-8") as f:
                local = json.load(f)
            for tier in ("t1", "t2", "t3"):
                tells["lexical"].setdefault(tier, [])
                tells["lexical"][tier].extend(local.get("lexical", {}).get(tier, []))
            tells["constructions"].extend(local.get("constructions", []))
        except Exception as e:  # local file must never break the scanner
            print(f"idiolect: warning: ignoring bad tells.local.json ({e})",
                  file=sys.stderr)
    return tells


def line_of(text, pos):
    return text.count("\n", 0, pos) + 1


PLATFORM_ADJUST = {
    # (emoji_warn_per_100w, hashtag_warn)
    "instagram": (4.0, 5), "tiktok": (4.0, 6), "threads": (2.5, 3),
    "x": (1.5, 2), "linkedin": (1.0, 4), "facebook": (1.5, 4),
    "reddit": (0.6, 1), "hn": (0.2, 1), "substack": (0.8, 2),
    "youtube": (2.0, 3), "nextdoor": (1.0, 2), "forums": (0.6, 1),
}


def scan_text(text, platform=None, tells=None):
    tells = tells or load_tells()
    cfg = tells["scoring"]
    body = strip_code(text)
    masked = mask_quotes(body)
    lower = masked.lower()
    stats = text_stats(text)
    n_words = max(stats["words"], 1)
    hits = []
    categories = set()

    def add(cat, kind, ident, weight, count, lines, note=""):
        hits.append({"category": cat, "kind": kind, "id": ident,
                     "weight": round(weight, 2), "count": count,
                     "lines": lines[:6], "note": note})
        categories.add(cat)

    # lexical tiers
    for tier in ("t1", "t2", "t3"):
        for item in tells["lexical"].get(tier, []):
            pat = item["p"]
            if item.get("regex"):
                rx = re.compile(item["re"], re.I)
            else:
                rx = re.compile(r"(?<![\w-])" + re.escape(pat).replace(r"\ ", r"\s+") + r"(?![\w-])", re.I)
            found = [m for m in rx.finditer(lower if not item.get("regex") else masked)]
            if not found:
                continue
            n = min(len(found), cfg["per_term_cap"])
            lines = [line_of(masked, m.start()) for m in found]
            add("lexical", f"lex_{tier}", pat, item["w"] * n, len(found), lines,
                item.get("note", ""))

    # constructions
    for c in tells["constructions"]:
        rx = re.compile(c["re"])
        found = list(rx.finditer(masked))
        if not found:
            continue
        if len(found) < c.get("min_hits", 1):
            continue
        capn = min(len(found), c.get("cap", cfg["per_construction_cap"]))
        lines = [line_of(masked, m.start()) for m in found]
        add("construction", "construction", c["id"], c["w"] * capn, len(found),
            lines, c.get("example", ""))

    # metrics
    M = tells["metrics"]
    emoji_warn, hashtag_warn = M["emoji_per_100w"]["warn"], M["hashtag_count"]["warn"]
    if platform in PLATFORM_ADJUST:
        emoji_warn, hashtag_warn = PLATFORM_ADJUST[platform]

    md = stats["em_dash_per_100w"]
    mm = M["em_dash_per_100w"]
    if md >= mm["bad"]:
        add("metric-stat", "metric", "em_dash_density", mm["w_bad"], 1, [], f"{md}/100w")
    elif md >= mm["warn"]:
        add("metric-stat", "metric", "em_dash_density", mm["w_warn"], 1, [], f"{md}/100w")

    sc = M["sent_cv"]
    if stats["sentences"] >= sc["min_sentences"] and stats["sent_cv"] is not None:
        if stats["sent_cv"] < sc["bad_below"]:
            add("metric-stat", "metric", "uniform_sentences", sc["w_bad"], 1, [],
                f"CV {stats['sent_cv']} — metronomic")
        elif stats["sent_cv"] < sc["warn_below"]:
            add("metric-stat", "metric", "uniform_sentences", sc["w_warn"], 1, [],
                f"CV {stats['sent_cv']}")

    pc = M["para_cv"]
    if stats["paragraphs"] >= pc["min_paras"] and stats["para_cv"] is not None \
            and stats["para_cv"] < pc["warn_below"]:
        add("metric-stat", "metric", "uniform_paragraphs", pc["w_warn"], 1, [],
            f"CV {stats['para_cv']}")

    if stats["sent_mean"] and stats["sent_mean"] > M["avg_sent_len"]["warn_above"]:
        add("metric-stat", "metric", "long_sentences", M["avg_sent_len"]["w_warn"],
            1, [], f"mean {stats['sent_mean']}w")

    triads = TRIAD_RE.findall(masked)
    td = M["triad_density_per_300w"]
    if len(triads) * 300 / n_words >= td["warn"] and len(triads) >= 2:
        add("metric-stat", "metric", "rule_of_three_density", td["w_warn"], len(triads),
            [], f"{len(triads)} triads/{n_words}w")

    st = M["staccato_run"]
    slens = stats["sent_lens"]
    runs = 0
    streak = 0
    for L in slens:
        if L <= st["max_words"]:
            streak += 1
            if streak == st["run_len"]:
                runs += 1
        else:
            streak = 0
    if runs:
        add("metric-stat", "metric", "staccato_drama", st["w"] * min(runs, st["cap"]),
            runs, [], f"{runs} run(s) of tiny sentences")

    hd = M["hedge_density_per_100w"]
    hedge_hits = 0
    for h in hd["hedges"]:
        hedge_hits += len(re.findall(r"(?<!\w)" + re.escape(h) + r"(?!\w)", lower))
    if hedge_hits * 100 / n_words >= hd["warn"]:
        add("metric-stat", "metric", "hedge_pileup", hd["w_warn"], hedge_hits, [],
            f"{hedge_hits} hedges/{n_words}w")

    if stats["emoji_per_100w"] >= emoji_warn and stats["emoji_count"] >= 3:
        add("metric-format", "metric", "emoji_density", M["emoji_per_100w"]["w_warn"],
            stats["emoji_count"], [], f"{stats['emoji_per_100w']}/100w (platform-adjusted)")

    if stats["hashtag_count"] >= hashtag_warn:
        add("metric-format", "metric", "hashtag_pile", M["hashtag_count"]["w_warn"],
            stats["hashtag_count"], [], f"{stats['hashtag_count']} hashtags")

    bolds = BOLD_RE.findall(body)
    if len(bolds) * 200 / n_words >= M["bold_spans_per_200w"]["warn"] and len(bolds) >= 3:
        add("metric-format", "metric", "bold_overuse", M["bold_spans_per_200w"]["w_warn"],
            len(bolds), [], f"{len(bolds)} bold spans")

    tc = 0
    for m in HEADING_RE.finditer(body):
        title = m.group(1).strip()
        tw = [t for t in title.split() if len(t) > 3]
        if len(tw) >= 3 and all(t[0].isupper() for t in tw):
            tc += 1
    if tc:
        w_each = M["title_case_headings"]["w_each"]
        add("metric-format", "metric", "title_case_headings",
            w_each * min(tc, M["title_case_headings"]["cap"]), tc, [])

    paras = paragraphs_of(body)
    if len(paras) >= 3 and all(p.rstrip().endswith("!") for p in paras):
        add("metric-format", "metric", "exclamation_uniformity",
            M["exclam_para_uniformity"]["w"], len(paras), [])

    bs = M["both_sides_marker"]
    if bs["a"] in lower and bs["b"] in lower:
        add("metric-stat", "metric", "both_sides_seesaw", bs["w"], 1, [])

    if "“" in body or "’" in body:
        add("metric-format", "metric", "curly_quotes", M["curly_quotes"]["w"], 1, [],
            "weak alone; autoformat-common")

    # human texture (reported, never scored)
    texture = []
    for hp in tells["human_signals"]["patterns"]:
        found = re.findall(hp["re"], body)
        if found:
            texture.append({"id": hp["id"], "label": hp["label"], "count": len(found)})

    raw = sum(h["weight"] for h in hits)
    mult = 1.0
    ncat = len(categories)
    for k, v in sorted(tells["scoring"]["cluster_multipliers"].items()):
        if ncat >= int(k):
            mult = v
    raw *= mult
    score = min(100, round(raw * cfg["normalize_to_words"]
                           / max(n_words, cfg["min_words_for_stats"])))
    band = next(b["band"] for b in cfg["bands"] if score <= b["max"])
    hits.sort(key=lambda h: -h["weight"])
    del stats["sent_lens"]
    return {
        "score": score, "band": band, "raw_points": round(raw, 1),
        "cluster_categories": ncat, "cluster_multiplier": mult,
        "platform": platform, "hits": hits, "human_texture": texture,
        "stats": stats,
        "disclaimer": "linter for drafts, not a detector for accusing people",
    }


def fmt_scan(rep):
    lines = [f"score {rep['score']}/100  band={rep['band']}  "
             f"(raw {rep['raw_points']}, {rep['cluster_categories']} tell categories, "
             f"x{rep['cluster_multiplier']})"]
    if rep["hits"]:
        lines.append("tells:")
        for h in rep["hits"][:25]:
            loc = f" @L{','.join(map(str, h['lines']))}" if h["lines"] else ""
            note = f"  — {h['note']}" if h["note"] else ""
            lines.append(f"  [{h['kind']}] {h['id']} x{h['count']} "
                         f"(+{h['weight']}){loc}{note}")
        if len(rep["hits"]) > 25:
            lines.append(f"  … and {len(rep['hits']) - 25} more")
    else:
        lines.append("tells: none")
    tx = rep["human_texture"]
    lines.append("human texture: " + (", ".join(f"{t['label']} x{t['count']}" for t in tx)
                                      if tx else "NONE — no specifics, no anchors, no first-person actions"))
    s = rep["stats"]
    lines.append(f"stats: {s['words']}w {s['sentences']}s  sent_mean={s['sent_mean']} "
                 f"sent_cv={s['sent_cv']}  em-dash/100w={s['em_dash_per_100w']}  "
                 f"emoji={s['emoji_count']}  hashtags={s['hashtag_count']}")
    return "\n".join(lines)


# ---------------------------------------------------------------- fingerprint

FUNCTION_WORDS = ("the of and a to in is was that it i you for on with as but "
                  "at by this so not are be have from or we they my me").split()


def fingerprint_text(text):
    stats = text_stats(text)
    body = strip_code(text)
    toks = [t.lower() for t in words_of(body)]
    n = max(len(toks), 1)
    fw = {w: round(toks.count(w) * 1000 / n, 2) for w in FUNCTION_WORDS}
    punct = {p: round(body.count(p) * 1000 / max(len(body), 1), 3)
             for p in [",", ";", ":", "(", "—", "!", "?", "…"]}
    informal = {}
    for mk in ["gonna", "gotta", "kinda", "tbh", "idk", "lol", "btw", "ngl",
               "imo", "fwiw", "yeah", "nah", "ok", "okay"]:
        c = len(re.findall(r"(?<!\w)" + mk + r"(?!\w)", body, re.I))
        if c:
            informal[mk] = c
    top = {}
    for t in toks:
        if len(t) > 3 and t not in FUNCTION_WORDS:
            top[t] = top.get(t, 0) + 1
    favorites = sorted(top.items(), key=lambda kv: -kv[1])[:25]
    del stats["sent_lens"]
    return {
        "stats": stats,
        "function_words_per_1000": fw,
        "punct_per_1000_chars": punct,
        "informal_markers": informal,
        "top_content_words": [{"w": w, "n": c} for w, c in favorites],
    }


# ---------------------------------------------------------------- voices

REQUIRED_FM = ["slug", "display", "archetype", "age", "locale", "platforms",
               "formality", "temperament", "humor", "stylo", "error_profile",
               "lexicon", "never", "domains"]
REQUIRED_STYLO = ["sent_mean", "sent_cv", "fragment_rate", "contractions",
                  "paragraphs", "emoji", "exclaims_per_100w", "em_dash",
                  "ellipsis", "caps", "terminal_period"]
REQUIRED_SECTIONS = ["## Who this is", "## Stance engine", "## How they write",
                     "## What they never do", "## Error profile in practice",
                     "## Openers and closers", "## Exemplars"]
ERROR_CLASSES = ["pristine", "lowercase", "boomer-ellipsis", "l2-systematic",
                 "fast-typer", "caps-burst", "double-space", "comma-splice",
                 "no-apostrophe", "run-on", "fragmentary"]
KNOWN_PLATFORMS = list(PLATFORM_ADJUST.keys())


def voice_files():
    files = {}
    for d, custom in ((VOICES_DIR, False), (CUSTOM_VOICES_DIR, True)):
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            if fn.endswith(".md") and not fn.startswith("_"):
                slug = fn[:-3]
                files[slug] = {"path": os.path.join(d, fn), "custom": custom}
    return files


def load_voice(slug):
    files = voice_files()
    if slug not in files:
        die(f"unknown voice: {slug} (run `idiolect.py voices`)")
    with open(files[slug]["path"], encoding="utf-8") as f:
        fm, body = parse_profile(f.read(), files[slug]["path"])
    fm["_path"] = files[slug]["path"]
    fm["_custom"] = files[slug]["custom"]
    return fm, body


def load_all_frontmatter():
    result = {}
    for slug, info in voice_files().items():
        try:
            with open(info["path"], encoding="utf-8") as f:
                fm, _ = parse_profile(f.read(), info["path"])
            fm["_path"], fm["_custom"] = info["path"], info["custom"]
            result[slug] = fm
        except Exception as e:
            result[slug] = {"_error": str(e), "_path": info["path"]}
    return result


def validate_voice(slug, strict_exemplars=True):
    errors, warnings = [], []
    try:
        fm, body = load_voice(slug)
    except SystemExit:
        raise
    except Exception as e:
        return [f"parse failure: {e}"], []
    for k in REQUIRED_FM:
        if k not in fm:
            errors.append(f"missing frontmatter field: {k}")
    if errors:
        return errors, warnings
    if fm["slug"] != slug:
        errors.append(f"slug {fm['slug']!r} != filename {slug!r}")
    if not re.match(r"^[a-z0-9-]+$", str(fm["slug"])):
        errors.append("slug must be [a-z0-9-]+")
    if not isinstance(fm["age"], int) or not 16 <= fm["age"] <= 100:
        errors.append("age must be int 16..100")
    if not 0 <= float(fm["formality"]) <= 1:
        errors.append("formality out of [0,1]")
    t = fm["temperament"]
    if not isinstance(t, dict) or sorted(t.keys()) != ["A", "C", "E", "N", "O"]:
        errors.append("temperament must have keys O,C,E,A,N")
    else:
        for k, v in t.items():
            if not 0 <= float(v) <= 1:
                errors.append(f"temperament.{k} out of [0,1]")
    for k in REQUIRED_STYLO:
        if k not in fm["stylo"]:
            errors.append(f"missing stylo.{k}")
    sy = fm["stylo"]
    if "sent_mean" in sy and not 4 <= float(sy["sent_mean"]) <= 35:
        errors.append("stylo.sent_mean out of [4,35]")
    if "sent_cv" in sy and not 0.2 <= float(sy["sent_cv"]) <= 1.2:
        errors.append("stylo.sent_cv out of [0.2,1.2]")
    ep = fm["error_profile"]
    if ep.get("class") not in ERROR_CLASSES:
        errors.append(f"error_profile.class {ep.get('class')!r} unknown")
    for p in fm["platforms"]:
        if p not in KNOWN_PLATFORMS:
            warnings.append(f"platform {p!r} not in known set")
    for sec in REQUIRED_SECTIONS:
        if sec not in body:
            errors.append(f"missing body section: {sec}")
    exemplars = re.findall(r"(?m)^### Exemplar \d+[^\n]*\n(.*?)(?=^### |\Z)", body, re.S)
    if len(exemplars) < 3:
        errors.append(f"need 3 exemplars, found {len(exemplars)}")
    else:
        tells = load_tells()
        banned = [str(b).lower() for b in fm.get("lexicon", {}).get("banned", [])]
        for i, ex in enumerate(exemplars[:3], 1):
            ex_clean = ex.strip()
            if len(words_of(ex_clean)) < 25:
                warnings.append(f"exemplar {i} is very short")
                continue
            rep = scan_text(ex_clean, platform=(fm["platforms"] or [None])[0], tells=tells)
            limit = 10 if strict_exemplars else 15
            if rep["score"] > limit:
                errors.append(f"exemplar {i} scans {rep['score']} (> {limit}): "
                              + ", ".join(h["id"] for h in rep["hits"][:4]))
            low = ex_clean.lower()
            for b in banned:
                if b and re.search(r"(?<!\w)" + re.escape(b) + r"(?!\w)", low):
                    errors.append(f"exemplar {i} uses voice-banned term {b!r}")
    return errors, warnings


# ---------------------------------------------------------------- distance

CAT_FIELDS = [("emoji", 0.06), ("caps", 0.08), ("contractions", 0.05),
              ("fragment_rate", 0.04)]


def _locale_family(loc):
    return str(loc).split()[0].lower() if loc else ""


def voice_distance(a, b):
    d = 0.0
    total = 0.0
    def num(x, w):
        nonlocal d, total
        d += w * x
        total += w
    # numeric diffs are scaled by realistic roster spread so a maximally
    # different pair approaches 1.0 on each component, not 0.2
    num(min(abs(float(a["formality"]) - float(b["formality"])) / 0.85, 1.0), 2.0)
    ta, tb = a["temperament"], b["temperament"]
    for k in "OCEAN":
        num(min(abs(float(ta[k]) - float(tb[k])) / 0.6, 1.0), 0.3)
    num(min(abs(float(a["stylo"]["sent_mean"]) - float(b["stylo"]["sent_mean"])) / 17.0, 1.0), 1.0)
    num(min(abs(float(a["stylo"]["sent_cv"]) - float(b["stylo"]["sent_cv"])) / 0.35, 1.0), 1.0)
    num(min(abs(float(a["stylo"]["exclaims_per_100w"]) - float(b["stylo"]["exclaims_per_100w"])) / 2.5, 1.0), 0.5)
    for f, w in CAT_FIELDS:
        d += w * (0 if a["stylo"].get(f) == b["stylo"].get(f) else 1)
        total += w
    d += 0.10 * (0 if a["error_profile"]["class"] == b["error_profile"]["class"] else 1)
    total += 0.10
    d += 0.08 * (0 if _locale_family(a["locale"]) == _locale_family(b["locale"]) else 1)
    total += 0.08
    fam_a = str(a["archetype"]).split("/")[0]
    fam_b = str(b["archetype"]).split("/")[0]
    d += 0.08 * (0 if fam_a == fam_b else 1)
    total += 0.08
    pa, pb = set(a["platforms"]), set(b["platforms"])
    j = len(pa & pb) / max(len(pa | pb), 1)
    d += 0.10 * (1 - j)
    total += 0.10
    ha = set(re.findall(r"\w+", str(a["humor"]).lower()))
    hb = set(re.findall(r"\w+", str(b["humor"]).lower()))
    d += 0.06 * (0 if ha & hb else 1)
    total += 0.06
    return round(d / total, 4)


# ---------------------------------------------------------------- conform

def conform_text(text, fm, platform=None):
    stats = text_stats(text)
    sy = fm["stylo"]
    checks = []

    def check(name, target, actual, ok):
        checks.append({"name": name, "target": target, "actual": actual, "ok": bool(ok)})

    sm, target_mean = stats["sent_mean"], float(sy["sent_mean"])
    if sm is not None and stats["sentences"] >= 3:
        tol = max(4.0, target_mean * 0.35)
        check("sent_mean", f"{target_mean}±{round(tol, 1)}", sm, abs(sm - target_mean) <= tol)
    if stats["sent_cv"] is not None and stats["sentences"] >= 6:
        check("sent_cv (burstiness)", f">={round(float(sy['sent_cv']) - 0.15, 2)}",
              stats["sent_cv"], stats["sent_cv"] >= float(sy["sent_cv"]) - 0.15)
    emoji_policy = sy["emoji"]
    limit = {"never": 0, "rare": 1, "brand-set": 2}.get(emoji_policy)
    if limit is not None:
        check(f"emoji ({emoji_policy})", f"<={limit}", stats["emoji_count"],
              stats["emoji_count"] <= limit)
    ed_policy = sy["em_dash"]
    ed_count = round(stats["em_dash_per_100w"] * stats["words"] / 100)
    if ed_policy == "never":
        check("em_dash (never)", "0", ed_count, ed_count == 0)
    elif ed_policy == "rare":
        check("em_dash (rare)", "<=1", ed_count, ed_count <= 1)
    ex_target = float(sy["exclaims_per_100w"])
    check("exclaims_per_100w", f"<={round(ex_target * 1.6 + 0.5, 2)}",
          stats["exclaims_per_100w"], stats["exclaims_per_100w"] <= ex_target * 1.6 + 0.5)
    caps = sy["caps"]
    if caps == "lowercase":
        check("caps (lowercase)", ">=60% lower starts",
              stats["lowercase_sentence_starts_pct"],
              stats["lowercase_sentence_starts_pct"] >= 60)
    elif caps == "standard":
        check("caps (standard)", "<=25% lower starts",
              stats["lowercase_sentence_starts_pct"],
              stats["lowercase_sentence_starts_pct"] <= 25)
    contr = sy["contractions"]
    cr = stats["contractions_per_100w"]
    if contr == "none":
        check("contractions (none)", "0", cr, cr == 0)
    elif contr == "heavy":
        check("contractions (heavy)", ">=1.5/100w", cr, cr >= 1.5)
    elif contr == "light":
        check("contractions (light)", "<=1.5/100w", cr, cr <= 1.5)
    violations = []
    low = strip_code(text).lower()
    for b in fm.get("lexicon", {}).get("banned", []):
        if re.search(r"(?<!\w)" + re.escape(str(b).lower()) + r"(?!\w)", low):
            violations.append(f"banned term used: {b!r}")
    for rule in fm.get("never", []):
        r = str(rule).lower()
        if "hashtag" in r and stats["hashtag_count"] > 0:
            violations.append("never-rule broken: hashtags present")
        if "emoji" in r and stats["emoji_count"] > 0:
            violations.append("never-rule broken: emoji present")
        if "bullet" in r and re.search(r"(?m)^\s*[-*•]\s+\w", text):
            violations.append("never-rule broken: bullet list present")
        if "header" in r and re.search(r"(?m)^#{1,4}\s", text):
            violations.append("never-rule broken: headers present")
    ok = all(c["ok"] for c in checks) and not violations
    return {"voice": fm["slug"], "pass": ok, "checks": checks,
            "violations": violations, "stats_words": stats["words"]}


def fmt_conform(rep):
    lines = [f"conform[{rep['voice']}]: {'PASS' if rep['pass'] else 'FAIL'}"]
    for c in rep["checks"]:
        mark = "ok " if c["ok"] else "FAIL"
        lines.append(f"  {mark} {c['name']}: target {c['target']}, actual {c['actual']}")
    for v in rep["violations"]:
        lines.append(f"  FAIL {v}")
    return "\n".join(lines)


# ---------------------------------------------------------------- overlap

def ngrams(tokens, n):
    return {" ".join(tokens[i:i + n]) for i in range(len(tokens) - n + 1)}


def overlap_files(paths):
    docs = []
    for p in paths:
        with open(p, encoding="utf-8") as f:
            txt = f.read()
        toks = [t.lower() for t in words_of(strip_code(txt))]
        docs.append({"path": p, "tokens": toks, "g5": ngrams(toks, 5)})
    pairs = []
    for i in range(len(docs)):
        for j in range(i + 1, len(docs)):
            a, b = docs[i], docs[j]
            inter = a["g5"] & b["g5"]
            union = a["g5"] | b["g5"]
            jac = round(len(inter) / max(len(union), 1), 4)
            shared = sorted(inter, key=len, reverse=True)[:5]
            pairs.append({"a": a["path"], "b": b["path"], "jaccard5": jac,
                          "flag": jac > 0.12, "shared_examples": shared})
    return pairs


# ---------------------------------------------------------------- ledger

def ledger_read():
    if not os.path.exists(LEDGER_PATH):
        return []
    entries = []
    with open(LEDGER_PATH, encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip()
            if ln:
                try:
                    entries.append(json.loads(ln))
                except json.JSONDecodeError:
                    pass
    return entries


def ledger_add(voice, platform, structure, campaign=None, text=None):
    ensure_home()
    h = hashlib.sha256((text or "").encode("utf-8")).hexdigest()[:8] if text else None
    entry = {"ts": now_iso(), "voice": voice, "platform": platform,
             "structure": structure, "campaign": campaign, "hash8": h}
    with open(LEDGER_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry


def ledger_check(voice, structure, lookback=5):
    entries = [e for e in ledger_read() if e["voice"] == voice][-lookback:]
    collisions = []
    for idx, e in enumerate(entries):
        s = e.get("structure") or {}
        same = [k for k in ("opener", "shape", "len") if s.get(k) and s.get(k) == structure.get(k)]
        if len(same) >= 2:
            collisions.append({"ts": e["ts"], "same": same, "structure": s})
        elif (idx == len(entries) - 1 and s.get("opener")
              and s.get("opener") == structure.get("opener")):
            # back-to-back posts must not reuse the opener move even alone
            collisions.append({"ts": e["ts"], "same": ["opener"], "structure": s})
    return {"voice": voice, "recent": len(entries), "collisions": collisions,
            "ok": not collisions,
            "advice": "vary >=2 of opener/shape/len vs recent posts" if collisions else "clear"}


# ---------------------------------------------------------------- self voice

CODEY_RE = re.compile(r"[{}<>`$\\/=;|]")


def self_capturable(text):
    t = text.strip()
    if not t or t.startswith("/") or t.startswith("!"):
        return False, "command"
    w = words_of(t)
    if len(w) < SELF_MIN_WORDS:
        return False, "too short"
    codey = len(CODEY_RE.findall(t))
    if codey / max(len(t), 1) > 0.03 or "```" in t:
        return False, "code-like"
    if re.search(r"(?m)^\s*(?:File \"|Traceback|at [\w$.]+\()", t):
        return False, "log-like"
    letters = sum(1 for c in t if c.isalpha())
    if letters / max(len(t), 1) < 0.55:
        return False, "not prose"
    return True, "ok"


def self_append(text, source):
    ensure_home()
    entry = {"ts": now_iso(), "source": source,
             "text": text.strip()[:SELF_ENTRY_MAX_CHARS]}
    with open(SELF_CORPUS, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    # compact when oversized: drop oldest prompt-entries first, keep samples
    try:
        if os.path.getsize(SELF_CORPUS) > SELF_CORPUS_MAX_BYTES:
            entries = self_read()
            samples = [e for e in entries if e["source"] == "sample"]
            prompts = [e for e in entries if e["source"] != "sample"]
            keep_p = prompts[-(SELF_CORPUS_MAX_ENTRIES - len(samples)):]
            merged = sorted(samples + keep_p, key=lambda e: e["ts"])
            tmp = SELF_CORPUS + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                for e in merged:
                    f.write(json.dumps(e, ensure_ascii=False) + "\n")
            os.replace(tmp, SELF_CORPUS)
    except OSError:
        pass
    return entry


def self_read():
    if not os.path.exists(SELF_CORPUS):
        return []
    entries = []
    with open(SELF_CORPUS, encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip()
            if ln:
                try:
                    entries.append(json.loads(ln))
                except json.JSONDecodeError:
                    pass
    return entries


# ---------------------------------------------------------------- commands

def cmd_scan(args):
    text = read_text_arg(args)
    rep = scan_text(text, platform=args.platform)
    out(args, fmt_scan(rep), rep)
    if args.fail_over is not None and rep["score"] > args.fail_over:
        sys.exit(1)


def cmd_fingerprint(args):
    if args.self:
        entries = self_read()
        if not entries:
            die("self corpus is empty — nothing captured yet")
        text = "\n\n".join(e["text"] for e in entries)
        fp = fingerprint_text(text)
        fp["source"] = {"entries": len(entries),
                        "samples": sum(1 for e in entries if e["source"] == "sample"),
                        "prompts": sum(1 for e in entries if e["source"] != "sample")}
    else:
        text = read_text_arg(args)
        fp = fingerprint_text(text)
    if args.json:
        print(json.dumps(fp, ensure_ascii=False, indent=2))
    else:
        s = fp["stats"]
        print(f"{s['words']}w, sent_mean={s['sent_mean']}, sent_cv={s['sent_cv']}, "
              f"contractions/100w={s['contractions_per_100w']}, "
              f"em-dash/100w={s['em_dash_per_100w']}, "
              f"lower-starts={s['lowercase_sentence_starts_pct']}%")
        if fp["informal_markers"]:
            print("informal:", ", ".join(f"{k}x{v}" for k, v in fp["informal_markers"].items()))
        print("top words:", ", ".join(t["w"] for t in fp["top_content_words"][:12]))


def cmd_voices(args):
    fms = load_all_frontmatter()
    rows = []
    for slug, fm in sorted(fms.items()):
        if "_error" in fm:
            rows.append({"slug": slug, "error": fm["_error"]})
            continue
        rows.append({"slug": slug, "display": fm.get("display"),
                     "archetype": fm.get("archetype"),
                     "platforms": fm.get("platforms"),
                     "formality": fm.get("formality"),
                     "locale": fm.get("locale"),
                     "domains": fm.get("domains"),
                     "custom": fm.get("_custom", False)})
    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        for r in rows:
            if "error" in r:
                print(f"{r['slug']:22} !! parse error: {r['error']}")
            else:
                tag = " [custom]" if r["custom"] else ""
                print(f"{r['slug']:22} f={r['formality']:<4} "
                      f"{','.join(r['platforms']):24} {r['display']}{tag}")
        print(f"\n{len(rows)} voices")


def cmd_show(args):
    fm, body = load_voice(args.slug)
    with open(fm["_path"], encoding="utf-8") as f:
        print(f.read())


def cmd_validate(args):
    fms = load_all_frontmatter()
    slugs = [args.slug] if args.slug else sorted(fms.keys())
    failed = 0
    results = {}
    for slug in slugs:
        strict = not fms.get(slug, {}).get("_custom", False)
        errors, warnings = validate_voice(slug, strict_exemplars=strict)
        results[slug] = {"errors": errors, "warnings": warnings}
        if errors:
            failed += 1
            print(f"FAIL {slug}")
            for e in errors:
                print(f"     - {e}")
        else:
            w = f"  ({len(warnings)} warning(s))" if warnings else ""
            print(f"ok   {slug}{w}")
        for wn in warnings:
            print(f"     ~ {wn}")
    print(f"\n{len(slugs) - failed}/{len(slugs)} valid")
    if failed:
        sys.exit(1)


def cmd_distance(args):
    fms = {s: fm for s, fm in load_all_frontmatter().items() if "_error" not in fm}
    slugs = sorted(fms.keys())
    pairs = []
    for i in range(len(slugs)):
        for j in range(i + 1, len(slugs)):
            d = voice_distance(fms[slugs[i]], fms[slugs[j]])
            pairs.append({"a": slugs[i], "b": slugs[j], "distance": d})
    pairs.sort(key=lambda p: p["distance"])
    threshold = args.threshold
    close = [p for p in pairs if p["distance"] < threshold]
    if args.json:
        print(json.dumps({"threshold": threshold, "too_close": close,
                          "closest": pairs[:15],
                          "voices": len(slugs)}, indent=2))
    else:
        print(f"{len(slugs)} voices, {len(pairs)} pairs, threshold {threshold}")
        for p in pairs[:15]:
            flag = "  << TOO CLOSE" if p["distance"] < threshold else ""
            print(f"  {p['distance']:.3f}  {p['a']} <-> {p['b']}{flag}")
    if close:
        sys.exit(1)


def cmd_pick(args):
    fms = {s: fm for s, fm in load_all_frontmatter().items() if "_error" not in fm}
    brief_toks = set()
    if args.brief_file:
        with open(args.brief_file, encoding="utf-8") as f:
            brief_toks = {t.lower() for t in words_of(f.read()) if len(t) > 3}
    recent = [e["voice"] for e in ledger_read()[-args.recent_window:]]
    scored = []
    for slug, fm in fms.items():
        if slug in (args.exclude or []):
            continue
        score = 0.0
        plats = fm.get("platforms", [])
        if args.platform:
            if not plats or args.platform not in plats:
                score -= 2.0
            elif plats[0] == args.platform:
                score += 2.0
            else:
                score += 1.2
        if args.formality is not None:
            score -= abs(float(fm["formality"]) - args.formality) * 2.0
        if brief_toks:
            dom_toks = set()
            for d in (fm.get("domains") or []):
                dom_toks |= {t.lower() for t in words_of(str(d))}
            dom_toks |= {t.lower() for t in words_of(str(fm.get("archetype", "")))}
            score += 1.5 * len(brief_toks & dom_toks) / max(len(dom_toks), 1) * 3
        if slug in recent:
            score -= 1.0 * (recent.count(slug))
        scored.append((round(score, 3), slug))
    scored.sort(reverse=True)
    n = args.n
    picks = []
    if args.distinct and n > 1:
        # greedy max-min-distance selection from the top pool
        pool = [s for _, s in scored[:max(n * 4, 12)]]
        picks = [pool[0]]
        while len(picks) < n and len(picks) < len(pool):
            best, best_d = None, -1
            for cand in pool:
                if cand in picks:
                    continue
                dmin = min(voice_distance(fms[cand], fms[p]) for p in picks)
                if dmin > best_d:
                    best, best_d = cand, dmin
            picks.append(best)
    else:
        picks = [s for _, s in scored[:n]]
    fit_by_slug = {sl: sc for sc, sl in scored}
    rows = [{"slug": s, "display": fms[s]["display"], "path": fms[s]["_path"],
             "fit": fit_by_slug[s]} for s in picks]
    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        for r in rows:
            print(f"{r['slug']:22} fit={r['fit']:<6} {r['display']}")


def cmd_conform(args):
    text = read_text_arg(args)
    fm, _ = load_voice(args.voice)
    rep = conform_text(text, fm, platform=args.platform)
    out(args, fmt_conform(rep), rep)
    if not rep["pass"]:
        sys.exit(1)


def cmd_overlap(args):
    for p in args.files:
        if not os.path.exists(p):
            die(f"no such file: {p}")
    pairs = overlap_files(args.files)
    if args.json:
        print(json.dumps(pairs, ensure_ascii=False, indent=2))
    else:
        for p in pairs:
            flag = "  << OVERLAP" if p["flag"] else ""
            print(f"jaccard5={p['jaccard5']:.4f}  {os.path.basename(p['a'])} <-> "
                  f"{os.path.basename(p['b'])}{flag}")
            for s in (p["shared_examples"] if p["flag"] else []):
                print(f"    shared: \"{s}\"")
    if any(p["flag"] for p in pairs):
        sys.exit(1)


def cmd_ledger(args):
    if args.action == "add":
        structure = {"opener": args.opener, "shape": args.shape, "len": args.len}
        text = None
        if args.file:
            with open(args.file, encoding="utf-8") as f:
                text = f.read()
        e = ledger_add(args.voice, args.platform, structure, args.campaign, text)
        print(json.dumps(e, ensure_ascii=False))
    elif args.action == "check":
        structure = {"opener": args.opener, "shape": args.shape, "len": args.len}
        rep = ledger_check(args.voice, structure, args.lookback)
        print(json.dumps(rep, ensure_ascii=False, indent=2))
        if not rep["ok"]:
            sys.exit(1)
    elif args.action == "list":
        entries = ledger_read()
        for e in entries[-args.lookback:]:
            s = e.get("structure") or {}
            print(f"{e['ts']}  {e['voice']:20} {e.get('platform') or '-':10} "
                  f"opener={s.get('opener')} shape={s.get('shape')} len={s.get('len')} "
                  f"campaign={e.get('campaign') or '-'}")
        print(f"\n{len(entries)} total entries")


def cmd_self(args):
    ensure_home()
    if args.action == "capture":
        if os.path.exists(SELF_OFF_FLAG):
            return  # silently disabled
        try:
            payload = json.load(sys.stdin)
            text = payload.get("prompt") or payload.get("text") or ""
        except Exception:
            text = ""
        ok, why = self_capturable(text)
        if ok:
            self_append(text, "prompt")
        # hooks must be silent and always exit 0
        return
    if args.action == "add":
        if args.file:
            with open(args.file, encoding="utf-8") as f:
                text = f.read()
        else:
            text = sys.stdin.read()
        chunks = [c for c in re.split(r"\n\s*\n", text) if len(words_of(c)) >= 8] or [text]
        for c in chunks:
            self_append(c, "sample")
        print(f"added {len(chunks)} sample chunk(s) to self corpus")
        return
    if args.action == "status":
        entries = self_read()
        samples = sum(1 for e in entries if e["source"] == "sample")
        prompts = len(entries) - samples
        total_words = sum(len(words_of(e["text"])) for e in entries)
        disabled = os.path.exists(SELF_OFF_FLAG)
        st = {"entries": len(entries), "samples": samples, "prompts": prompts,
              "words": total_words, "capture": "off" if disabled else "on",
              "corpus": SELF_CORPUS,
              "last": entries[-1]["ts"] if entries else None,
              "ready_for_build": total_words >= 800 or samples >= 5}
        if args.json:
            print(json.dumps(st, indent=2))
        else:
            print(f"self capture: {st['capture']}\n"
                  f"corpus: {st['entries']} entries ({samples} samples, {prompts} prompts), "
                  f"{total_words} words\n"
                  f"ready for build: {'yes' if st['ready_for_build'] else 'no — need ~800 words or 5 samples'}")
        return
    if args.action == "corpus":
        for e in self_read()[-args.tail:]:
            print(f"[{e['ts']} {e['source']}] {e['text'][:120]}")
        return
    if args.action == "on":
        if os.path.exists(SELF_OFF_FLAG):
            os.remove(SELF_OFF_FLAG)
        print("self capture: on")
        return
    if args.action == "off":
        with open(SELF_OFF_FLAG, "w") as f:
            f.write(now_iso() + "\n")
        print("self capture: off (corpus kept; `self on` to resume)")
        return
    if args.action == "clear":
        if os.path.exists(SELF_CORPUS):
            os.remove(SELF_CORPUS)
        print("self corpus cleared")
        return


def cmd_synth_scaffold(args):
    fp = None
    if args.from_fingerprint:
        with open(args.from_fingerprint, encoding="utf-8") as f:
            fp = json.load(f)
    s = fp["stats"] if fp else {}
    def g(k, default):
        v = s.get(k)
        return v if v is not None else default
    caps = "lowercase" if g("lowercase_sentence_starts_pct", 0) >= 60 else "standard"
    contr = "heavy" if g("contractions_per_100w", 0) >= 2 else (
        "light" if g("contractions_per_100w", 0) <= 0.8 else "standard")
    emd = "never" if g("em_dash_per_100w", 0) == 0 else (
        "rare" if g("em_dash_per_100w", 0) < 0.8 else "comfortable")
    print(f"""---
slug: {args.slug}
display: "TODO — one-line who/where"
archetype: TODO-family/niche
age: TODO
locale: "TODO dialect/register"
platforms: [TODO]
formality: TODO
temperament: {{O: 0.5, C: 0.5, E: 0.5, A: 0.5, N: 0.5}}
humor: "TODO"
domains: [TODO, TODO]
stylo:
  sent_mean: {round(g('sent_mean', 13) or 13)}
  sent_cv: {round(g('sent_cv', 0.65) or 0.65, 2)}
  fragment_rate: {"some" if g('short_fragments', 0) else "rare"}
  contractions: {contr}
  paragraphs: "TODO"
  emoji: {"never" if g('emoji_count', 0) == 0 else "rare"}
  exclaims_per_100w: {round(g('exclaims_per_100w', 0.5) or 0.5, 1)}
  em_dash: {emd}
  ellipsis: "TODO"
  caps: {caps}
  terminal_period: {"dropped-in-short-lines" if caps == "lowercase" else "always"}
error_profile:
  class: TODO
  rate: light
  rules:
    - "TODO systematic flaw 1"
lexicon:
  favorites: [TODO]
  intensifiers: [TODO]
  hedges: [TODO]
  banned: [delve, leverage, elevate, game-changer, journey, seamless, unlock]
  profanity: none
never:
  - "TODO"
---
## Who this is
TODO

## Stance engine
- loves:
- hates:

## How they write
- TODO

## What they never do
- TODO

## Error profile in practice
TODO

## Openers and closers
Openers: TODO
Closers: TODO

## Exemplars
### Exemplar 1 — promo (PLATFORM)
TODO

### Exemplar 2 — story (PLATFORM)
TODO

### Exemplar 3 — opinion/reply (PLATFORM)
TODO
""")


def cmd_path(_args):
    print(json.dumps({"root": ROOT, "voices": VOICES_DIR, "data": DATA_DIR,
                      "home": HOME, "custom_voices": CUSTOM_VOICES_DIR,
                      "ledger": LEDGER_PATH, "self_corpus": SELF_CORPUS}, indent=2))


def cmd_doctor(_args):
    problems = []
    print(f"python: {sys.version.split()[0]}")
    for p, label in ((TELLS_PATH, "tells.json"), (VOICES_DIR, "voices/")):
        if os.path.exists(p):
            print(f"ok   {label}")
        else:
            print(f"MISS {label}: {p}")
            problems.append(label)
    ensure_home()
    try:
        probe = os.path.join(HOME, ".probe")
        with open(probe, "w") as f:
            f.write("x")
        os.remove(probe)
        print(f"ok   home writable: {HOME}")
    except OSError as e:
        print(f"FAIL home not writable: {e}")
        problems.append("home")
    fms = load_all_frontmatter()
    bad = [s for s, fm in fms.items() if "_error" in fm]
    print(f"ok   {len(fms) - len(bad)} voices parse ({len(bad)} broken: {bad})" if not bad
          else f"WARN {len(bad)} voices fail to parse: {bad}")
    print("doctor:", "all clear" if not problems and not bad else "problems found")
    if problems:
        sys.exit(1)


# ---------------------------------------------------------------- selftest

SLOP_SNIPPET = """In today's fast-paced world, staying organized is more crucial than ever.
That's where Shotbox comes in. This game-changer seamlessly integrates with your
workflow, offering a treasure trove of features designed to elevate your productivity.
It's not just a tool—it's a revolution. Whether you're a busy professional or a
creative entrepreneur, Shotbox has you covered. Say goodbye to messy screenshots
and hello to effortless organization. The best part? It's free to start.
Don't miss out on this incredible opportunity. The future of productivity is bright!"""

HUMAN_SNIPPET = """ok so I finally cleaned up my screenshots folder last night. 4,312 files.
there was a receipt from 2021 in there for a burrito I don't remember eating.

been using shotbox for two weeks now, the $12 thing I mentioned. it moved
everything into folders by app and date and honestly the search is the part
I keep using. typed "invoice" this morning and found the thing my accountant
wanted in about four seconds, which. yeah.

anyway if your desktop looks like mine did, it exists. that's the whole post."""


def cmd_selftest(_args):
    global HOME, CUSTOM_VOICES_DIR, LEDGER_PATH, SELF_DIR, SELF_CORPUS, SELF_OFF_FLAG, LOCAL_TELLS
    failures = []

    def t(name, cond, detail=""):
        status = "pass" if cond else "FAIL"
        print(f"{status}  {name}" + (f"  ({detail})" if detail and not cond else ""))
        if not cond:
            failures.append(name)

    # yaml subset
    fm = parse_yaml_subset(
        'slug: test\nage: 51\nformality: 0.3\nplatforms: [facebook, x]\n'
        'temperament: {O: 0.4, C: 0.7, E: 0.5, A: 0.6, N: 0.3}\n'
        'stylo:\n  sent_mean: 12\n  caps: standard\nlexicon:\n  banned: [delve, "game-changer"]\n'
        'never:\n  - hashtags\n  - "bullet lists"\n')
    t("yaml: scalars", fm["slug"] == "test" and fm["age"] == 51 and fm["formality"] == 0.3)
    t("yaml: inline list", fm["platforms"] == ["facebook", "x"])
    t("yaml: inline map", fm["temperament"]["C"] == 0.7)
    t("yaml: nested block", fm["stylo"]["sent_mean"] == 12 and fm["stylo"]["caps"] == "standard")
    t("yaml: block list", fm["never"] == ["hashtags", "bullet lists"])
    t("yaml: quoted in list", fm["lexicon"]["banned"][1] == "game-changer")

    sents = sentences_of("Dr. Smith fixed it. It cost $40. Worth it! Right? ok then")
    t("sentences: abbrev guard", len(sents) == 5, f"got {len(sents)}: {sents}")

    stats = text_stats(HUMAN_SNIPPET)
    t("stats: counts words", stats["words"] > 80)
    t("stats: cv computed", stats["sent_cv"] is not None and stats["sent_cv"] > 0.3)

    slop = scan_text(SLOP_SNIPPET)
    human = scan_text(HUMAN_SNIPPET)
    t("scan: slop scores slop", slop["score"] >= 41, f"score {slop['score']}")
    t("scan: human scores clean", human["score"] <= 15, f"score {human['score']}")
    t("scan: separation margin", slop["score"] - human["score"] >= 30,
      f"{slop['score']} vs {human['score']}")
    t("scan: finds not_x_but_y family", any(h["id"] in ("its_not_x_its_y", "not_just_but")
                                            for h in slop["hits"]))
    t("scan: human texture found in human", len(human["human_texture"]) >= 2)
    quoted = scan_text('She said "this is a game-changer that will elevate your workflow" and laughed for a solid minute at the brochure, then threw it in the recycling with the rest of the conference swag.')
    t("scan: quotes are masked", not any(h["id"] in ("game-changer", "elevate your")
                                         for h in quoted["hits"]),
      str([h["id"] for h in quoted["hits"]]))

    # conform
    fm_v = {"slug": "t", "stylo": {"sent_mean": 12, "sent_cv": 0.6, "emoji": "never",
            "em_dash": "never", "exclaims_per_100w": 0.5, "caps": "lowercase",
            "contractions": "heavy", "fragment_rate": "some", "paragraphs": "x",
            "ellipsis": "x", "terminal_period": "dropped-in-short-lines"},
            "lexicon": {"banned": ["delve"]}, "never": ["hashtags"]}
    rep = conform_text(HUMAN_SNIPPET, fm_v)
    t("conform: human passes lowercase-heavy profile", rep["pass"],
      json.dumps(rep, indent=1)[:300])
    rep2 = conform_text(SLOP_SNIPPET, fm_v)
    t("conform: slop fails it", not rep2["pass"])

    # distance sanity
    a = {"formality": 0.3, "temperament": {c: 0.5 for c in "OCEAN"},
         "stylo": {"sent_mean": 12, "sent_cv": 0.65, "exclaims_per_100w": 0.5,
                   "emoji": "never", "caps": "standard", "contractions": "heavy",
                   "fragment_rate": "some"},
         "error_profile": {"class": "fast-typer"}, "locale": "en-US Ohio",
         "archetype": "trades/hvac", "platforms": ["facebook"], "humor": "dry"}
    import copy
    b = copy.deepcopy(a)
    t("distance: identical = 0", voice_distance(a, b) == 0)
    b.update({"formality": 0.9, "locale": "en-GB London", "archetype": "law/barrister",
              "platforms": ["x"], "humor": "polite", "error_profile": {"class": "pristine"}})
    b["stylo"].update({"sent_mean": 24, "sent_cv": 0.5, "caps": "standard",
                       "contractions": "none", "emoji": "never"})
    t("distance: far pair > 0.3", voice_distance(a, b) > 0.3,
      str(voice_distance(a, b)))

    # ledger + self in a temp home
    old = (HOME, CUSTOM_VOICES_DIR, LEDGER_PATH, SELF_DIR, SELF_CORPUS, SELF_OFF_FLAG, LOCAL_TELLS)
    with tempfile.TemporaryDirectory() as td:
        HOME = td
        CUSTOM_VOICES_DIR = os.path.join(td, "voices")
        LEDGER_PATH = os.path.join(td, "ledger.jsonl")
        SELF_DIR = os.path.join(td, "self")
        SELF_CORPUS = os.path.join(SELF_DIR, "corpus.jsonl")
        SELF_OFF_FLAG = os.path.join(SELF_DIR, "off")
        LOCAL_TELLS = os.path.join(td, "tells.local.json")
        ensure_home()
        ledger_add("dale-hvac", "facebook", {"opener": "scene", "shape": "story", "len": "med"})
        chk = ledger_check("dale-hvac", {"opener": "scene", "shape": "story", "len": "short"})
        t("ledger: collision detected", not chk["ok"])
        chk2 = ledger_check("dale-hvac", {"opener": "price", "shape": "tip", "len": "short"})
        t("ledger: variation clears", chk2["ok"])
        ok1, _ = self_capturable("fix the bug in main.py using {x: 1} and re-run $PYTHON please")
        t("self: code-like rejected", not ok1)
        ok2, _ = self_capturable("honestly I think the report reads too formal, can we make the opening feel more like how I actually talk to customers when they walk in")
        t("self: prose accepted", ok2)
        self_append("this is a sample of my writing that is long enough to matter for the corpus", "sample")
        t("self: corpus roundtrip", len(self_read()) == 1)
    (HOME, CUSTOM_VOICES_DIR, LEDGER_PATH, SELF_DIR, SELF_CORPUS, SELF_OFF_FLAG, LOCAL_TELLS) = old

    print(f"\nselftest: {'PASS' if not failures else 'FAIL'} "
          f"({len(failures)} failure(s))")
    if failures:
        sys.exit(1)


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(prog="idiolect", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("scan", help="AI-tell lint")
    sp.add_argument("--file", required=True, help="path or - for stdin")
    sp.add_argument("--platform", choices=KNOWN_PLATFORMS)
    sp.add_argument("--json", action="store_true")
    sp.add_argument("--fail-over", type=int, default=None,
                    help="exit 1 if score exceeds this")
    sp.set_defaults(fn=cmd_scan)

    sp = sub.add_parser("fingerprint", help="descriptive stylometry")
    sp.add_argument("--file", help="path or - for stdin")
    sp.add_argument("--self", action="store_true", help="fingerprint the self corpus")
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(fn=cmd_fingerprint)

    sp = sub.add_parser("voices", help="list roster")
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(fn=cmd_voices)

    sp = sub.add_parser("show", help="print a profile")
    sp.add_argument("slug")
    sp.set_defaults(fn=cmd_show)

    sp = sub.add_parser("validate", help="enforce VOICE-SPEC")
    sp.add_argument("slug", nargs="?")
    sp.set_defaults(fn=cmd_validate)

    sp = sub.add_parser("distance", help="pairwise voice distance")
    sp.add_argument("--threshold", type=float, default=0.2)
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(fn=cmd_distance)

    sp = sub.add_parser("pick", help="rank voices for a brief")
    sp.add_argument("--platform", choices=KNOWN_PLATFORMS)
    sp.add_argument("--formality", type=float)
    sp.add_argument("--brief-file", help="file with the brief text (topic keywords)")
    sp.add_argument("--n", type=int, default=3)
    sp.add_argument("--distinct", action="store_true",
                    help="greedy max-distance set instead of pure top-N")
    sp.add_argument("--exclude", nargs="*")
    sp.add_argument("--recent-window", type=int, default=10)
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(fn=cmd_pick)

    sp = sub.add_parser("conform", help="draft vs voice parameters")
    sp.add_argument("--file", required=True)
    sp.add_argument("--voice", required=True)
    sp.add_argument("--platform", choices=KNOWN_PLATFORMS)
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(fn=cmd_conform)

    sp = sub.add_parser("overlap", help="cross-draft n-gram overlap")
    sp.add_argument("files", nargs="+")
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(fn=cmd_overlap)

    sp = sub.add_parser("ledger", help="structure-rotation memory")
    sp.add_argument("action", choices=["add", "check", "list"])
    sp.add_argument("--voice")
    sp.add_argument("--platform")
    sp.add_argument("--opener", help="opener type, e.g. scene|question|price|claim|address")
    sp.add_argument("--shape", help="post shape, e.g. story|tip|list|rant|announcement|reply")
    sp.add_argument("--len", help="short|med|long")
    sp.add_argument("--campaign")
    sp.add_argument("--file", help="post text (for dedup hash)")
    sp.add_argument("--lookback", type=int, default=5)
    sp.set_defaults(fn=cmd_ledger)

    sp = sub.add_parser("self", help="the user's own voice")
    sp.add_argument("action", choices=["capture", "add", "status", "corpus",
                                       "on", "off", "clear"])
    sp.add_argument("--file")
    sp.add_argument("--tail", type=int, default=10)
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(fn=cmd_self)

    sp = sub.add_parser("synth-scaffold", help="profile skeleton from fingerprint")
    sp.add_argument("--slug", required=True)
    sp.add_argument("--from-fingerprint", help="JSON from `fingerprint --json`")
    sp.set_defaults(fn=cmd_synth_scaffold)

    sp = sub.add_parser("selftest")
    sp.set_defaults(fn=cmd_selftest)
    sp = sub.add_parser("doctor")
    sp.set_defaults(fn=cmd_doctor)
    sp = sub.add_parser("path")
    sp.set_defaults(fn=cmd_path)

    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
