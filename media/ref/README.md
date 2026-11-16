# Автосерт-М

The document templates use «Автосерт-М» throughout.

`pechat.png` is the round company seal copied from `journal_С-00395.docx`
(`word/media/image3.png`). The text-only company wordmark is no longer used as
a seal in the document templates.

`director_signature_and_stamp.png` is the existing combined director signature
and round seal copied from `contract.docx` (`word/media/image1.png`). It is used
in `contract.docx` and `act_contract_qaz.docx` without regenerating the image.

Laboratory staff signatures and their sources are described in
[`signature_sources/README.md`](signature_sources/README.md). Run
`python scripts/update_ref_documents.py --staff-only` to update only those
names and signatures, preserving the company seals and director signatures.
