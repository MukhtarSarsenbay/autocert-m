from __future__ import annotations

import argparse
import hashlib
import os
import posixpath
from io import BytesIO
from pathlib import Path
from tempfile import NamedTemporaryFile
from zipfile import ZIP_DEFLATED, ZipFile

from lxml import etree
from PIL import Image, ImageChops, ImageOps


BASE_DIR = Path(__file__).resolve().parents[1]
REF_DIR = BASE_DIR / "media" / "ref"
NCA_IMAGE = REF_DIR / "nca_kz_t_09_3244.png"
DIRECTOR_SIGNATURE_IMAGE = REF_DIR / "director_sign.png"
DIRECTOR_SIGNATURE_AND_STAMP_IMAGE = REF_DIR / "director_signature_and_stamp.png"
LAB_HEAD_SIGNATURE_IMAGE = REF_DIR / "lab_head_sign.png"
SPECIALIST_SIGNATURE_IMAGE = REF_DIR / "specialist_sign.png"
# Existing round company seal extracted from the user's reference journal.
STAMP_IMAGE = REF_DIR / "pechat.png"

DIRECTOR_FULL_NAME = "Мырзалиев М.Б."
DIRECTOR_FULL_NAME_GENITIVE = "Мырзалиева М.Б."
LAB_HEAD_FULL_NAME = "Озықбай Береке Сембекұлы"
SPECIALIST_FULL_NAME = "Женисов Бекзат Ерболатович"
STAFF_REPLACEMENTS = [
    ("Шәріп Ахмеди Құлбайұлы", LAB_HEAD_FULL_NAME),
    ("Тусипкалиев  Кулбай Шарипович", SPECIALIST_FULL_NAME),
    ("Тусипкалиев Кулбай Шарипович", SPECIALIST_FULL_NAME),
    ("Тусипкалиев К.Ш.", SPECIALIST_FULL_NAME),
]

# Roles were checked against the text and drawing relationships in each DOCX.
# The source journal's image1 is the specialist; image2 is the laboratory head.
STAFF_IMAGE_REPLACEMENTS = {
    "conclusion.docx": {"word/media/image1.png": "lab_head_signature"},
    "decision.docx": {"word/media/image2.png": "lab_head_signature"},
    "journal_С-00395.docx": {
        "word/media/image1.png": "specialist_signature",
        "word/media/image2.png": "lab_head_signature",
    },
    "logbook.docx": {
        "word/media/image1.png": "specialist_signature",
        "word/media/image2.png": "lab_head_signature",
    },
    "protocol_add_С-00395.docx": {
        "word/media/image3.png": "specialist_signature",
        "word/media/image4.png": "lab_head_signature",
    },
    "protocol_new.docx": {
        "word/media/image3.png": "specialist_signature",
        "word/media/image4.png": "lab_head_signature",
    },
    "protocol_b.docx": {
        "word/media/image2.png": "specialist_signature",
        "word/media/image3.png": "lab_head_signature",
    },
    "protocol_o.docx": {
        "word/media/image2.png": "specialist_signature",
        "word/media/image3.png": "lab_head_signature",
    },
    "tex_expert.docx": {
        "word/media/image2.png": "specialist_signature",
        "word/media/image3.png": "lab_head_signature",
    },
    "tex_expert_p.docx": {
        "word/media/image2.png": "specialist_signature",
        "word/media/image3.png": "lab_head_signature",
    },
}

OLD_NCA_SHA256_VALUES = {
    "bed789602755594baf14f049ef7d565b4003d72c1f0f00c8ba69851405cda29a",
    "026fe8fac90aae0740714129d7a67a2deeb96c836f6b6afd57abb202060bee30",
    "1119e1313dc0d5b7e659f9b4f8a81b97e8d372d50f4e5a87b1b874c3600aa882",
}

