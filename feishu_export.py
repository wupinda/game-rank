#!/usr/bin/env python3
"""
将 README.md 导出为飞书文档（Word 导入方式，完整还原表格/代码块/标题）
用法: python feishu_export.py
"""
import re
import sys
import time
import os
import io
import requests
from docx import Document
from docx.shared import Pt, RGBColor
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

APP_ID     = "cli_aa9d44ade9395bdb"
APP_SECRET = "MKCPGIW5YmV7i94UQH3bLc3Polugu3xG"
BASE       = "https://open.feishu.cn/open-apis"

import sys as _sys
_default_md = "GUIDE.md" if len(_sys.argv) < 2 else _sys.argv[1]
README = os.path.join(os.path.dirname(os.path.abspath(__file__)), _default_md)


# ── Auth ──────────────────────────────────────────────────────────────────────

def get_token() -> str:
    r = requests.post(f"{BASE}/auth/v3/tenant_access_token/internal",
                      json={"app_id": APP_ID, "app_secret": APP_SECRET})
    d = r.json()
    if d.get("code") != 0:
        sys.exit(f"认证失败: {d}")
    return d["tenant_access_token"]


def H(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── Build .docx from README ───────────────────────────────────────────────────

_STRIP_MD = re.compile(r'\*\*|(?:^|\s)`+|`+(?:\s|$)')


def clean(text: str) -> str:
    return _STRIP_MD.sub(" ", text).strip()


def set_code_style(para):
    """Apply monospace font to a paragraph."""
    for run in para.runs:
        run.font.name = "Courier New"
        run.font.size = Pt(9)
        run.font.color.rgb = RGBColor(0x1F, 0x2D, 0x3D)
    # light gray shading
    pPr = para._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), "F3F4F6")
    pPr.append(shd)


def build_docx(readme: str) -> bytes:
    doc   = Document()
    lines = readme.split("\n")
    i     = 0

    while i < len(lines):
        line = lines[i]

        # ── Heading ──────────────────────────────────────────
        m = re.match(r'^(#{1,3})\s+(.*)', line)
        if m:
            level = len(m.group(1))
            text  = clean(m.group(2))
            doc.add_heading(text, level=level)
            i += 1
            continue

        # ── Fenced code block ─────────────────────────────────
        if line.startswith("```"):
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                code_lines.append(lines[i])
                i += 1
            code_text = "\n".join(code_lines)
            para = doc.add_paragraph()
            para.add_run(code_text)
            set_code_style(para)
            i += 1
            continue

        # ── Markdown table ────────────────────────────────────
        if ("|" in line
                and i + 1 < len(lines)
                and re.match(r'^\|[\s\-:|]+\|', lines[i + 1])):
            header = [c.strip() for c in line.strip().strip("|").split("|")]
            i += 2   # skip separator
            rows = [header]
            while i < len(lines) and "|" in lines[i]:
                row = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                rows.append(row)
                i += 1
            n_cols = max(len(r) for r in rows)
            tbl = doc.add_table(rows=len(rows), cols=n_cols)
            tbl.style = "Table Grid"
            for ri, row in enumerate(rows):
                for ci, cell_text in enumerate(row):
                    cell = tbl.cell(ri, ci)
                    cell.text = cell_text
                    if ri == 0:  # bold header
                        for run in cell.paragraphs[0].runs:
                            run.bold = True
            doc.add_paragraph()  # spacing after table
            continue

        # ── Bullet ────────────────────────────────────────────
        m = re.match(r'^[-*]\s+(.*)', line)
        if m:
            doc.add_paragraph(clean(m.group(1)), style="List Bullet")
            i += 1
            continue

        # ── Horizontal rule ───────────────────────────────────
        if re.match(r'^-{3,}$', line.strip()):
            doc.add_paragraph("─" * 40)
            i += 1
            continue

        # ── Plain paragraph ───────────────────────────────────
        stripped = clean(line)
        if stripped:
            doc.add_paragraph(stripped)
        i += 1

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


# ── Upload to Feishu Drive ────────────────────────────────────────────────────

