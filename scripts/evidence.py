#!/usr/bin/env python3
"""Register read-only materials and preserve deliberately selected source excerpts."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from datetime import datetime, timezone
import xml.etree.ElementTree as ET
import zipfile

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from xikari_paths import require_external_output
finally:
    sys.path.pop(0)


FORMAT = "xikari-materials-1"
EXTRACTION_VERSIONS = {
    "txt": "evidence.py/2", "md": "evidence.py/2", "docx": "evidence.py/2",
    "csv": "evidence.py/1", "pdf": "evidence.py/1",
}
ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}\Z")
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


class MaterialError(Exception):
    pass


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def identity(data):
    return hashlib.sha256(data).hexdigest()


def valid_id(value):
    if not ID.fullmatch(value):
        raise MaterialError("ID须为1—80个英文字母、数字、点、短横线或下划线，首位为字母或数字。")
    return value


def read_bytes(path):
    try:
        return Path(path).read_bytes()
    except OSError as exc:
        raise MaterialError(f"无法读取材料 {path}: {exc}") from exc


def decode(data):
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise MaterialError("文本须为UTF-8；请让宿主另存转换副本并登记原始来源，保留原件。") from exc
    if "\x00" in text:
        raise MaterialError("文本含NUL字符，可能不是UTF-8文本；请检查格式或转换副本。")
    return text


def unit(locator, text, **location):
    return {"locator": locator, "text": text, "location": location}


def paragraph_text(element):
    def walk(node):
        if node.tag in {W + "del", W + "moveFrom", W + "txbxContent", W + "drawing", W + "pict"}:
            return ""
        if node.tag == W + "t":
            return node.text or ""
        if node.tag == W + "tab":
            return "\t"
        if node.tag in {W + "br", W + "cr"}:
            return "\n"
        return "".join(walk(child) for child in node)
    return walk(element)


def docx_units(data):
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            document = ET.fromstring(archive.read("word/document.xml"))
    except (zipfile.BadZipFile, KeyError, ET.ParseError, RuntimeError, OSError) as exc:
        raise MaterialError(f"DOCX正文损坏或缺失: {exc}") from exc
    body = document.find(W + "body")
    if body is None:
        raise MaterialError("DOCX没有可读取的正文body。")
    result = []

    def blocks(parent, prefix=""):
        paragraph = table = 0
        # Content controls wrap blocks without changing document order.
        def children(node):
            for child in node:
                if child.tag == W + "sdt":
                    content = child.find(W + "sdtContent")
                    if content is not None:
                        yield from children(content)
                elif child.tag in {W + "ins", W + "customXml"}:
                    yield from children(child)
                else:
                    yield child
        for child in children(parent):
            if child.tag == W + "p":
                paragraph += 1
                locator = f"{prefix}P{paragraph}"
                result.append(unit(locator, paragraph_text(child), kind="paragraph", document_order=len(result) + 1))
            elif child.tag == W + "tbl":
                table += 1
                table_id = f"{prefix}T{table}"
                rows = (row for row in children(child) if row.tag == W + "tr")
                for row_no, row in enumerate(rows, 1):
                    cells = (cell for cell in children(row) if cell.tag == W + "tc")
                    for cell_no, cell in enumerate(cells, 1):
                        if cell.find(W + "tcPr/" + W + "cellDel") is not None:
                            continue
                        blocks(cell, f"{table_id}R{row_no}C{cell_no}")
    blocks(body)
    return result, ["DOCX定位按正文XML顺序，不是排版页码；表格C是存储单元格序号，合并单元格可能不等于视觉列。仅提取正文段落和表格，忽略删除文字、移动来源文字及当前标记删除的单元格；不重建全部结构修订。页眉页脚、脚注尾注、文本框、图片、批注及外部嵌入对象需回源查看。"]


def extract(data, kind, delimiter=","):
    if kind in {"txt", "md"}:
        text = decode(data)
        result = [unit(f"L{i}", line.removesuffix("\n"), line=i) for i, line in enumerate(io.StringIO(text, newline=None), 1)]
        return result, ["L按此UTF-8文件的LF、CRLF或CR换行计数，行内其他字符保留；宿主转换文本的行号不能冒充原网页段落或原PDF页码。"]
    if kind == "csv":
        if len(delimiter) != 1 or delimiter in "\r\n\x00":
            raise MaterialError("CSV分隔符须为单个非换行字符。")
        result = []
        reader = csv.reader(io.StringIO(decode(data), newline=""), delimiter=delimiter, strict=True)
        old_limit = csv.field_size_limit()
        csv.field_size_limit(2**31 - 1)
        try:
            last_line = 0
            for record_no, record in enumerate(reader, 1):
                first_line, last_line = last_line + 1, reader.line_num
                if not record:
                    result.append(unit(f"R{record_no}", "", record=record_no, column=None, physical_lines=[first_line, last_line]))
                for col, value in enumerate(record, 1):
                    result.append(unit(f"R{record_no}C{col}", value, record=record_no, column=col, physical_lines=[first_line, last_line]))
        except csv.Error as exc:
            raise MaterialError(f"CSV解析失败，约在物理行 {reader.line_num}: {exc}") from exc
        finally:
            csv.field_size_limit(old_limit)
        return result, ["R按CSV记录计数，包含表头与空记录；C按字段计数。带引号的字段可跨物理行。单元格公式只作为文字，不执行。"]
    if kind == "docx":
        return docx_units(data)
    if kind == "pdf":
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise MaterialError("PDF需可选依赖pypdf。可使用宿主现有PDF工具提取并保留页码，另存UTF-8后以--origin与--locator-note登记；或在用户允许的环境安装pypdf。此命令未自动安装依赖或进行OCR。") from exc
        try:
            reader = PdfReader(io.BytesIO(data))
            if reader.is_encrypted and not reader.decrypt(""):
                raise MaterialError("PDF已加密；请使用有权访问的宿主工具生成可读提取副本。")
            result = [unit(f"PDF{i}", page.extract_text() or "", page=i) for i, page in enumerate(reader.pages, 1)]
        except MaterialError:
            raise
        except Exception as exc:
            raise MaterialError(f"PDF解析失败: {exc}") from exc
        empty = [u["location"]["page"] for u in result if not u["text"].strip()]
        if not result or len(empty) == len(result):
            raise MaterialError("PDF未提取到文字。扫描页需宿主OCR或人工回源；不能把空提取当作没有证据。")
        warnings = ["PDF定位是文件页序号，不一定等于印刷页码；多栏、表格和文字顺序应对照原页核实，未执行OCR。"]
        if empty:
            warnings.append("未提取到文字的PDF页: " + ", ".join(map(str, empty)))
        return result, warnings
    raise MaterialError(f"不支持的格式 {kind}；支持UTF-8 txt/md、csv、docx、pdf。请用宿主转换副本，保留原件与定位说明。")


def load_catalog(path, allow_missing=False):
    if not path.exists():
        if allow_missing:
            return {"format": FORMAT, "sources": {}, "clips": {}}
        raise MaterialError(f"材料目录不存在: {path}")
    try:
        catalog = json.loads(path.read_text(encoding="utf-8-sig"))
        if not isinstance(catalog, dict) or catalog.get("format") != FORMAT:
            raise ValueError("不是Xikari材料目录，不能覆盖")
        if not isinstance(catalog.get("sources"), dict) or not isinstance(catalog.get("clips"), dict):
            raise ValueError("sources或clips结构错误")
        for key, source in catalog["sources"].items():
            valid_id(key)
            if not isinstance(source, dict) or source.get("id") != key:
                raise ValueError("材料ID结构错误")
            if not all(isinstance(source.get(field), str) for field in ("path", "sha256", "kind", "title")):
                raise ValueError("材料身份字段缺失")
            if Path(source["path"]).resolve() == path.resolve():
                raise ValueError("目录不能也是已登记的原始材料")
        for key, clip in catalog["clips"].items():
            valid_id(key)
            if not isinstance(clip, dict) or clip.get("id") != key or clip.get("source_id") not in catalog["sources"]:
                raise ValueError("片段关联错误")
            if not isinstance(clip.get("source_extracts"), list):
                raise ValueError("片段结构错误")
    except (ValueError, OSError) as exc:
        raise MaterialError(f"无法使用材料目录 {path}: {exc}") from exc
    return catalog


def source_by_id(catalog, source_id):
    if source_id not in catalog["sources"]:
        raise MaterialError(f"未知材料ID: {source_id}")
    return catalog["sources"][source_id]


def current_status(source):
    try:
        data = Path(source["path"]).read_bytes()
    except FileNotFoundError:
        return {"state": "missing", "message": "原文件不存在；已保存片段仍属于登记时的源版本。"}
    except OSError as exc:
        return {"state": "unreadable", "message": str(exc)}
    digest = identity(data)
    return {"state": "current" if digest == source["sha256"] else "changed", "current_sha256": digest}


def live_units(source):
    data = read_bytes(source["path"])
    if identity(data) != source["sha256"]:
        raise MaterialError(f"材料 {source['id']} 的内容已变化，旧定位不能用于当前文件。以新ID add，并用--supersedes {source['id']}登记新版本；旧片段仍可show --clip查看。")
    if source["kind"] in {"txt", "md", "docx"} and source.get("extraction") != EXTRACTION_VERSIONS[source["kind"]]:
        raise MaterialError(f"材料 {source['id']} 的{source['kind'].upper()}提取版本与当前工具不一致或未登记，旧定位不能用于当前提取方式。以新ID add，并用--supersedes {source['id']}登记新版本；旧片段仍可show --clip查看。")
    return extract(data, source["kind"], source.get("delimiter", ","))


def select(units, selectors):
    selected = set()
    for selector in selectors:
        match = re.fullmatch(r"L(\d+):L(\d+)", selector)
        if match:
            start, end = map(int, match.groups())
            line_numbers = [u["location"]["line"] for u in units if "line" in u["location"]]
            if start < 1 or end < start or not line_numbers or end > max(line_numbers):
                raise MaterialError(f"行范围不存在: {selector}")
            wanted = {f"L{i}" for i in range(start, end + 1)}
            available = {u["locator"] for u in units}
            if start < 1 or end < start or not wanted or not wanted <= available:
                raise MaterialError(f"行范围不存在: {selector}")
            selected.update(wanted)
            continue
        matches = [u["locator"] for u in units if u["locator"] == selector or (
            re.fullmatch(r"R\d+|(?:T\d+R\d+C\d+)+|(?:T\d+R\d+C\d+)*T\d+", selector)
            and u["locator"].startswith(selector)
            and u["locator"][len(selector):len(selector) + 1] in {"C", "P", "T", "R"}
        )]
        if not matches:
            raise MaterialError(f"定位不存在: {selector}；先search查看实际定位。")
        selected.update(matches)
    return [u for u in units if u["locator"] in selected]


def save_catalog(path, catalog):
    require_external_output(path, __file__)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".xikari-materials-", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as output:
            json.dump(catalog, output, ensure_ascii=False, indent=2)
            output.write("\n")
            output.flush()
            os.fsync(output.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def mutate(path, operation, original=None):
    require_external_output(path, __file__)
    lock = path.with_name(path.name + ".lock")
    require_external_output(lock, __file__)
    if original is not None and original.resolve() in {path.resolve(), lock.resolve()}:
        raise MaterialError("目录或锁文件路径与原始材料相同，拒绝覆盖。请指定独立的任务工作目录。")
    # Read before creating any path; reject unrelated existing files.
    before = load_catalog(path, allow_missing=True)
    if any(Path(s["path"]).resolve() == lock.resolve() for s in before["sources"].values()):
        raise MaterialError("锁文件路径与已登记原始材料相同，拒绝写入。")
    existed = path.exists()
    previous_bytes = path.read_bytes() if existed else None
    # Validate and extract first, so unsupported/broken input leaves no catalog.
    result = operation(before)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        lock_fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise MaterialError(f"材料目录正在写入或遗留锁存在: {lock}；确认没有其他写入者后人工处理，未自动覆盖。") from exc
    try:
        os.close(lock_fd)
        if path.exists() != existed or (existed and path.read_bytes() != previous_bytes):
            raise MaterialError("材料目录在处理期间已改变；本次未写入，请重新执行。")
        save_catalog(path, before)
    finally:
        lock.unlink()
    return result


def add(catalog, args):
    valid_id(args.id)
    if args.id in catalog["sources"]:
        raise MaterialError(f"材料ID已存在，不能覆盖: {args.id}")
    if args.supersedes:
        source_by_id(catalog, args.supersedes)
    if args.origin and not args.locator_note:
        raise MaterialError("登记原URL或外部来源时需--locator-note，说明提取文本位置如何回到原材料。")
    path = Path(args.path).resolve()
    kind = args.type or path.suffix.lower().lstrip(".")
    delimiter = args.delimiter
    if kind == "tsv":
        kind, delimiter = "csv", "\t"
    data = read_bytes(path)
    units, warnings = extract(data, kind, delimiter)
    source = {
        "id": args.id, "title": args.title or path.name, "path": str(path),
        "kind": kind, "sha256": identity(data), "bytes": len(data),
        "source_date": args.source_date, "origin": args.origin,
        "locator_note": args.locator_note, "registered_at": now(),
        "supersedes": args.supersedes, "unit_count": len(units),
        "extraction": EXTRACTION_VERSIONS[kind], "extraction_limits": warnings,
    }
    if kind == "csv":
        source["delimiter"] = delimiter
    catalog["sources"][args.id] = source
    return {"source": source, "stored_content": "metadata_only"}


def clip(catalog, args):
    valid_id(args.clip_id)
    if args.clip_id in catalog["clips"]:
        raise MaterialError(f"片段ID已存在，不能覆盖: {args.clip_id}")
    source = source_by_id(catalog, args.id)
    units, warnings = live_units(source)
    record = {
        "id": args.clip_id, "source_id": args.id, "source_sha256": source["sha256"],
        "captured_at": now(), "source_extracts": select(units, args.at),
        "author_statement": args.claim, "support_boundary": args.support,
        "assumptions": args.assumption or [], "extraction_limits": warnings,
    }
    catalog["clips"][args.clip_id] = record
    return {"clip": record}


def parser():
    result = argparse.ArgumentParser(description="按需登记材料、定位原文和保存选定片段；不证明阅读完成，不判断来源可信度。")
    result.add_argument("--catalog", required=True, help="独立任务工作目录中的JSON材料目录")
    sub = result.add_subparsers(dest="command", required=True)
    command = sub.add_parser("add", help="登记一个不可覆盖的源版本，只保存元数据")
    command.add_argument("path")
    command.add_argument("--id", required=True)
    command.add_argument("--title")
    command.add_argument("--type", choices=["txt", "md", "csv", "tsv", "docx", "pdf"])
    command.add_argument("--delimiter", default=",")
    command.add_argument("--source-date", help="原材料形成/发布日期；未知时省略，不以登记日期替代")
    command.add_argument("--origin", help="原网页URL、访谈或原始文件身份；不会联网下载")
    command.add_argument("--locator-note", help="提取定位与原材料对应方式及丢失内容")
    command.add_argument("--supersedes", help="被此新版本替代的旧材料ID，旧条目保持原样")
    sub.add_parser("list", help="列出源版本、片段ID及文件当前状态")
    command = sub.add_parser("search", help="搜索登记版本的原文；源已变时要求先登记新版本")
    command.add_argument("query")
    command.add_argument("--id", action="append", help="限定材料，可重复；省略搜索全部")
    command.add_argument("--limit", type=int, default=20)
    command = sub.add_parser("show", help="查看材料元数据、精确定位原文或已保存片段")
    group = command.add_mutually_exclusive_group(required=True)
    group.add_argument("--id")
    group.add_argument("--clip")
    command.add_argument("--at", action="append", help="可重复，如L3:L7、R2C3、T1R2C1P1、PDF4")
    command = sub.add_parser("clip", help="明确选取片段保存；作者判断与来源原文分开")
    command.add_argument("--id", required=True, help="材料ID")
    command.add_argument("--clip-id", required=True)
    command.add_argument("--at", action="append", required=True)
    command.add_argument("--claim", help="作者提出的判断，不会标为来源原文")
    command.add_argument("--support", required=True, help="作者填写：片段能支持什么、不能支持什么")
    command.add_argument("--assumption", action="append", help="需要额外成立的假设，可重复")
    return result


def run(args):
    path = Path(args.catalog)
    if args.command == "add":
        require_external_output(path, __file__)
        path = path.resolve()
        return mutate(path, lambda catalog: add(catalog, args), Path(args.path))
    if args.command == "clip":
        require_external_output(path, __file__)
        path = path.resolve()
        return mutate(path, lambda catalog: clip(catalog, args))
    catalog = load_catalog(path)
    if args.command == "list":
        return {"sources": [{**s, "status": current_status(s)} for s in catalog["sources"].values()], "clip_ids": list(catalog["clips"])}
    if args.command == "show":
        if args.clip:
            if args.at:
                raise MaterialError("show --clip读取已保存的选定片段，不能同时指定--at。")
            if args.clip not in catalog["clips"]:
                raise MaterialError(f"未知片段ID: {args.clip}")
            record = catalog["clips"][args.clip]
            source = source_by_id(catalog, record["source_id"])
            return {"clip": record, "source": source, "status": current_status(source), "notice": "片段属于登记时的源版本；文件状态不判定其真实性或法律有效性。"}
        source = source_by_id(catalog, args.id)
        if not args.at:
            return {"source": source, "status": current_status(source)}
        units, warnings = live_units(source)
        return {"source_id": args.id, "source_sha256": source["sha256"], "source_extracts": select(units, args.at), "extraction_limits": warnings}
    if args.command == "search":
        if not args.query or args.limit < 1:
            raise MaterialError("搜索词不能为空，limit须大于0。")
        sources = [source_by_id(catalog, key) for key in args.id] if args.id else list(catalog["sources"].values())
        matches, skipped, warnings = [], [], {}
        for source in sources:
            try:
                units, limits = live_units(source)
            except MaterialError as exc:
                skipped.append({"source_id": source["id"], "reason": str(exc)})
                continue
            warnings[source["id"]] = limits
            matches.extend({"source_id": source["id"], "source_sha256": source["sha256"], **u} for u in units if args.query.casefold() in u["text"].casefold())
        return {"matches": matches[:args.limit], "total_matches": len(matches), "truncated": len(matches) > args.limit, "skipped_sources": skipped, "complete": not skipped, "extraction_limits": warnings}
    raise MaterialError("未知命令。")


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        result = run(args)
    except (MaterialError, OSError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    raise SystemExit(main())
