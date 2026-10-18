#!/usr/bin/env python3
"""Read-only inventory and sensitive-candidate scan for reviewed autobiography Word files.

This script does not decide whether a candidate is truly sensitive. It extracts the
sentence plus surrounding context and assigns a review-priority hint.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path

from docx import Document

CATEGORIES = {
    "self_harm": {
        "label": "自伤/自杀风险",
        "terms": [
            "自杀", "轻生", "不想活", "活不下去", "活着没意思", "自残", "割腕",
            "跳楼", "安眠药", "结束生命", "一了百了", "死了算了", "想死",
        ],
    },
    "emotion": {
        "label": "情绪困扰",
        "terms": [
            "绝望", "崩溃", "抑郁", "重度抑郁", "焦虑", "无助", "想哭",
            "活着好累", "压抑", "自暴自弃", "想不开",
        ],
    },
    "violence": {
        "label": "霸凌/暴力",
        "terms": [
            "霸凌", "校园暴力", "欺凌", "殴打", "挨打", "被打", "辱骂",
            "网暴", "网络暴力", "孤立", "排挤", "扇耳光", "欺负",
        ],
    },
    "family": {
        "label": "家庭风险",
        "terms": ["家暴", "家庭暴力", "虐待", "打骂", "离家出走", "被赶出", "赶出家门", "重男轻女"],
    },
    "sexual": {
        "label": "性侵害/骚扰",
        "terms": ["性侵", "猥亵", "性骚扰", "骚扰", "强奸"],
    },
    "grief": {
        "label": "丧亲/死亡",
        "terms": ["去世", "离世", "葬礼", "墓前", "车祸", "溺水", "病逝"],
    },
    "harm": {
        "label": "伤害/受伤",
        "terms": ["伤害", "自伤", "受伤", "流血"],
    },
}

HIGH_RISK = {"self_harm", "violence", "family", "sexual"}
TERM_TO_CATEGORY = {
    term: key for key, value in CATEGORIES.items() for term in value["terms"]
}
ALL_TERMS = sorted(TERM_TO_CATEGORY, key=len, reverse=True)
TERM_PATTERNS = {
    # Avoid ordinary compounds such as 被打断, 绝望坡, 自杀式.
    term: re.compile(re.escape(term) + suffix)
    for term, suffix in {
        "被打": r"(?!断|开|动|扰|破|败)",
        "绝望": r"(?!坡)",
        "自杀": r"(?!式|性)",
    }.items()
}

SENTENCE_RE = re.compile(r"[^。！？!?；;\n]+[。！？!?；;]?")
HAN_RE = re.compile(r"[\u4e00-\u9fff]")
ID_RE = re.compile(r"\d{6,}")


def parse_stem(stem: str) -> tuple[str, str]:
    match = ID_RE.search(stem)
    if not match:
        return "", stem.strip(" _-—+")
    student_id = match.group(0)
    name = (stem[: match.start()] + stem[match.end() :]).strip(" _-—+")
    return student_id, name or stem


def sentences_with_spans(text: str) -> list[tuple[int, int, str]]:
    result = []
    for match in SENTENCE_RE.finditer(text):
        sentence = match.group(0).strip()
        if sentence:
            result.append((match.start(), match.end(), sentence))
    if not result and text.strip():
        result.append((0, len(text), text.strip()))
    return result


def sentence_context(text: str, position: int) -> tuple[str, str]:
    parts = sentences_with_spans(text)
    if not parts:
        return "", ""
    index = 0
    for i, (start, end, _) in enumerate(parts):
        if start <= position <= end:
            index = i
            break
    current = parts[index][2]
    context_parts = [parts[i][2] for i in range(max(0, index - 1), min(len(parts), index + 2))]
    context = " ".join(context_parts)
    if len(context) > 320:
        left = max(0, position - 160)
        right = min(len(text), position + 160)
        context = text[left:right]
    return current, context


def flags_for(sentence: str, context: str, before: str, term: str) -> list[str]:
    flags = []
    if re.search(r"我|自己|本人|我们", context):
        flags.append("first_person")
    if re.search(r"同学|朋友|别人|他们|她们|(?<!其)他|(?<!其)她|家人|父母|老师|邻居|听说|看到|见到", context):
        flags.append("third_party")
    if re.search(r"电影|电视|新闻|网上|网络|书里|小说|案例|课堂|老师讲", context):
        flags.append("media")
    if re.search(r"如果|假如|要是|即使|哪怕|万一|将来|未来|有一天|若", context):
        flags.append("hypothetical")
    if not term.startswith("不") and re.search(
        r"(?:没有|没|从未|不曾|不再|并不|并非|不是|无).{0,6}$", before
    ):
        flags.append("negated")
    if re.search(r"“|”|「|」", context):
        flags.append("quoted_or_dialogue")
    if re.search(r"有点|一点|稍微|偶尔|开玩笑|笑死|累死|困死|社死|尴尬死", context):
        flags.append("minimizer")
    if re.search(r"长期|一直|每天|经常|严重|重度|持续|多年|反复|越来越", context):
        flags.append("intensifier")
    if re.search(r"曾经|当时|那时|小时候|初中|高中|以前|过去|那年", context):
        flags.append("past")
    if re.search(r"现在|最近|目前|这学期|大学|大一", context):
        flags.append("current")
    if re.search(r"我挺了过来|我没有放弃|后来我|如今我|现在已经|已经走出|最终我|但我没有", context):
        flags.append("resolved")
    return flags


def attention_for(category: str, flags: list[str], sentence: str) -> str:
    if "negated" in flags:
        return "likely_not_personal"
    if "media" in flags and "first_person" not in flags:
        return "likely_not_personal"
    if "hypothetical" in flags and "past" not in flags:
        return "likely_not_personal"
    if "quoted_or_dialogue" in flags and "first_person" not in flags:
        return "likely_not_personal"
    if category in HIGH_RISK:
        if "first_person" in flags and "third_party" not in flags:
            return "medium" if "resolved" in flags else "high"
        if "first_person" in flags or "third_party" in flags:
            return "medium"
        return "context_needed"
    if category == "emotion":
        severe = any(term in sentence for term in ("绝望", "抑郁", "想哭", "活着好累", "自暴自弃", "想不开"))
        if "first_person" in flags and "intensifier" in flags and severe:
            return "medium" if "resolved" in flags else "high"
        if "first_person" in flags:
            return "medium"
        return "context_needed"
    if category in {"grief", "harm"}:
        return "medium" if "first_person" in flags else "context_needed"
    return "context_needed"


def extract_chunks(path: Path) -> tuple[list[str], list[str]]:
    doc = Document(str(path))
    chunks: list[str] = []
    errors: list[str] = []

    for paragraph in doc.paragraphs:
        text = paragraph.text.strip()
        if text:
            chunks.append(text)

    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    text = paragraph.text.strip()
                    if text and text not in chunks:
                        chunks.append(text)

    return chunks, errors


def candidate_scan(paragraphs: list[str], student: dict[str, object]) -> list[dict[str, object]]:
    candidates: list[dict[str, object]] = []
    seen: set[tuple[str, str]] = set()

    for p_index, paragraph in enumerate(paragraphs, start=1):
        matches = []
        for term in ALL_TERMS:
            pattern = TERM_PATTERNS.get(term, re.compile(re.escape(term)))
            for match in pattern.finditer(paragraph):
                matches.append((match.start(), match.end(), term))
        matches.sort(key=lambda item: (item[0], -(item[1] - item[0])))

        chosen = []
        occupied: list[tuple[int, int]] = []
        for start, end, term in matches:
            if any(start < e and end > s for s, e in occupied):
                continue
            occupied.append((start, end))
            chosen.append((start, end, term))

        for start, end, term in chosen:
            category = TERM_TO_CATEGORY[term]
            sentence, context = sentence_context(paragraph, start)
            before = paragraph[max(0, start - 18) : start]
            flags = flags_for(sentence, context, before, term)
            attention = attention_for(category, flags, sentence)
            key = (category, sentence)
            if key in seen:
                continue
            seen.add(key)
            candidates.append(
                {
                    "student": student["name"],
                    "student_id": student["student_id"],
                    "file": student["file"],
                    "paragraph": p_index,
                    "term": term,
                    "category": category,
                    "category_label": CATEGORIES[category]["label"],
                    "sentence": sentence,
                    "context": context,
                    "attention": attention,
                    "flags": flags,
                }
            )
    return candidates


def normalize_names(value: object) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        return [str(value)]
    result = []
    for item in value:
        if isinstance(item, dict):
            name = item.get("name") or item.get("student") or item.get("student_id")
            if name:
                result.append(str(name).strip())
        elif item:
            result.append(str(item).strip())
    return result


def normalize_meta(meta: dict[str, object] | None, student_count: int) -> tuple[dict[str, object], list[str]]:
    meta = meta or {}
    warnings: list[str] = []
    warning_names = normalize_names(meta.get("warning"))
    missing_names = normalize_names(meta.get("missing_pages"))

    warning_count = meta.get("warning_count")
    missing_count = meta.get("missing_pages_count")
    completed_count = meta.get("completed_count")
    total = meta.get("total_students")

    if warning_count is None and "warning" in meta:
        warning_count = len(warning_names)
    if missing_count is None and "missing_pages" in meta:
        missing_count = len(missing_names)
    if total is None:
        total = student_count
    if total is not None and int(total) != student_count:
        warnings.append(f"meta total_students={total}，但文件夹实际识别 {student_count} 名学生")
    if warning_count is not None and "warning" in meta and len(warning_names) not in (0, int(warning_count)):
        warnings.append(f"warning_count={warning_count}，但 warning 名单有 {len(warning_names)} 人")
    if missing_count is not None and "missing_pages" in meta and len(missing_names) not in (0, int(missing_count)):
        warnings.append(f"missing_pages_count={missing_count}，但 missing_pages 名单有 {len(missing_names)} 人")
    if completed_count is None and total is not None and missing_count is not None:
        completed_count = int(total) - int(missing_count)
    if total is not None and completed_count is not None and int(completed_count) > int(total):
        warnings.append(f"completed_count={completed_count} 大于 total_students={total}")
    if (
        total is not None
        and missing_count is not None
        and completed_count is not None
        and int(completed_count) != int(total) - int(missing_count)
    ):
        warnings.append(
            f"completed_count={completed_count} 与 total_students - missing_pages_count="
            f"{int(total) - int(missing_count)} 不一致"
        )
    if warning_count is not None and completed_count is not None and int(warning_count) > int(completed_count):
        warnings.append(f"warning_count={warning_count} 大于 completed_count={completed_count}")

    return (
        {
            "class_name": str(meta.get("class_name") or ""),
            "total_students": int(total) if total is not None else None,
            "warning_count": int(warning_count) if warning_count is not None else None,
            "missing_pages_count": int(missing_count) if missing_count is not None else None,
            "completed_count": int(completed_count) if completed_count is not None else None,
            "warning": warning_names,
            "missing_pages": missing_names,
            "count_source": "meta" if meta else "unknown",
            "count_note": str(meta.get("count_note") or ""),
        },
        warnings,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan reviewed autobiography Word files without modifying them.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--meta", default="")
    args = parser.parse_args()

    input_dir = Path(args.input).expanduser().resolve()
    out_dir = Path(args.out).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    if not input_dir.exists():
        raise SystemExit(f"输入目录不存在：{input_dir}")

    docx_files = sorted(
        path for path in input_dir.rglob("*.docx") if not path.name.startswith("~$")
    )
    students: list[dict[str, object]] = []
    unreadable: list[dict[str, str]] = []
    all_candidates: list[dict[str, object]] = []
    seen_ids: dict[str, int] = {}

    for path in docx_files:
        student_id, name = parse_stem(path.stem)
        student = {
            "student_id": student_id,
            "name": name,
            "file": str(path),
            "chars": 0,
            "paragraphs": 0,
        }
        try:
            chunks, _ = extract_chunks(path)
            text = "\n".join(chunks)
            student["chars"] = len(HAN_RE.findall(text))
            student["paragraphs"] = len(chunks)
            candidates = candidate_scan(chunks, student)
            all_candidates.extend(candidates)
            student["candidate_count"] = len(candidates)
        except Exception as exc:
            unreadable.append({"file": str(path), "error": str(exc)})
            student["candidate_count"] = 0
            student["error"] = str(exc)
        if student_id:
            seen_ids[student_id] = seen_ids.get(student_id, 0) + 1
        students.append(student)

    for item in all_candidates:
        item["id"] = ""
    for index, item in enumerate(
        sorted(all_candidates, key=lambda x: (str(x["student_id"]), str(x["student"]), int(x["paragraph"]))),
        start=1,
    ):
        item["id"] = f"S{index:03d}"

    meta_path = Path(args.meta).expanduser() if args.meta else None
    raw_meta = None
    if meta_path and meta_path.exists():
        raw_meta = json.loads(meta_path.read_text(encoding="utf-8-sig"))
    meta, meta_warnings = normalize_meta(raw_meta, len(students))

    by_category: dict[str, int] = {}
    by_attention: dict[str, int] = {}
    by_student: dict[str, int] = {}
    for item in all_candidates:
        by_category[item["category"]] = by_category.get(item["category"], 0) + 1
        by_attention[item["attention"]] = by_attention.get(item["attention"], 0) + 1
        key = f"{item['student_id']}_{item['student']}"
        by_student[key] = by_student.get(key, 0) + 1

    result = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "input_dir": str(input_dir),
        "doc_count": len(docx_files),
        "student_count": len(students),
        "unique_ids": len(seen_ids),
        "duplicate_ids": {key: value for key, value in seen_ids.items() if value > 1},
        "unreadable": unreadable,
        "meta": meta,
        "meta_warnings": meta_warnings,
        "students": students,
        "candidate_count": len(all_candidates),
        "by_category": by_category,
        "by_attention": by_attention,
        "by_student": by_student,
        "candidates": all_candidates,
    }

    (out_dir / "review_scan.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )

    template = {
        "class_name": meta.get("class_name") or input_dir.parent.name,
        "total_students": len(students),
        "warning_count": None,
        "missing_pages_count": None,
        "completed_count": None,
        "warning": [],
        "missing_pages": [],
        "count_note": "只填写老师明确提供的人数/名单；没有提供就保留 null。",
    }
    (out_dir / "review_meta.template.json").write_text(
        json.dumps(template, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    lines = [
        "# 审核版扫描结果",
        "",
        f"> 生成时间：{result['generated_at']}  ",
        f"> 输入目录：`{input_dir}`",
        "",
        "## 一、文件识别",
        "",
        "| 项目 | 数量 |",
        "| --- | --- |",
        f"| Word 文件 | {result['doc_count']} |",
        f"| 唯一学生 | {result['student_count']} |",
        f"| 可读取 | {result['doc_count'] - len(unreadable)} |",
        f"| 读取失败 | {len(unreadable)} |",
        f"| 敏感候选 | {result['candidate_count']} |",
        "",
        "## 二、审核口径",
        "",
        f"- 预警人数：{meta['warning_count'] if meta['warning_count'] is not None else '待确认'}",
        f"- 缺页漏页人数：{meta['missing_pages_count'] if meta['missing_pages_count'] is not None else '待确认'}",
        f"- 完成人数：{meta['completed_count'] if meta['completed_count'] is not None else '待确认'}",
        f"- 统计来源：{meta['count_source']}",
    ]
    if meta["warning"]:
        lines.append(f"- 预警名单：{'、'.join(meta['warning'])}")
    if meta["missing_pages"]:
        lines.append(f"- 缺页漏页名单：{'、'.join(meta['missing_pages'])}")
    if meta_warnings:
        lines.extend(["", "**口径警告：**"])
        lines.extend(f"- {item}" for item in meta_warnings)
    lines.extend(
        [
            "",
            "## 三、敏感候选分布",
            "",
            "| 类别 | 候选数 |",
            "| --- | --- |",
        ]
    )
    for category, count in sorted(by_category.items(), key=lambda item: -item[1]):
        lines.append(f"| {CATEGORIES[category]['label']} | {count} |")
    lines.extend(["", "| 复核优先级 | 候选数 |", "| --- | --- |"])
    for attention, count in sorted(by_attention.items(), key=lambda item: -item[1]):
        lines.append(f"| {attention} | {count} |")
    lines.extend(
        [
            "",
            "## 四、下一步",
            "",
            "1. 阅读 `sensitive_candidates.md`，结合每条的前后文判定。",
            "2. 按 `templates/sensitive_decisions.example.json` 写 `sensitive_decisions.json`。",
            "3. 运行 `build_report.py` 生成汇报。",
            "",
            "详细候选上下文见 `sensitive_candidates.md`；本文件不给出最终敏感结论。",
        ]
    )
    (out_dir / "review_scan.md").write_text("\n".join(lines), encoding="utf-8-sig", newline="\n")

    candidate_lines = [
        "# 敏感候选上下文",
        "",
        "> 这些是关键词候选，不是最终结论。逐条结合前后文判断，再写入 `sensitive_decisions.json`。",
        "",
    ]
    if not all_candidates:
        candidate_lines.append("未发现候选。")
    for item in sorted(
        all_candidates,
        key=lambda x: ({"high": 0, "medium": 1, "context_needed": 2, "likely_not_personal": 3}.get(str(x["attention"]), 4), str(x["student_id"]), int(x["paragraph"])),
    ):
        candidate_lines.extend(
            [
                f"## {item['id']}｜{item['student']}｜{item['category_label']}｜{item['attention']}",
                "",
                f"- 文件：`{Path(str(item['file'])).name}`",
                f"- 段落：第 {item['paragraph']} 段",
                f"- 命中词：{item['term']}",
                f"- 原文：{item['sentence']}",
                f"- 上下文：{item['context']}",
                f"- 提示：{', '.join(item['flags']) or '无'}",
                "",
            ]
        )
    (out_dir / "sensitive_candidates.md").write_text(
        "\n".join(candidate_lines), encoding="utf-8-sig", newline="\n"
    )
    (out_dir / "sensitive_candidates.json").write_text(
        json.dumps(
            {
                "generated_at": result["generated_at"],
                "input_dir": str(input_dir),
                "candidate_count": len(all_candidates),
                "candidates": all_candidates,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"documents={len(docx_files)} students={len(students)} candidates={len(all_candidates)}")
    print(str(out_dir / "review_scan.json"))
    print(str(out_dir / "sensitive_candidates.md"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