def get_root_folder(token: str) -> str:
    r = requests.get(f"{BASE}/drive/explorer/v2/root_folder/meta", headers=H(token))
    d = r.json()
    if d.get("code") != 0:
        return ""
    return d.get("data", {}).get("token", "")


def upload_file(token: str, filename: str, data: bytes, folder_token: str) -> str:
    size = len(data)
    fields = {
        "file_name":   (None, filename),
        "parent_type": (None, "explorer"),
        "parent_node": (None, folder_token),
        "size":        (None, str(size)),
        "file":        (filename, data, "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
    }
    r = requests.post(
        f"{BASE}/drive/v1/files/upload_all",
        headers=H(token),
        files=fields,
    )
    d = r.json()
    if d.get("code") != 0:
        sys.exit(f"上传失败: {d}")
    return d["data"]["file_token"]


# ── Import as Feishu Doc ──────────────────────────────────────────────────────

def create_import_task(token: str, file_token: str, folder_token: str = "") -> str:
    r = requests.post(
        f"{BASE}/drive/v1/import_tasks",
        headers={**H(token), "Content-Type": "application/json"},
        json={
            "file_extension": "docx",
            "file_token":     file_token,
            "type":           "docx",
            "point": {"mount_type": 1, "mount_key": folder_token},
        },
    )
    d = r.json()
    if d.get("code") != 0:
        sys.exit(f"创建导入任务失败: {d}")
    return d["data"]["ticket"]


def poll_import(token: str, ticket: str, timeout: int = 90) -> tuple:
    time.sleep(3)   # wait for task to start
    fail_count = 0
    deadline = time.time() + timeout
    while time.time() < deadline:
        r = requests.get(f"{BASE}/drive/v1/import_tasks/{ticket}", headers=H(token))
        d = r.json()
        result = d.get("data", {}).get("result", {})
        status = result.get("job_status")
        if status == 0:   # success
            return result.get("token", ""), result.get("url", "")
        if status in (2, 3):  # failed / cancelled
            fail_count += 1
            if fail_count >= 3:
                sys.exit(f"导入任务失败: {result}")
        time.sleep(2)
    sys.exit("导入任务超时")


# ── Main ──────────────────────────────────────────────────────────────────────

def share_with_org(token: str, doc_token: str):
    requests.patch(
        f"{BASE}/drive/v1/permissions/{doc_token}/public",
        headers={**H(token), "Content-Type": "application/json"},
        params={"type": "docx"},
        json={
            "security_entity":      "anyone_can_edit",
            "link_share_entity":    "tenant_editable",
            "external_access_entity": "closed",
        },
    )


def main():
    print("1/6  获取访问令牌…")
    token = get_token()

    print(f"2/6  生成 Word 文档（{os.path.basename(README)}）…")
    with open(README, "r", encoding="utf-8") as f:
        readme = f.read()
    # Use first H1 as doc title, fallback to filename
    title_match = __import__('re').search(r'^#\s+(.+)', readme, __import__('re').M)
    doc_title = title_match.group(1).strip() if title_match else os.path.splitext(os.path.basename(README))[0]
    docx_bytes = build_docx(readme)
    print(f"     标题: {doc_title}  大小: {len(docx_bytes):,} 字节")

    print("3/6  获取云盘根目录…")
    folder_token = get_root_folder(token)
    if not folder_token:
        print("     ⚠ 未获取到根目录 token，将上传到应用默认位置")

    print("4/6  上传到飞书云盘…")
    safe_name = doc_title.replace("/", "_").replace("\\", "_")[:60] + ".docx"
    file_token = upload_file(token, safe_name, docx_bytes, folder_token)

    print("5/6  导入为飞书文档…")
    ticket = create_import_task(token, file_token, folder_token)
    doc_token, doc_url = poll_import(token, ticket)

    print("6/6  开放组织内访问权限…")
    share_with_org(token, doc_token)

    print()
    print("完成！")
    url = doc_url or f"https://feishu.cn/docx/{doc_token}"
    print(f"  文档链接: {url}")
    print("  组织内所有人均可通过链接查看。")


if __name__ == "__main__":
    main()