LEGAL_ADDRESS = (
    "Республика Казахстан, Западно-Казахстанская область, г. Уральск, "
    "ул. Самал, дом 94/1, кв. 133"
)
PHYSICAL_ADDRESS = (
    "Республика Казахстан, Западно-Казахстанская область, г. Уральск, "
    "ул. Академика Асана Тайманова, здание 221В"
)
ADDRESS_REPLACEMENTS = [
    ("Атырауская область, город Атырау, микрорайон Атырау, 89а.", LEGAL_ADDRESS),
    ("Атырауская область, город Атырау, микрорайон Атырау, 89А.", LEGAL_ADDRESS),
    ("Атырауская область, город Атырау, микрорайон Атырау, 89б.", PHYSICAL_ADDRESS),
    ("Атырауская область, город Атырау, микрорайон Атырау, 89Б.", PHYSICAL_ADDRESS),
]
NEW_ATTESTATION = "№ KZ.T.09.3244 от «8» октября 2026 года"
NEW_ATTESTATION_DATES = "от «8» октября 2026 года"
KAZAKH_ATTESTATION = "№ KZ.T.09.3244, 2026 ж. «8» қазаннан бастап"
# Approved examples: Протокол_новый_D-00003.pdf and ТехСпец_D-00003.pdf.
# They contain only the issue date, without the old expiry date / ISO line.
ACCREDITATION_REPLACEMENTS = [
    (
        "№ KZ.T.06.3077"
        "2026 ж. «4» мамырдан бастап"
        "2031 ж. «4» мамырға дейін жарамды"
        "ГОСТ ISO/ІЕС 17025-2019",
        KAZAKH_ATTESTATION,
    ),
    (
        "от «4» мая 2026 года"
        "действителен до «4» мая 2031 года."
        "ГОСТ ISO/ІЕС 17025-2019",
        NEW_ATTESTATION_DATES,
    ),
]

# Long, context-specific replacements must run before the short fallbacks.
REPLACEMENTS = [
    ("Сайдхакимов Бахтияр Абдухамидович", DIRECTOR_FULL_NAME),
    ("Сайдхакимова Бахтияра Абдухамидовича", DIRECTOR_FULL_NAME_GENITIVE),
    ("Садуахасов Алихан Бахитович", DIRECTOR_FULL_NAME),
    ("Садуахасов А.Б .", DIRECTOR_FULL_NAME),
    ("Садуахасов А.Б.", DIRECTOR_FULL_NAME),
    ("Садуахасов А .Б.", DIRECTOR_FULL_NAME),
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
    ("Көлік сынақ зертханасы", "Автосерт-М"),
    ('«"Автосерт-М"»', "«Автосерт-М»"),
    ("KZ.T.06.3077", "KZ.T.09.3244"),
    ("KZ.T.16.Е1185", "KZ.T.09.3244"),
    ("KZ.T.16.E1185", "KZ.T.09.3244"),
    ("от «15» июля 2022 г.", NEW_ATTESTATION_DATES),
    ("от «15» июля 2022 г", NEW_ATTESTATION_DATES),
    ("города Шымкент", "города Атырау"),
    ("г. Шымкент", "г. Атырау"),
]

DOCUMENT_REPLACEMENTS = {
    "act_contract_qaz.docx": [
        (
            "в лице директора действующий",
            f"в лице директора {DIRECTOR_FULL_NAME_GENITIVE}, действующего",
        ),
    ],
    # This address is an unlabeled requisites line in the customer contract.
    "contract.docx": [
        (
            "в лице директора Досмайлова Н.А., действующей",
            f"в лице директора {DIRECTOR_FULL_NAME_GENITIVE}, действующего",
        ),
        ("Директор: Досмайлов Н.А.", f"Директор: {DIRECTOR_FULL_NAME}"),
        (PHYSICAL_ADDRESS, LEGAL_ADDRESS),
    ],
    "protocol_add_С-00395.docx": [
        ("Николаевич Валерий", LAB_HEAD_FULL_NAME),
    ],
    "protocol_new.docx": [
        ("{{ClastName}} {{CfirstName}}", LAB_HEAD_FULL_NAME),
    ],
}

