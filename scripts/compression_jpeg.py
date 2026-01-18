from pathlib import Path
from PIL import Image

def jpeg_compression_info(folder):
    for img_path in Path(folder).glob("*.jpg"):
        with Image.open(img_path) as img:
            width, height = img.size
            pixels = width * height
            size_bytes = img_path.stat().st_size
            ratio = size_bytes / pixels
            dpi = img.info.get("dpi", None)

        print(f"{img_path.name:30} | {width}x{height} | "
              f"{size_bytes/1024:8.1f} KB | {ratio:.2f} B/pixel| "
              f"DPI: {dpi}")


# Exemple
jpeg_compression_info("C:/Projets/GONM/Numérisation/003_Grebe_Castagneux")
