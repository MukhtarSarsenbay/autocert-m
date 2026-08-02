from __future__ import annotations

import hashlib
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from zipfile import ZIP_DEFLATED, ZipFile

from lxml import etree


BASE_DIR = Path(__file__).resolve().parents[1]
REF_DIR = BASE_DIR / "media" / "ref"
NCA_IMAGE = REF_DIR / "nca_kz_t_06_3077.png"

OLD_NCA_SHA256_VALUES = {
    "026fe8fac90aae0740714129d7a67a2deeb96c836f6b6afd57abb202060bee30",
    "1119e1313dc0d5b7e659f9b4f8a81b97e8d372d50f4e5a87b1b874c3600aa882",
}

LEGAL_ADDRESS = "Атырауская область, город Атырау, микрорайон Атырау, 89а."
PHYSICAL_ADDRESS = "Атырауская область, город Атырау, микрорайон Атырау, 89б."
NEW_ATTESTATION = (
    "№ KZ.T.06.3077\n"
    "от «4» мая 2026 года\n"
    "действителен до «4» мая 2031 года.\n"
    "ГОСТ ISO/ІЕС 17025-2019"
)
NEW_ATTESTATION_DATES = (
    "от «4» мая 2026 года\n"
    "действителен до «4» мая 2031 года.\n"
    "ГОСТ ISO/ІЕС 17025-2019"
)
KAZAKH_ATTESTATION = (
    "№ KZ.T.06.3077\n"
    "2026 ж. «4» мамырдан бастап\n"
    "2031 ж. «4» мамырға дейін жарамды\n"
    "ГОСТ ISO/ІЕС 17025-2019"
)

# Long, context-specific replacements must run before the short fallbacks.
REPLACEMENTS = [
    (
        f"Юридический адрес: {PHYSICAL_ADDRESS}",
        f"Юридический адрес: {LEGAL_ADDRESS}",
    ),
    (f"Юр.адрес: {PHYSICAL_ADDRESS}", f"Юр.адрес: {LEGAL_ADDRESS}"),
    (f"Юр. адрес: {PHYSICAL_ADDRESS}", f"Юр. адрес: {LEGAL_ADDRESS}"),
    (
        "№ KZ.T.16.Е1185 аккредитация аттестаты 2022 ж. «15» шілдеден",
        KAZAKH_ATTESTATION,
    ),
    ("№ KZ.T.16.Е1185 до 15.07.2027 г.", NEW_ATTESTATION),
    (
        "РК, Туркестанская область, РК, г. г. Шымкент, Каратауский район, "
        "Квартал 216, уч. 312",
        PHYSICAL_ADDRESS,
    ),
    (
        "РК, Туркестанская область, г.Шымкент, Каратауский район, "
        "Квартал 216, уч.312",
        PHYSICAL_ADDRESS,
    ),
    (
        "РК, Туркестанская область, г.Шымкент, мкр. Самал-1, "
        "ул.Рыскулова зд.1048Б",
        PHYSICAL_ADDRESS,
    ),
    (
        "Республика Казахстан, Шымкент, мкр Самал 1, Т.Рыскулова, зд.1048 Б",
        PHYSICAL_ADDRESS,
    ),
    (
        "РК, г. г. Шымкент, Каратауский район, Квартал 216, уч. 312",
        PHYSICAL_ADDRESS,
    ),
    (
        "РК, г. Шымкент, Каратауский район, Квартал 216, уч. 312",
        PHYSICAL_ADDRESS,
    ),
    ("РК, г. Шымкент, ул. Рыскулова 1048Б", PHYSICAL_ADDRESS),
    ("город Шымкент, ул. Рыскулова 1048Б", PHYSICAL_ADDRESS),
    ("Көлік сынақ зертханасы", "Kaspisert"),
    ("KaspiNet", "Kaspisert"),
    ('«"Kaspisert"»', "«Kaspisert»"),
    ("KZ.T.16.Е1185", "KZ.T.06.3077"),
    ("KZ.T.16.E1185", "KZ.T.06.3077"),
    ("от «15» июля 2022 г.", NEW_ATTESTATION_DATES),
    ("от «15» июля 2022 г", NEW_ATTESTATION_DATES),
    ("города Шымкент", "города Атырау"),
    ("г. Шымкент", "г. Атырау"),
]

