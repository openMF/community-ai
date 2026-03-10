# Claude Skills for Speech Model Benchmarking

This document defines reusable AI skills for the benchmarking framework.

## /benchmark-speech

**Purpose:** Run standardized evaluation against a speech provider

**Trigger:** When evaluating provider accuracy

**Inputs:**
- `provider`: Provider name (deepgram, google, aws)
- `languages`: List of language codes (en, es, fr, hi, sw)
- `domain`: Financial domain (account_opening, transfers, balance_inquiry)

**Output:** Accuracy metrics report (WER, CER, MOS per language)

**Example:** 
```
/benchmark-speech provider:deepgram languages:[en,es,hi] domain:transfers
```

---

## /evaluate-language

**Purpose:** Deep-dive evaluation for a specific language

**Trigger:** When investigating why a language scores poorly

**Inputs:**
- `language`: ISO 639-1 code (e.g., `hi` for Hindi)
- `provider`: Speech provider
- `min_samples`: Minimum test samples (default: 5)

**Output:** Language-specific report with:
- Per-sample WER/CER breakdown
- Confidence scores distribution
- Error categories (substitution, deletion, insertion)
- Recommendations for improvement

**Example:**
```
/evaluate-language language:sw provider:deepgram
```

---

## /compare-providers

**Purpose:** Side-by-side accuracy comparison

**Trigger:** When selecting provider or validating new model version

**Inputs:**
- `providers`: List (deepgram, google, aws, etc.)
- `languages`: Languages to compare
- `test_set`: Dataset subset (default: all)

**Output:** Comparison matrix showing:
- Provider performance per language
- Cost-per-request estimates
- Mobile resource impact
- Recommendations

**Example:**
```
/compare-providers providers:[deepgram,google] languages:[en,es]
```

---

## /validate-model-update

**Purpose:** Check if new model version is regression-safe

**Trigger:** When updating provider API or model

**Inputs:**
- `provider`: Provider name
- `baseline_results`: Path to previous evaluation
- `threshold`: Acceptable WER change % (default: 5%)

**Output:** Pass/fail with delta analysis

---

## Implementation Pattern

Skills are implemented as:

1. **Python Functions** in `runners/` with clear inputs/outputs
2. **JSON Schema** for skill definition (tools/skill_schemas.json)
3. **CLI Invocable** via `cli.py --skill benchmark-speech --provider deepgram`
4. **Claude Integration** via MCP (Model Context Protocol) for tool calling

See `tools/skill_schemas.json` for skill definitions.

---

## Benefits

- **Reproducible:** Each skill has defined inputs, outputs, success criteria
- **Automatable:** Claude can invoke these without human intervention
- **Auditable:** All evaluations logged with skill version, parameters, results
- **Extensible:** New skills added as new providers or metrics are needed
