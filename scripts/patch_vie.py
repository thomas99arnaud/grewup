from pathlib import Path

models = Path("backend/modules/offers/models.py")
text = models.read_text(encoding="utf-8")
if 'VIE = "vie"' not in text:
    text = text.replace(
        'class OfferSource(str, enum.Enum):\n    WTTJ = "wttj"',
        'class OfferSource(str, enum.Enum):\n    VIE = "vie"\n    WTTJ = "wttj"',
    )
    models.write_text(text, encoding="utf-8", newline="\n")
    print("models.py updated")

router = Path("backend/modules/offers/router.py")
text = router.read_text(encoding="utf-8")
needle = "location=params.location,\n            greenhouse_slugs"
if "specialization_ids=params.specialization_ids" not in text:
    text = text.replace(
        needle,
        "location=params.location,\n"
        "            specialization_ids=params.specialization_ids,\n"
        "            teletravail=params.teletravail,\n"
        "            porte_env=params.porte_env,\n"
        "            greenhouse_slugs",
    )
    router.write_text(text, encoding="utf-8", newline="\n")
    print("router.py updated")

worker = Path("backend/workers/scrape_worker.py")
text = worker.read_text(encoding="utf-8")
needle = 'location=params_dict.get("location", ""),\n        greenhouse_slugs'
if "specialization_ids=params_dict.get" not in text:
    text = text.replace(
        needle,
        'location=params_dict.get("location", ""),\n'
        '        specialization_ids=params_dict.get("specialization_ids", ["24"]),\n'
        '        teletravail=params_dict.get("teletravail", ["0"]),\n'
        '        porte_env=params_dict.get("porte_env", ["0"]),\n'
        "        greenhouse_slugs",
    )
    worker.write_text(text, encoding="utf-8", newline="\n")
    print("scrape_worker.py updated")
