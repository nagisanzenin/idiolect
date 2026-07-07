# Changelog

## 0.1.0 — 2026-07-07

Initial release.

- 62 validated voice profiles (4 hand-authored gold + 58 grown from a locked 62-seed diversity matrix), each with stance engine, systematic error profile, opener/closer pools, and three scanner-verified exemplars; roster distance floor 0.2 enforced (closest pair 0.224).
- `scripts/idiolect.py` (stdlib-only): scan / conform / distance / overlap / pick / ledger / fingerprint / self / synth-scaffold / validate / voices / show / selftest (25 tests) / doctor / path.
- `data/tells.json`: era-tagged tell lexicon (gpt4/gpt5/model-family), 40+ construction regexes, statistical thresholds, human-texture patterns (report-only by design), local extension point.
- Six skills — idiolect (natural-language router), write, humanize, audit, synthesize, campaign, self — plus three agents: blind idiolect-auditor, isolated idiolect-writer, idiolect-synthesizer.
- Continuous self-voice pickup: UserPromptSubmit hook → filtered local corpus → fingerprint → co-authored `self` profile; `on/off/clear/drift`.
- Omni-platform: Claude Code native; Codex (.codex-plugin, .agents marketplace, TOML agent ports, installer); opencode (skills native, markdown agent ports, installer).
- Bench: fixture corpus with stated separation criteria (loud slop ≥ 41, humans ≤ 15, margin ≥ 20; subtle astroturf documented as the deterministic floor).
- Docs: THEORY.md (literature review with corrections), VOICE-SPEC.md, PUBLISHING.md, INSTALL-OMNI.md, SAMPLES.md (five voices + control, receipts included).
