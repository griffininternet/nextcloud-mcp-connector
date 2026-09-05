"""Safe, read-only text extraction from OOXML Word documents."""

from io import BytesIO
from pathlib import PurePosixPath
from typing import Any
from zipfile import BadZipFile, ZipFile

from lxml import etree

from ..errors import ToolError
from ..nextcloud import NcClients
from ..nextcloud.clients import dav

DOCX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
MAX_SOURCE_BYTES = 10 * 1024 * 1024
MAX_ARCHIVE_ENTRIES = 1_000
MAX_UNCOMPRESSED_BYTES = 50 * 1024 * 1024
MAX_PART_BYTES = 20 * 1024 * 1024
DEFAULT_MAX_BYTES = 512 * 1024
HARD_MAX_BYTES = 2 * 1024 * 1024

_WORD_DOCUMENT = "word/document.xml"
_W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
_TAG_P = f"{{{_W}}}p"
_TAG_TBL = f"{{{_W}}}tbl"
_TAG_TR = f"{{{_W}}}tr"
_TAG_TC = f"{{{_W}}}tc"
_TAG_TEXT = f"{{{_W}}}t"
_TAG_TAB = f"{{{_W}}}tab"
_TAG_BREAK = f"{{{_W}}}br"
_TAG_CARRIAGE_RETURN = f"{{{_W}}}cr"


async def extract(
    clients: NcClients,
    path: str,
    offset: int = 0,
    max_bytes: int = DEFAULT_MAX_BYTES,
) -> dict[str, Any]:
    """Download one small DOCX and return a byte-paged UTF-8 text projection."""
    if offset < 0:
        raise ToolError(
            message=f"offset must not be negative (got {offset}).",
            hint="Start at offset 0 and follow next_offset until truncated is false.",
        )
    if max_bytes < 1 or max_bytes > HARD_MAX_BYTES:
        raise ToolError(
            message=f"max_bytes must be between 1 and {HARD_MAX_BYTES} bytes.",
            hint="Use the registered tool's fixed page size and follow next_offset.",
        )

    target = dav.safe_path(path)
    info = await dav.stat(clients.client, clients.creds, target)
    if info["is_collection"]:
        raise ToolError(
            message=f"{target} is a folder, not a file.",
            hint="Give the full path of a .docx file.",
        )

    content_type = (info["content_type"] or "").split(";", 1)[0].strip().lower()
    if PurePosixPath(target).suffix.lower() != ".docx" or content_type != DOCX_CONTENT_TYPE:
        raise ToolError(
            message=f"{target} is not a supported Word document.",
            hint=f"Use a .docx file reported as {DOCX_CONTENT_TYPE}.",
        )

    source_size = info["size"]
    if source_size > MAX_SOURCE_BYTES:
        raise ToolError(
            message=f"{target} is too large to extract safely ({source_size} bytes).",
            hint=f"Use a Word document no larger than {MAX_SOURCE_BYTES} bytes.",
        )

    data = await dav.get_range(clients.client, clients.creds, target)
    text = extract_docx(data, target)
    encoded = text.encode("utf-8")
    extracted_size = len(encoded)

    if not extracted_size:
        raise ToolError(
            message=f"{target} contains no readable document text.",
            hint=(
                "Open it in Nextcloud to check whether it contains only images or embedded objects."
            ),
        )
    if offset >= extracted_size:
        raise ToolError(
            message=(
                f"offset {offset} is at or past the end of the extracted text "
                f"({extracted_size} bytes)."
            ),
            hint="Read from a smaller offset, or stop: the document has no more extracted text.",
        )

    content, used = _utf8_slice(encoded, offset, max_bytes)
    result: dict[str, Any] = {
        "path": target,
        "content": content,
        "source_size": source_size,
        "extracted_size": extracted_size,
        "content_type": content_type,
        "format": "docx",
        "truncated": offset + used < extracted_size,
    }
    if result["truncated"]:
        result["next_offset"] = offset + used
    return result


def extract_docx(data: bytes, path: str = "document.docx") -> str:
    """Extract paragraphs and tables in document order without processing active content."""
    try:
        with ZipFile(BytesIO(data)) as archive:
            members = archive.infolist()
            if len(members) > MAX_ARCHIVE_ENTRIES:
                raise ToolError(
                    message=f"{path} contains too many archive entries.",
                    hint="Use a normal, unencrypted .docx document.",
                )
            total = sum(member.file_size for member in members)
            if total > MAX_UNCOMPRESSED_BYTES:
                raise ToolError(
                    message=f"{path} expands beyond the safe extraction limit.",
                    hint="Use a smaller .docx document without large embedded objects.",
                )
            try:
                part = archive.getinfo(_WORD_DOCUMENT)
            except KeyError:
                raise ToolError(
                    message=f"{path} has no Word document body.",
                    hint="Use a valid, unencrypted .docx document.",
                ) from None
            if part.file_size > MAX_PART_BYTES:
                raise ToolError(
                    message=f"{path} has a document body above the safe extraction limit.",
                    hint="Use a smaller .docx document.",
                )
            xml = archive.read(part)
    except BadZipFile:
        raise ToolError(
            message=f"{path} is not a valid .docx archive.",
            hint="Open and resave it as a modern Word document, then try again.",
        ) from None

    try:
        parser = etree.XMLParser(
            resolve_entities=False,
            no_network=True,
            recover=False,
            huge_tree=False,
            remove_comments=True,
        )
        root = etree.fromstring(xml, parser=parser)
    except etree.XMLSyntaxError:
        raise ToolError(
            message=f"{path} contains malformed Word XML.",
            hint="Open and resave the document in Word or LibreOffice, then try again.",
        ) from None

    body = root.find(f".//{{{_W}}}body")
    if body is None:
        return ""

    blocks: list[str] = []
    for child in body:
        if child.tag == _TAG_P:
            line = _paragraph_text(child)
            if line:
                blocks.append(line)
        elif child.tag == _TAG_TBL:
            blocks.extend(_table_lines(child))
    return "\n".join(blocks).strip()


def _paragraph_text(paragraph: etree._Element) -> str:
    pieces: list[str] = []
    for node in paragraph.iter():
        if node.tag == _TAG_TEXT and node.text:
            pieces.append(node.text)
        elif node.tag == _TAG_TAB:
            pieces.append("\t")
        elif node.tag in {_TAG_BREAK, _TAG_CARRIAGE_RETURN}:
            pieces.append("\n")
    return "".join(pieces).strip()


def _table_lines(table: etree._Element) -> list[str]:
    lines: list[str] = []
    for row in table.iterchildren(tag=_TAG_TR):
        cells: list[str] = []
        for cell in row.iterchildren(tag=_TAG_TC):
            paragraphs = [
                text for paragraph in cell.iter(tag=_TAG_P) if (text := _paragraph_text(paragraph))
            ]
            cells.append(" ".join(paragraphs))
        if any(cells):
            lines.append("\t".join(cells))
    return lines


def _utf8_slice(data: bytes, offset: int, limit: int) -> tuple[str, int]:
    """Return a valid UTF-8 window and the exact number of bytes consumed."""
    window = data[offset : offset + limit]
    while window:
        try:
            return window.decode("utf-8"), len(window)
        except UnicodeDecodeError as exc:
            if exc.start >= len(window) - 3:
                window = window[: exc.start]
                continue
            raise ToolError(
                message="The extracted document text could not be paged as UTF-8.",
                hint="Start again from offset 0.",
            ) from None
    return "", 0