# Company director and stamp assets. Laboratory staff are handled separately
# above; customer signature placeholders must remain dynamic.
DOCUMENT_IMAGE_REPLACEMENTS = {
    "act.docx": {
        "word/media/image1.png": "stamp",
        "word/media/image2.png": "director_signature",
    },
    "act_contract.docx": {
        "word/media/image1.png": "director_signature",
        "word/media/image2.png": "stamp",
    },
    "act_contract_qaz.docx": {
        "word/media/image1.png": "director_signature_and_stamp",
    },
    "act_qaz.docx": {
        "word/media/image1.png": "stamp",
        "word/media/image2.png": "director_signature",
    },
    "contract.docx": {
        "word/media/image1.png": "director_signature_and_stamp",
    },
    "decision.docx": {
        "word/media/image3.png": "stamp",
    },
    "journal_С-00395.docx": {
        "word/media/image3.png": "stamp",
    },
    "logbook.docx": {
        "word/media/image3.png": "stamp",
    },
    "protocol_b.docx": {
        "word/media/image4.png": "stamp",
    },
    "protocol_new.docx": {
        "word/media/image5.png": "stamp",
    },
    "protocol_o.docx": {
        "word/media/image4.png": "stamp",
    },
    "tex_expert.docx": {
        "word/media/image4.png": "stamp",
    },
    "tex_expert_p.docx": {
        "word/media/image4.png": "stamp",
    },
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


def _replace_addresses(root, counts, document_name):
    changed = False
    for paragraph in root.iter():
        if paragraph.tag not in PARAGRAPH_TAGS:
            continue
        changed = _replace_in_container(paragraph, counts, ADDRESS_REPLACEMENTS) or changed
        # The customer contract puts this label in the preceding table row.
        # The complete address now includes the country itself.
        text = "".join(node.text or "" for node in _text_nodes(paragraph))
        if document_name == "contract.docx" and text.strip() == "Юр.адрес: Республика Казахстан,":
            changed = _replace_in_container(
                paragraph,
                counts,
                [("Юр.адрес: Республика Казахстан,", "Юр.адрес:")],
            ) or changed
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


def _format_decision_director_name(root, document_name):
    if document_name != "decision.docx":
        return False

    for paragraph in root.iter(W_P):
        nodes = _text_nodes(paragraph)
        paragraph_text = "".join(node.text or "" for node in nodes)
        if "ТОО «Автосерт-М»" not in paragraph_text:
            continue
        for node in nodes:
            if node.text != DIRECTOR_FULL_NAME:
                continue
            run = node.getparent()
            if run is None or run.tag != W_R:
                continue
            previous_element = node.getprevious()
            if previous_element is not None and previous_element.tag == W_BR:
                return False
            node.addprevious(etree.Element(W_BR))
            return True
    return False


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
    changed = _replace_addresses(root, counts, document_name)
    changed = _replace_legal_address_table_rows(root, counts) or changed
    replacements = DOCUMENT_REPLACEMENTS.get(document_name, []) + REPLACEMENTS
    for paragraph in root.iter():
        if paragraph.tag in PARAGRAPH_TAGS:
            if _replace_in_container(paragraph, counts, ACCREDITATION_REPLACEMENTS):
                # The superseded date, expiry and ISO block used manual breaks.
                # Remove those breaks as well as the text to match the examples.
                for line_break in list(paragraph.iter(W_BR)):
                    line_break.getparent().remove(line_break)
                changed = True
            changed = _replace_in_container(paragraph, counts, replacements) or changed
    changed = _replace_kazakh_accreditation_cell(root, counts) or changed
    changed = _format_decision_director_name(root, document_name) or changed
    changed = _format_protocol_accreditation(root, document_name) or changed
    if not changed:
        return data, False
    _convert_newlines_to_word_breaks(root)
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True), True


def _format_protocol_accreditation(root, document_name):
    if document_name not in {"protocol_new.docx", "protocol_add_С-00395.docx"}:
        return False
    heading = attestation = None
    for paragraph in root.iter(W_P):
        text = "".join(node.text or "" for node in _text_nodes(paragraph))
        if text.strip() == "Испытательная лаборатория ТОО «Автосерт-М»":
            heading = paragraph
        elif "Аттестат аккредитации " + NEW_ATTESTATION in text:
            attestation = paragraph
    if heading is None or attestation is None:
        return False
    cell = heading.getparent()
    if cell.tag != W_TC or attestation.getparent() is cell:
        return False
    # Match the supplied protocol: attestation below the laboratory name,
    # with the legal and physical addresses in the next table row.
    heading.addnext(attestation)
    for properties in attestation.iter(f"{{{W_NS}}}rPr"):
        for name in ("b", "bCs"):
            flag = properties.find(f"{{{W_NS}}}{name}")
            if flag is None:
                flag = etree.SubElement(properties, f"{{{W_NS}}}{name}")
            flag.set(f"{{{W_NS}}}val", "0")
    return True


def _crop_white_margins(image):
    rgb_image = image.convert("RGB")
    white_background = Image.new("RGB", rgb_image.size, "white")
    difference = ImageChops.difference(rgb_image, white_background).convert("L")
    visible_pixels = difference.point(lambda value: 255 if value > 12 else 0)
    bounding_box = visible_pixels.getbbox()
    return rgb_image.crop(bounding_box) if bounding_box else rgb_image


