# ruff: noqa: F401
from datetime import datetime
from pathlib import Path

import ffmpeg
from PIL import Image
from PIL.ExifTags import TAGS

media_dir = Path(__file__).parent.parent / "media_files"
img_suffix = (".jpg", ".jpeg", ".png", ".gif")
video_suffix = (".mp4", ".mov", ".mkv", ".avi", ".wmv", ".flv")
new_name = ""

# List comprehension to get only files
files_list = [p for p in media_dir.iterdir() if p.is_file()]

# Print the list of Path objects
for file_path in files_list:
    name_datetime = ""
    file_extension = file_path.suffix.lower()
    if file_extension in img_suffix:
        media = Path(file_path)
        with Image.open(media) as image:
            exif = image._getexif()
            for tag, value in exif.items():
                decoded = TAGS.get(tag, tag)
                if decoded in (
                    "UserComment",
                    "MakerNote",
                    "PrintImageMatching",
                    "ComponentsConfiguration",
                    "FileSource",
                ):
                    continue
                # print(f"{decoded}: {value}")
                if decoded == "DateTime":
                    name_datetime = datetime.strptime(
                        value, "%Y:%m:%d %H:%M:%S"
                    ).strftime("%Y%m%d_%H%M%S")
                    new_name = media_dir / f"{name_datetime}{file_extension}"
        if not new_name:
            continue
        try:
            media.rename(new_name)
        except FileExistsError:
            count = 1
            while new_name.exists():
                count += 1
                new_name = media_dir / f"{name_datetime}_{count}{file_extension}"
            media.rename(new_name)
        finally:
            new_name = ""

    elif file_extension in video_suffix:
        media = Path(file_path)
        probe = ffmpeg.probe(file_path)
        for stream in probe["streams"]:
            if stream["codec_type"] == "video":
                creation_time_iso = datetime.fromisoformat(
                    stream["tags"]["creation_time"]
                )
                name_datetime = creation_time_iso.strftime("%Y%m%d_%H%M%S")
                new_name = media_dir / f"{name_datetime}{file_extension}"
                break
        if not new_name:
            continue
        try:
            media.rename(new_name)
        except FileExistsError:
            count = 1
            while new_name.exists():
                count += 1
                new_name = media_dir / f"{name_datetime}_{count}{file_extension}"
            media.rename(new_name)
        finally:
            new_name = ""

if __name__ == "__main__":
    pass
