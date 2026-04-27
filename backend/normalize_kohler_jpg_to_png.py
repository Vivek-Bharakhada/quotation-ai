import csv
import os
from PIL import Image


BASE_DIR = os.path.dirname(__file__)
IMAGE_DIR = os.path.join(BASE_DIR, "static", "images", "Kohler")
REPORT_PATH = os.path.join(BASE_DIR, "kohler_image_normalize_report.csv")


def main():
    rows = []
    converted = 0
    removed = 0

    for name in sorted(os.listdir(IMAGE_DIR)):
        if not name.lower().endswith((".jpg", ".jpeg")):
            continue

        src = os.path.join(IMAGE_DIR, name)
        stem = os.path.splitext(name)[0]
        dst = os.path.join(IMAGE_DIR, stem + ".png")

        if os.path.exists(dst):
            status = "skipped_exists"
            rows.append([name, os.path.basename(dst), status])
            continue

        with Image.open(src) as img:
            img.convert("RGB").save(dst, "PNG")

        os.remove(src)
        converted += 1
        removed += 1
        rows.append([name, os.path.basename(dst), "converted"])

    with open(REPORT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["source_file", "target_file", "status"])
        writer.writerows(rows)

    print(f"Normalize report written: {REPORT_PATH}")
    print(f"Converted: {converted}")
    print(f"Removed source JPGs: {removed}")


if __name__ == "__main__":
    main()
