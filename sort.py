import os
import sys
import shutil
import pathlib
import tempfile
import datetime
import collections

RESULTS_FOLDERS = ("images", "video", "documents", "audio", "archives")


def normalize(file_name: str) -> str:
    reverse_char_map = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'h', 'ґ': 'g',
        'д': 'd', 'е': 'e', 'є': 'ie', 'ж': 'zh', 'з': 'z',
        'и': 'y', 'і': 'i', 'ї': 'yi', 'й': 'i', 'к': 'k',
        'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o', 'п': 'p',
        'р': 'r', 'с': 's', 'т': 't', 'у': 'u', 'ф': 'f',
        'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch',
        'ь': "'", 'ю': 'iu', 'я': 'ia'
    }   

    for char in file_name:
        if char.lower() in reverse_char_map:
            file_name = file_name.replace(char, reverse_char_map[char.lower()])
        elif not char.isalnum():
            file_name = file_name.replace(char, "_")    

    return file_name

def process_dir(result_path, element, extensions_info):
    res = False

    if element.name not in RESULTS_FOLDERS:
        folder_res = diver(result_path, element, extensions_info)

        if folder_res is False:
            element.rmdir()

        res |= folder_res

    return res


def process_file(result_path, element, extensions_info):

    table = (
        ('JPEG', 'PNG', 'JPG', 'SVG'),
        ('AVI', 'MP4', 'MOV', 'MKV'),
        ('DOC', 'DOCX', 'TXT', 'PDF', 'XLSX', 'PPTX'),
        ('MP3', 'OGG', 'WAV', 'AMR'),
        ('ZIP', 'GZ', 'TAR')
    )

    suffixes_dict = {
        table[i][j]: RESULTS_FOLDERS[i]
        for i in range(len(table))
        for j in range(len(table[i]))
    }

    suffix = element.suffix[1:].upper()

    known = suffixes_dict.get(suffix) is not None

    extensions_info["known" if known else "unknown"].add(suffix)

    if known:
        dest_folder = suffixes_dict[suffix]
        result_path /= dest_folder

        if not result_path.is_dir():
            result_path.mkdir()

        if dest_folder == "archives":
            result_path /= f"{normalize(element.stem)}"

            shutil.unpack_archive(
                str(element), str(result_path), element.suffix[1:].lower()
            )
        else:
            result_path /= f"{normalize(element.stem)}{element.suffix}"

            shutil.copy(str(element), str(result_path))

    return True


def diver(result_path, folder_path, extensions_info):
    res = False

    if not any(folder_path.iterdir()):
        return res

    for element in folder_path.iterdir():
        processor = process_dir if element.is_dir() else process_file
        res |= processor(result_path, element, extensions_info)

    return res


def post_processor(results_path, extensions_info):
    print(f"Known extensions: {extensions_info['known']}")
    if len(extensions_info['unknown']):
        print(f"Unknown extensions: {extensions_info['unknown']}")

    for folder in results_path.iterdir():
        print(f"{folder.name}:")
        for item in folder.iterdir():
            print(f"\t{item.name}")


def sorter(folder_platform_path):
    extensions_info = collections.defaultdict(set)
    folder_path = pathlib.Path(folder_platform_path)

    if not folder_path.is_dir():
        raise RuntimeError("error: no such directory")

    with tempfile.TemporaryDirectory() as tmp_platform_path:
        tmp_path = pathlib.Path(tmp_platform_path)

        if diver(tmp_path, folder_path, extensions_info) is False:
            raise RuntimeError("It's empty directory")

        os.makedirs("results", exist_ok=True)

        results_path = pathlib.Path(
            "results/"
            f"result_{datetime.datetime.now().strftime('%d.%m.%y_%H.%M.%S')}"
        )

        shutil.copytree(
            str(tmp_path),
            str(results_path)
        )

    post_processor(results_path, extensions_info)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise RuntimeError(f"usage: {sys.argv[0]} folder_platform_path")

    sorter(sys.argv[1])