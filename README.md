# chinese-autobiography-review-summary

GitHub: https://github.com/Mengfeifei-sm/chinese-autobiography-review-summary

A reusable Agent Skill for summarizing a **human-reviewed** batch of Chinese autobiography Word files and contextually judging sensitive content for a teacher report.

It is different from `chinese-autobiography-proofreading`:

- that skill produces corrected Word files from PDF + DOCX;
- this skill reads the already-reviewed `.docx` files, counts students, finds sensitive-content candidates, and helps produce a short teacher report.

## Install

Codex:

```powershell
git clone https://github.com/Mengfeifei-sm/chinese-autobiography-review-summary.git `
  "$env:USERPROFILE\.codex\skills\chinese-autobiography-review-summary"
```

Or copy this folder manually to:

```text
%USERPROFILE%\.codex\skills\chinese-autobiography-review-summary\
```

Other agents: use their documented skills directory; `SKILL.md` is the entry point.

## Requirements

- Python 3.10+
- `python-docx`

```powershell
python -m pip install python-docx
```

## Quick start

### 1. Scan the reviewed folder

```powershell
python .\scripts\scan_review.py `
  --input "C:\path\to\审核版\学生Word" `
  --out "C:\path\to\审核版\汇报材料\review_analysis"
```

This creates:

```text
review_scan.json
review_scan.md
sensitive_candidates.json
sensitive_candidates.md
review_meta.template.json
```

### 2. Fill `review_meta.json`

Copy `templates/review_meta.example.json` and fill only what the teacher provided. You may provide counts without names, names without counts, or both. Do not infer.

### 3. Review candidate context

Read `sensitive_candidates.md`. For each hit, read the sentence and the previous/next sentence. Create `sensitive_decisions.json` using `templates/sensitive_decisions.example.json`.

Each confirmed item can include:

- `label`: short teacher-facing label, e.g. `绝望`、`霸凌`、`离家出走`;
- `occurrences`: number of confirmed mentions, e.g. `2`;
- `context_type`: `personal_current`、`personal_past`、`third_party`、`uncertain` etc.;
- `severity`: `high`、`medium`、`low`;
- `quote`: exact local evidence, not shown in the short message.

### 4. Build the report

```powershell
python .\scripts\build_report.py `
  --scan "...\review_analysis\review_scan.json" `
  --decisions "...\review_analysis\sensitive_decisions.json" `
  --out "...\汇报材料" `
  --class-name "示例班" `
  --teacher "伍老师"
```

Outputs:

```text
审核汇总报告.docx
审核汇总报告.md
发给老师的汇报.txt
```

## Important

- Read-only on student files.
- Fully local; no upload, no cloud OCR/LLM.
- Keyword hits are not final sensitive conclusions.
- Never invent warning, missing-page, or completed counts.
- Sensitive quotes stay in the local report, not in chat.

## Files

```text
SKILL.md
scripts/scan_review.py
scripts/build_report.py
templates/review_meta.example.json
templates/sensitive_decisions.example.json
references/sensitive-context.md
references/report-format.md
```
