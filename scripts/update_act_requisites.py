"""Update only the supplier sections and director signature in act templates."""
from copy import deepcopy
from pathlib import Path
from zipfile import ZipFile
from lxml import etree
from PIL import Image

from update_ref_documents import _replace_in_container, W_NS, W_P, W_R, W_T

REF = Path(__file__).resolve().parents[1] / 'media/ref'
NS = {'w': W_NS, 'wp': 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing',
      'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
      'pic': 'http://schemas.openxmlformats.org/drawingml/2006/picture',
      'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
SIGNATURES = {'act.docx': 'word/media/image2.png', 'act_qaz.docx': 'word/media/image2.png'}
LINES = [
    'БИН {{vendor_uid}}',
    'Юридический адрес: {{vendor_address}}',
    'Почтовый индекс: {{vendor_postcode}}',
    'Фактический адрес: {{vendor_physical_address}}',
    'Тел.: {{vendor_phone}}', 'e-mail: {{vendor_email}}',
    'ИИК {{vendor_iik}}', 'БИК {{vendor_bik}}', '{{vendor_bank}}, КБе {{vendor_kbe}}',
]


def text(element):
    return ''.join(element.xpath('.//w:t/text()', namespaces=NS))


def size_drawing(drawing, width, height):
    for extent in drawing.xpath('.//wp:extent | .//pic:spPr/a:xfrm/a:ext', namespaces=NS):
        extent.set('cx', str(width)); extent.set('cy', str(height))
    for crop in drawing.findall('.//a:srcRect', NS):
        crop.getparent().remove(crop)


def combine_executor(root, relations, entries):
    image_name = 'word/media/act_executor_medeu.png'
    rid = 'rIdActExecutionBlock'
    block = (REF / 'act_executor_medeu.png').read_bytes()
    if image_name in entries:
        entries[image_name] = (entries[image_name][0], block)
        with Image.open(REF / 'act_executor_medeu.png') as im:
            for drawing in root.findall('.//w:drawing', NS):
                blip = drawing.find('.//a:blip', NS)
                if blip is not None and blip.get(f'{{{NS["r"]}}}embed') == rid:
                    size_drawing(drawing, 2160000, round(2160000 * im.height / im.width))
        for paragraph in root.iter(W_P):
            if text(paragraph).strip() == 'Исполнитель:':
                nodes = paragraph.findall('.//w:t', NS)
                nodes[0].text = 'Исполнитель: {{vendor_frln}}'
                for node in nodes[1:]: node.text = ''
        return
    targets = {r.get('Id') for r in relations if r.get('Target') in {'media/image1.png', 'media/image2.png'}}
    source = None
    for drawing in list(root.findall('.//w:drawing', NS)):
        blip = drawing.find('.//a:blip', NS)
        if blip is not None and blip.get(f'{{{NS["r"]}}}embed') in targets:
            if source is None: source = deepcopy(drawing)
            drawing.getparent().remove(drawing)
    assert source is not None
    old_container = source[0]
    inline = etree.Element(f'{{{NS["wp"]}}}inline', distT='0', distB='0', distL='0', distR='0')
    for child in list(old_container):
        if etree.QName(child).localname in {'extent', 'effectExtent', 'docPr', 'cNvGraphicFramePr', 'graphic'}:
            inline.append(child)
    source.replace(old_container, inline)
    source.find('.//a:blip', NS).set(f'{{{NS["r"]}}}embed', rid)
    source.find('.//wp:docPr', NS).set('descr', 'Мырзалиев Медеубек Бахытович: подпись и печать Автосерт-М')
    with Image.open(REF / 'act_executor_medeu.png') as im:
        size_drawing(source, 2160000, round(2160000 * im.height / im.width))
    label = next(p for p in root.iter(W_P) if text(p).startswith('Исполнитель:'))
    image_paragraph = etree.Element(W_P)
    run = etree.SubElement(image_paragraph, W_R)
    run.append(source)
    label.addnext(image_paragraph)
    for p in list(label.getparent().findall('w:p', NS)):
        if text(p).strip() and set(text(p).strip()) == {'_'}:
            p.getparent().remove(p)
    rel = etree.SubElement(relations, '{http://schemas.openxmlformats.org/package/2006/relationships}Relationship')
    rel.set('Id', rid); rel.set('Type', NS['r'] + '/image'); rel.set('Target', 'media/act_executor_medeu.png')
    entries[image_name] = (image_name, block)


def update(name):
    path = REF / name
    with ZipFile(path) as z:
        entries = {i.filename: (i, z.read(i.filename)) for i in z.infolist()}
        comment = z.comment
    root = etree.fromstring(entries['word/document.xml'][1])
    relations = etree.fromstring(entries['word/_rels/document.xml.rels'][1])
    for paragraph in root.iter(W_P):
        _replace_in_container(paragraph, {}, [
            ('в лице Директора {{vendor_frln}}', 'в лице директора {{vendor_frln_genitive}}'),
            ('в лице руководителя {{vendor_frln}}', 'в лице директора {{vendor_frln_genitive}}'),
            ('Мырзалиева М.Б.', '{{vendor_frln_genitive}}'),
            ('Исполнитель:{{vendor_frln}}', 'Исполнитель: {{vendor_frln}}'),
            ('Исполнитель:Директор {{vendor_frln}}', 'Исполнитель, директор: {{vendor_frln}}'),
        ])
    for cell in root.findall('.//w:tc', NS):
        contents = text(cell)
        if '{{vendor_iik}}' not in contents and 'KZ3096516F0010293217' not in contents:
            continue
        assert not cell.findall('.//w:drawing', NS), 'Unexpected image in requisites cell'
        original = cell.find('w:p', NS)
        properties = original.find('w:pPr', NS) if original is not None else None
        for child in list(cell):
            if child.tag != f'{{{W_NS}}}tcPr': cell.remove(child)
        lines = LINES
        for line in lines:
            p = etree.SubElement(cell, W_P)
            if properties is not None: p.append(deepcopy(properties))
            # Compact requisites avoid pushing the signature off the act page.
            ppr = p.find('w:pPr', NS)
            if ppr is None: ppr = etree.SubElement(p, f'{{{W_NS}}}pPr')
            spacing = ppr.find('w:spacing', NS)
            if spacing is None: spacing = etree.SubElement(ppr, f'{{{W_NS}}}spacing')
            for key, value in {'before': '0', 'after': '0', 'line': '220', 'lineRule': 'auto'}.items():
                spacing.set(f'{{{W_NS}}}{key}', value)
            run = etree.SubElement(p, W_R)
            rp = etree.SubElement(run, f'{{{W_NS}}}rPr')
            fonts = etree.SubElement(rp, f'{{{W_NS}}}rFonts')
            for key in ['ascii', 'hAnsi', 'cs', 'eastAsia']: fonts.set(f'{{{W_NS}}}{key}', 'Times New Roman')
            for tag in ['sz', 'szCs']:
                etree.SubElement(rp, f'{{{W_NS}}}{tag}').set(f'{{{W_NS}}}val', '20')
            etree.SubElement(run, W_T).text = line
    signature = (REF / 'director_sign_medeu.png').read_bytes()
    rid = next(r.get('Id') for r in relations if 'word/' + r.get('Target', '') == SIGNATURES[name])
    with Image.open(REF / 'director_sign_medeu.png') as im: ratio = im.height / im.width
    for drawing in list(root.findall('.//w:drawing', NS)):
        blip = drawing.find('.//a:blip', NS)
        if blip is None or blip.get(f'{{{NS["r"]}}}embed') != rid: continue
        extent = drawing.find('.//wp:extent', NS)
        width = min(int(extent.get('cx')), 1260000)
        size_drawing(drawing, width, round(width * ratio))
    entries[SIGNATURES[name]] = (entries[SIGNATURES[name]][0], signature)
    if name in {'act.docx', 'act_qaz.docx'}:
        combine_executor(root, relations, entries)
    for key, xml in [('word/document.xml', root), ('word/_rels/document.xml.rels', relations)]:
        entries[key] = (entries[key][0], etree.tostring(xml, encoding='UTF-8', xml_declaration=True, standalone=True))
    temporary = path.with_suffix('.docx.tmp')
    with ZipFile(temporary, 'w') as z:
        z.comment = comment
        for info, data in entries.values(): z.writestr(info, data)
    with ZipFile(temporary) as z: assert z.testzip() is None
    temporary.replace(path)
    print(name)


if __name__ == '__main__':
    for name in SIGNATURES: update(name)