def _save_image(image, image_format):
    output = BytesIO()
    if image_format in {"JPEG", "JPG"}:
        image.convert("RGB").save(output, format="JPEG", quality=95)
    else:
        image.save(output, format="PNG")
    return output.getvalue()


def _fit_asset_to_embedded_image(asset, embedded_image):
    with Image.open(BytesIO(embedded_image)) as target:
        target_size = target.size
        target_format = target.format or "PNG"
    with Image.open(BytesIO(asset)) as source:
        cropped_source = _crop_white_margins(source)

    padding = max(2, round(min(target_size) * 0.04))
    available_size = (
        max(1, target_size[0] - padding * 2),
        max(1, target_size[1] - padding * 2),
    )
    fitted_source = ImageOps.contain(
        cropped_source,
        available_size,
        method=Image.Resampling.LANCZOS,
    )
    canvas = Image.new("RGB", target_size, "white")
    position = (
        (target_size[0] - fitted_source.width) // 2,
        (target_size[1] - fitted_source.height) // 2,
    )
    canvas.paste(fitted_source, position)
    return _save_image(canvas, target_format)


def _compose_director_signature_and_stamp(signature, stamp, embedded_image):
    with Image.open(BytesIO(embedded_image)) as target:
        target_size = target.size
        target_format = target.format or "PNG"
    with Image.open(BytesIO(signature)) as signature_image:
        cropped_signature = _crop_white_margins(signature_image)
    with Image.open(BytesIO(stamp)) as stamp_image:
        cropped_stamp = _crop_white_margins(stamp_image)

    canvas = Image.new("RGB", target_size, "white")
    outer_padding = max(3, round(min(target_size) * 0.03))
    gap = outer_padding
    available_width = target_size[0] - outer_padding * 2 - gap
    signature_width = round(available_width * 0.42)
    stamp_width = available_width - signature_width
    available_height = target_size[1] - outer_padding * 2

    fitted_signature = ImageOps.contain(
        cropped_signature,
        (signature_width, available_height),
        method=Image.Resampling.LANCZOS,
    )
    fitted_stamp = ImageOps.contain(
        cropped_stamp,
        (stamp_width, available_height),
        method=Image.Resampling.LANCZOS,
    )
    signature_position = (
        outer_padding + (signature_width - fitted_signature.width) // 2,
        (target_size[1] - fitted_signature.height) // 2,
    )
    stamp_area_left = outer_padding + signature_width + gap
    stamp_position = (
        stamp_area_left + (stamp_width - fitted_stamp.width) // 2,
        (target_size[1] - fitted_stamp.height) // 2,
    )
    canvas.paste(fitted_signature, signature_position)
    canvas.paste(fitted_stamp, stamp_position)
    return _save_image(canvas, target_format)


def _replace_document_image(document_name, entry_name, embedded_image, assets):
    staff_role = STAFF_IMAGE_REPLACEMENTS.get(document_name, {}).get(entry_name)
    if staff_role:
        # Keep the cleaned asset intact; its proportions are set in DrawingML.
        return assets[staff_role]
    replacement_role = DOCUMENT_IMAGE_REPLACEMENTS.get(document_name, {}).get(entry_name)
    if replacement_role == "director_signature":
        return _fit_asset_to_embedded_image(assets["director_signature"], embedded_image)
    if replacement_role == "stamp":
        return assets["stamp"]
    if replacement_role == "director_signature_and_stamp":
        # Keep the user-provided director signature and round seal together.
        return assets["director_signature_and_stamp"]
    return embedded_image


