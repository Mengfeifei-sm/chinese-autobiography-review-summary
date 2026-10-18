---
name: chinese-autobiography-review-summary
description: Summarize a final human-reviewed Chinese autobiography batch (Word docx) and contextually classify sensitive content for a teacher report. Use for 审核版/汇报/汇总/敏感内容/预警/缺页漏页, after review, when a Word summary and a short message are needed.
---

# Chinese Autobiography Review Summary

Use this skill after a teacher/assistant has finished reviewing a batch of Chinese autobiography Word files. It produces a class-level summary and a short report, with **context-aware** sensitive-content review.

This is not the OCR proofreading skill. Do not rerun OCR or rewrite student documents.

## Critical rules

1. **Read-only on student files.** Never edit, move, rename, or delete the reviewed `.docx` files.
2. **Fully local.** Do not upload student text, names, or excerpts. Do not call cloud OCR/LLM/API.
3. **Never infer warning or missing-page counts from filenames, file size, or text length.** Use only the teacher's explicit `review_meta.json`, or mark them **待确认**. Do not copy another class's numbers.
4. **Never diagnose.** Classify what the text says and its context; do not label a student with a medical/psychological diagnosis.
5. **Context beats keywords.** A keyword hit is a candidate, not a confirmed sensitive item. Read the surrounding sentences before deciding.
6. **Do not include full sensitive passages in chat.** Keep quotes in the local report/JSON; summarize in chat.
7. **If uncertain, mark `uncertain` and ask the teacher.** Do not force a high/medium/low label.

## Workflow

### 1. Inventory the reviewed folder

Expected: one folder of final reviewed `.docx` files, usually one per student.

```powershell
python scripts\scan_review.py `
  --input "C:\path\to\审核版\学生Word" `
  --out "C:\path\to\审核版\汇报材料\review_analysis" `
  --meta "C:\path\to\审核版\汇报材料\review_meta.json"
```

The scan writes:

```text
review_scan.json
review_scan.md
sensitive_candidates.json
sensitive_candidates.md
```

It extracts paragraph/table text, counts unique students, and lists every sensitive-term occurrence with the containing sentence plus previous/next sentence.

### 2. Fill the count metadata — do not guess

Copy `templates/review_meta.example.json` and fill only what the teacher actually provided:

```json
{
  "class_name": "示例班",
  "total_students": 49,
  "warning_count": 1,
  "missing_pages_count": 4,
  "completed_count": 45,
  "warning": [],
  "missing_pages": []
}
```

Rules:

- Counts and names are optional independently.
- If `warning_count`/`missing_pages_count` are absent, the report says **待确认**.
- If only counts are known, leave the name arrays empty; do not invent names.
- If names are known, put them in the arrays and the count is derived.
- `completed_count` defaults to `total_students - missing_pages_count` only when both are known.
- The teacher's count overrides arithmetic; record `count_note` if needed.

### 3. Context-review every candidate

Read `sensitive_candidates.md` (or `sensitive_candidates.json`) in bounded batches. For each candidate, inspect:

- the exact sentence;
- previous and next sentence;
- whether the writer is speaking about self, a friend/relative, a hypothetical, a quote, a film/news story, or a general statement;
- time frame: past/resolved, current, future;
- negation and minimization;
- whether the term is literal or figurative.

Create `sensitive_decisions.json` from `templates/sensitive_decisions.example.json`.

Allowed context labels:

```text
personal_current
personal_past
personal_resolved
third_party
hypothetical
negated
quoted_media
figurative
general_statement
uncertain
```

Decision rules:

| Context | Action |
| --- | --- |
| Direct personal experience, current/persistent, literal | `confirmed`, severity `high` or `medium` |
| Personal past, resolved, no current risk | `confirmed`, severity `medium` or `low` |
| Witnessed/known third party | `confirmed`, context `third_party`; label clearly |
| Hypothetical/future "如果/哪怕" | exclude from personal sensitive list; note `hypothetical` |
| Negated "没有/从未/不再" | exclude; note `negated` |
| Film/news/book/quote | exclude as student's own experience; note `quoted_media` |
| Figurative "累死/笑死/社死/绝望坡" | exclude; note `figurative` |
| General academic statement "霸凌的危害" | exclude as personal; note `general_statement` |
| Cannot decide | `uncertain`; ask the teacher, do not report as fact |

Do not report a keyword-only list. The final `confirmed` list must contain the student, category, short summary, exact quote, context label, severity, and source file.

### 4. Build the report

```powershell
python scripts\build_report.py `
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

The short message uses only confirmed sensitive items. Unknown warning/missing counts appear as **待确认**, never as invented numbers.

### 5. Verify before reporting

- `reviewed: true` in decisions.
- confirmed count matches the unique students listed.
- report counts match `review_meta.json`.
- no excluded candidate appears in the confirmed table.
- Word file opens.
- no full sensitive quote in the chat reply.

## Candidate heuristics are not verdicts

`scan_review.py` assigns `attention` values:

- `high` — direct personal high-risk wording; read first.
- `medium` — possible personal/historical/third-party context.
- `context_needed` — keyword may be figurative, general, or ambiguous.
- `likely_not_personal` — likely negated/quoted/hypothetical; still spot-check.

Never copy these values directly into the final report. They only order human/agent review.

## What to report back

Bounded summary:

```text
已识别 N 份审核稿、M 名唯一学生。
预警 X（或待确认）；缺页漏页 Y（或待确认）；完成 Z（或待确认）。
敏感内容：确认 K 人 / L 处；排除候选 P 条。
报告：<path>
```

Do not enumerate all confirmed quotes in chat.

## References

- `references/sensitive-context.md` — detailed context examples and false positives.
- `references/report-format.md` — report sections and count semantics.
- `templates/review_meta.example.json` — count/name metadata.
- `templates/sensitive_decisions.example.json` — decisions format.
- `scripts/scan_review.py` — read-only extraction and candidate scan.
- `scripts/build_report.py` — report builder.
