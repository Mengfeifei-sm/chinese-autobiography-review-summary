# Context rules for sensitive content

A keyword hit is only a lead. Decide from the **sentence plus at least one sentence before and after**.

## Context labels

| Label | Meaning | Report? |
| --- | --- | --- |
| `personal_current` | 本人，当前/持续，字面意思 | yes, usually high/medium |
| `personal_past` | 本人，过去发生 | yes, usually medium/low |
| `personal_resolved` | 本人，已过去且明确走出 | yes, low/medium, note resolved |
| `third_party` | 同学、朋友、家人、听说/看到 | yes, label third party; not the writer's own experience |
| `hypothetical` | 如果/假如/哪怕/将来 | no as fact; note hypothetical |
| `negated` | 没有/从未/不再/并非 | no |
| `quoted_media` | 电影/新闻/书/网络/别人说的话 | no as student's own experience |
| `figurative` | 笑死/累死/社死/绝望坡/崩溃边缘 | no |
| `general_statement` | 泛泛讨论“霸凌的危害” | no as personal |
| `uncertain` | 无法判断 | do not report as fact; ask teacher |

## Examples

### Confirmed, personal

> 那段时间我每天都很绝望，晚上经常睡不着，也不想见人。

Context: first person, persistent, literal. Confirm emotion, medium/high; do not diagnose depression.

> 我小时候被同学堵在厕所里打过。

First person, past, literal violence. Confirm violence; severity medium/high depending on wording; label `personal_past`.

> 我朋友被她爸爸打过，她后来离家出走了。

Third party, literal. Confirm family/violence with `third_party`; do not attribute to the writer.

### Excluded

> 军训太累了，我快崩溃了。

Figurative/minimizer. Exclude from crisis list; maybe note as ordinary stress.

> 如果我被霸凌，我一定会告诉老师。

Hypothetical. Exclude as personal experience.

> 我从来没有想过自杀。

Negated. Exclude.

> 电影里的主角选择了自杀。

Quoted media. Exclude as student's own experience.

> 熬夜会伤害身体。

General health statement. Exclude from personal harm.

> 我家在绝望坡附近。

Toponym/figurative. Exclude.

### Uncertain

> 那段时间真的很难，有时候觉得不如消失。

Possible self-harm ideation but ambiguous. Mark `uncertain`, quote the full sentence, and ask the teacher rather than assigning a diagnosis.

## Severity

Use only three levels:

- `high`: direct, current, explicit self-harm/violence/abuse/sexual harm, or persistent severe distress.
- `medium`: personal but past/resolved, third-party, or clear distress without immediate risk.
- `low`: brief historical mention, no current risk, but still relevant.

Do not use clinical terms (e.g. "重度抑郁症") unless the student explicitly says a clinician diagnosed it; even then report it as self-report, not your diagnosis.

## Deduplication

- One student + one category + one incident = one confirmed entry.
- Repeated mentions of the same feeling can be one entry with a note "多处提及".
- Do not count every keyword occurrence as a separate sensitive item in the short message.
- The report can say "学生A：伤害（2处）" when two distinct incidents/mentions are confirmed.