def _update_staff_xml(data, counts, document_name, relationships, assets):
    root = etree.fromstring(data, etree.XMLParser(resolve_entities=False))
    changed = False
    for paragraph in root.iter():
        if paragraph.tag in PARAGRAPH_TAGS:
            changed = _replace_in_container(paragraph, counts, STAFF_REPLACEMENTS) or changed

    ns = {
        "w": W_NS,
        "a": A_NS,
        "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
        "wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
        "pic": "http://schemas.openxmlformats.org/drawingml/2006/picture",
    }
    roles = STAFF_IMAGE_REPLACEMENTS.get(document_name, {})
    for drawing in root.findall(".//w:drawing", ns):
        blip = drawing.find(".//a:blip", ns)
        if blip is None:
            continue
        image_name = relationships.get(blip.get(f"{{{ns['r']}}}embed"))
        role = roles.get(image_name)
        if not role:
            continue
        extent = drawing.find(".//wp:extent", ns)
        picture_extent = drawing.find(".//pic:spPr/a:xfrm/a:ext", ns)
        if extent is None or picture_extent is None:
            raise ValueError(f"Missing signature drawing dimensions: {document_name}, {image_name}")
        with Image.open(BytesIO(assets[role])) as signature:
            width, height = signature.size
        cx, cy = int(extent.get("cx")), int(extent.get("cy"))
        # Compact signature rows have captions immediately below the handwriting.
        # A 1 cm image height keeps the white image box clear of those captions.
        max_height = cy if document_name in {"conclusion.docx", "decision.docx"} else 360000
        # Fit inside the existing signature area, without enlarging or stretching.
        # A one-EMU rounding tolerance makes subsequent runs stable.
        if cy > max_height or abs(cx * height - cy * width) > max(width, height):
            scale = min(cx / width, cy / height, max_height / height)
            new_cx, new_cy = round(width * scale), round(height * scale)
            horizontal_offset = drawing.find(".//wp:positionH/wp:posOffset", ns)
            if horizontal_offset is not None:
                horizontal_offset.text = str(int(horizontal_offset.text) + (cx - new_cx) // 2)
            for element in (extent, picture_extent):
                element.set("cx", str(new_cx))
                element.set("cy", str(new_cy))
            changed = True
        # Cropping values from the previous photograph must not clip the new ink.
        for crop in drawing.findall(".//a:srcRect", ns):
            crop.getparent().remove(crop)
            changed = True
    if not changed:
        return data, False
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True), True


def _update_document(document, assets, staff_only=False):
    counts = {}
    image_replacements = 0
    changed_parts = 0
    original_mode = document.stat().st_mode

    with ZipFile(document, "r") as source:
        archive_comment = source.comment
        entries = [(info, source.read(info.filename)) for info in source.infolist()]
    contents = {info.filename: data for info, data in entries}

    updated_entries = []
    for info, data in entries:
        updated_data = data
        if info.filename.startswith("word/") and info.filename.endswith(".xml"):
            changed = False
            if not staff_only:
                updated_data, changed = _update_xml(updated_data, counts, document.name)
            directory, filename = posixpath.split(info.filename)
            relations_data = contents.get(f"{directory}/_rels/{filename}.rels")
            relationships = {}
            if relations_data:
                for relation in etree.fromstring(relations_data):
                    if relation.get("TargetMode") != "External":
                        relationships[relation.get("Id")] = posixpath.normpath(
                            posixpath.join(directory, relation.get("Target"))
                        )
            updated_data, staff_changed = _update_staff_xml(
                updated_data, counts, document.name, relationships, assets
            )
            changed = changed or staff_changed
            changed_parts += int(changed)
        elif info.filename.startswith("word/media/"):
            staff_role = STAFF_IMAGE_REPLACEMENTS.get(document.name, {}).get(info.filename)
            if not staff_only or staff_role:
                updated_data = _replace_document_image(
                    document.name,
                    info.filename,
                    data,
                    assets,
                )
            if updated_data != data:
                image_replacements += 1
            elif not staff_only and hashlib.sha256(data).hexdigest() in OLD_NCA_SHA256_VALUES:
                updated_data = assets["nca"]
                image_replacements += 1
        updated_entries.append((info, updated_data))

    if not counts and not image_replacements and not changed_parts:
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
    parser = argparse.ArgumentParser(description="Update reference document templates.")
    parser.add_argument(
        "--staff-only",
        action="store_true",
        help="Update laboratory head and specialist names/signatures only.",
    )
    args = parser.parse_args()
    required_images = {
        "lab_head_signature": LAB_HEAD_SIGNATURE_IMAGE,
        "specialist_signature": SPECIALIST_SIGNATURE_IMAGE,
    }
    if not args.staff_only:
        required_images.update({
            "nca": NCA_IMAGE,
            "director_signature": DIRECTOR_SIGNATURE_IMAGE,
            "director_signature_and_stamp": DIRECTOR_SIGNATURE_AND_STAMP_IMAGE,
            "stamp": STAMP_IMAGE,
        })
    missing_images = [path for path in required_images.values() if not path.is_file()]
    if missing_images:
        raise FileNotFoundError(", ".join(str(path) for path in missing_images))
    assets = {name: path.read_bytes() for name, path in required_images.items()}

    updated = {}
    for document in sorted(REF_DIR.glob("*.docx")):
        result = _update_document(document, assets, staff_only=args.staff_only)
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
