# Review report format

## Count semantics

| Field | Source | If missing |
| --- | --- | --- |
| total_students | meta, else unique docx count | use unique count |
| warning_count | meta only | `待确认` |
| missing_pages_count | meta only | `待确认` |
| completed_count | meta; else total - missing | `待确认` |
| warning names | meta list only | no names, keep count |
| missing names | meta list only | no names, keep count |

Never infer warning or missing-page names from:

- file size;
- text length;
- number of sections;
- another class's report;
- the phrase "缺页" appearing in a student's text.

If the teacher only gives counts, report counts and state "名单未提供". If the teacher gives names but no count, count the names.

## Report sections

1. **总体情况** — files, unique students, warning/missing/completed, confirmed sensitive students.
2. **敏感内容明细** — student, category, short summary, severity, context label. Do not include long quotes.
3. **给老师的简短汇报** — copy-ready short message.
4. **口径与限制** — count source, read-only statement, sensitive-review caveat.

## Short message

Use the counts only when all required values are known. Otherwise:

```text
XX班自传共49人；预警、缺页漏页及完成情况待确认。
```

Do not generate a false "完成45人" from an assumed missing count.

## Sensitive wording

- Use neutral labels: "自伤/自杀风险", "情绪困扰", "霸凌/暴力", "家庭风险", "性侵害/骚扰", "丧亲/死亡", "伤害/受伤".
- Do not diagnose.
- For third-party content, write "涉及同学/朋友" or `context_type=third_party`.
- For past/resolved content, add "过去/已走出" in the summary.
- For uncertain content, do not put it in the confirmed table; list it in a separate "待确认" note only if the teacher needs it.

## Privacy

- All outputs remain local.
- Do not paste full sensitive excerpts into chat.
- Do not upload the reports or candidate JSON to GitHub or any external service.