DOCUMENT_REPLACEMENTS = {
    # This address is an unlabeled requisites line in the customer contract.
    "contract.docx": [(PHYSICAL_ADDRESS, LEGAL_ADDRESS)],
}

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
XML_NS = "http://www.w3.org/XML/1998/namespace"
W_P = f"{{{W_NS}}}p"
W_R = f"{{{W_NS}}}r"
W_T = f"{{{W_NS}}}t"
W_BR = f"{{{W_NS}}}br"
W_TR = f"{{{W_NS}}}tr"
W_TC = f"{{{W_NS}}}tc"
A_P = f"{{{A_NS}}}p"
A_T = f"{{{A_NS}}}t"
TEXT_TAGS = {W_T, A_T}
PARAGRAPH_TAGS = {W_P, A_P}


def _text_nodes(paragraph):
    return [element for element in paragraph.iter() if element.tag in TEXT_TAGS]


def _find_start(nodes, position):
    cursor = 0
    for index, node in enumerate(nodes):
        length = len(node.text or "")
        if position < cursor + length:
            return index, position - cursor
        cursor += length
    raise ValueError(f"Start position {position} is outside paragraph text")


def _find_end(nodes, position):
    cursor = 0
    for index, node in enumerate(nodes):
        length = len(node.text or "")
        if position <= cursor + length:
            return index, position - cursor
        cursor += length
    raise ValueError(f"End position {position} is outside paragraph text")


def _replace_match(nodes, start, end, replacement):
    start_index, start_offset = _find_start(nodes, start)
    end_index, end_offset = _find_end(nodes, end)
    start_node = nodes[start_index]
    end_node = nodes[end_index]

    if start_index == end_index:
        text = start_node.text or ""
        start_node.text = text[:start_offset] + replacement + text[end_offset:]
        return

    start_node.text = (start_node.text or "")[:start_offset] + replacement
    for node in nodes[start_index + 1 : end_index]:
        node.text = ""
    end_node.text = (end_node.text or "")[end_offset:]


def _replace_in_container(container, counts, replacements):
    changed = False
    for old, new in replacements:
        while True:
            nodes = _text_nodes(container)
            full_text = "".join(node.text or "" for node in nodes)
            start = full_text.find(old)
            if start < 0:
                break
            _replace_match(nodes, start, start + len(old), new)
            counts[old] = counts.get(old, 0) + 1
            changed = True
    return changed


def _replace_legal_address_table_rows(root, counts):
    changed = False
    replacement = [(PHYSICAL_ADDRESS, LEGAL_ADDRESS)]
    for row in root.iter(W_TR):
        row_text = "".join(node.text or "" for node in _text_nodes(row))
        if "Юридический адрес" in row_text and PHYSICAL_ADDRESS in row_text:
            changed = _replace_in_container(row, counts, replacement) or changed
    return changed


def _replace_kazakh_accreditation_cell(root, counts):
    changed = False
    current_block = NEW_ATTESTATION.replace("\n", "")
    replacement = [(current_block, KAZAKH_ATTESTATION)]
    for cell in root.iter(W_TC):
        cell_text = "".join(node.text or "" for node in _text_nodes(cell))
        if "Мемлекеттік техникалық реттеу жүйесі" not in cell_text:
            continue
        for paragraph in cell.iter(W_P):
            changed = _replace_in_container(paragraph, counts, replacement) or changed
    return changed


def _set_space_preserve(text_node):
    text = text_node.text or ""
    if text[:1].isspace() or text[-1:].isspace():
        text_node.set(f"{{{XML_NS}}}space", "preserve")
    else:
        text_node.attrib.pop(f"{{{XML_NS}}}space", None)


def _convert_newlines_to_word_breaks(root):
    for text_node in list(root.iter(W_T)):
        text = text_node.text or ""
        if "\n" not in text:
            _set_space_preserve(text_node)
            continue

        run = text_node.getparent()
        if run is None or run.tag != W_R:
            raise ValueError("Cannot insert a Word line break outside a text run")

        parts = text.split("\n")
        text_node.text = parts[0]
        _set_space_preserve(text_node)
        insertion_point = text_node
        for part in parts[1:]:
            line_break = etree.Element(W_BR)
            new_text = etree.Element(W_T)
            new_text.text = part
            _set_space_preserve(new_text)
            insertion_point.addnext(line_break)
            line_break.addnext(new_text)
            insertion_point = new_text

    drawing_text_with_newlines = [
        node for node in root.iter(A_T) if "\n" in (node.text or "")
    ]
    if drawing_text_with_newlines:
        raise ValueError("A replacement requiring line breaks landed in DrawingML text")


def _update_xml(data, counts, document_name):
    parser = etree.XMLParser(remove_blank_text=False, resolve_entities=False)
    root = etree.fromstring(data, parser)
    changed = _replace_legal_address_table_rows(root, counts)
    replacements = DOCUMENT_REPLACEMENTS.get(document_name, []) + REPLACEMENTS
    for paragraph in root.iter():
        if paragraph.tag in PARAGRAPH_TAGS:
            changed = _replace_in_container(paragraph, counts, replacements) or changed
    changed = _replace_kazakh_accreditation_cell(root, counts) or changed
    if not changed:
        return data, False
    _convert_newlines_to_word_breaks(root)
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True), True


def _update_document(document, replacement_image):
    counts = {}
    image_replacements = 0
    changed_parts = 0
    original_mode = document.stat().st_mode

    with ZipFile(document, "r") as source:
        archive_comment = source.comment
        entries = [(info, source.read(info.filename)) for info in source.infolist()]

    updated_entries = []
    for info, data in entries:
        updated_data = data
        if info.filename.startswith("word/") and info.filename.endswith(".xml"):
            updated_data, changed = _update_xml(data, counts, document.name)
            changed_parts += int(changed)
        elif info.filename.startswith("word/media/"):
            if hashlib.sha256(data).hexdigest() in OLD_NCA_SHA256_VALUES:
                updated_data = replacement_image
                image_replacements += 1
        updated_entries.append((info, updated_data))

    if not counts and not image_replacements:
        return None

    with NamedTemporaryFile(
        dir=document.parent,
        prefix=f".{document.name}.",
        suffix=".tmp",
        delete=False,
    ) as temporary_file:
        temporary_path = Path(temporary_file.name)

    try:
        with ZipFile(temporary_path, "w", compression=ZIP_DEFLATED) as destination:
            destination.comment = archive_comment
            for info, data in updated_entries:
                destination.writestr(info, data)

        with ZipFile(temporary_path, "r") as verification:
            invalid_member = verification.testzip()
            if invalid_member:
                raise ValueError(f"Invalid DOCX member after update: {invalid_member}")

        os.chmod(temporary_path, original_mode)
        temporary_path.replace(document)
    finally:
        temporary_path.unlink(missing_ok=True)

    return {
        "text_replacements": sum(counts.values()),
        "image_replacements": image_replacements,
        "xml_parts": changed_parts,
    }


def main():
    if not NCA_IMAGE.is_file():
        raise FileNotFoundError(NCA_IMAGE)
    replacement_image = NCA_IMAGE.read_bytes()

    updated = {}
    for document in sorted(REF_DIR.glob("*.docx")):
        result = _update_document(document, replacement_image)
        if result:
            updated[document.name] = result

    print(f"Updated {len(updated)} DOCX templates")
    for name, result in updated.items():
        print(
            f"{name}: text={result['text_replacements']}, "
            f"images={result['image_replacements']}, xml_parts={result['xml_parts']}"
        )


if __name__ == "__main__":
    main()
