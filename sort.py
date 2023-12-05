from typing import Set, DefaultDict, Dict, List, Union
import os
import sys
import shutil
import pathlib
import tempfile
import datetime
import collections

RESULT_FOLDERS = ("images", "video", "documents", "audio", "archives")

def normalize(file_name: str) -> str:
    char_map = {
        ord('a'): 'а', ord('b'): 'б', ord('v'): 'в', ord('h'): 'г', ord('g'): 'ґ',
        ord('d'): 'д', ord('e'): 'е', ord('ie'): 'є', ord('zh'): 'ж', ord('z'): 'з',
        ord('y'): 'и', ord('i'): 'і', ord('yi'): 'ї', ord('i'): 'й', ord('k'): 'к',
        ord('l'): 'л', ord('m'): 'м', ord('n'): 'н', ord('o'): 'о', ord('p'): 'п',
        ord('r'): 'р', ord('s'): 'с', ord('t'): 'т', ord('u'): 'у', ord('f'): 'ф',
        ord('kh'): 'х', ord('ts'): 'ц', ord('ch'): 'ч', ord('sh'): 'ш', ord('shch'): 'щ',
        ord("'"): 'ь', ord('iu'): 'ю', ord('ia'): 'я'
    }
    return file_name.translate(char_map)

def process_dir(result_path: pathlib.Path, element: pathlib.Path, extensions_info: DefaultDict[str, Set[str]]) -> bool:
    res = False
    if element.name not in RESULT_FOLDERS:
        folder_res = diver(result_path, element, extensions_info)

        if folder_res is False:
            element.rmdir()

        res |= folder_res

    return res

def process_file(result_path: pathlib.Path, element: pathlib.Path, extensions_info: DefaultDict[str, Set[str]]) -> bool:
    table: Tuple[Tuple[str, ...], ...] = (
        ("JPEG", "PNG", "JPG", "SVG"),
        ("AVI", "MP4", "MOV", "MKV"),
        ("DOC", "DOCX", "TXT", "PDF", "XLXS", "PPTX"),
        ("MP3", "OGG", "WAV", "AMR"),
        ("ZIP", "GZ", "TAR"),
    )

    suffixes_dict: Dict[str, str] = {
        table[i][j]: RESULT_FOLDERS[i]
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

def diver(result_path: pathlib.Path, folder_path: pathlib.Path, extensions_info: DefaultDict[str, Set[str]]) -> bool:
    res = False

    if not any(folder_path.iterdir()):
        return res

    for element in folder_path.iterdir():
        processor = process_dir if element.is_dir() else process_file
        res |= processor(result_path, element, extensions_info)

    return res

def post_processor(result_path: pathlib.Path, extensions_info: DefaultDict[str, Set[str]]) -> None:
    print(f"Known extensions: {extensions_info['known']}")
    if len(extensions_info):
        print(f"Unknown extensions: {extensions_info['unknown']}")

    for folder in result_path.iterdir():
        print(f"{folder.name}:")
        for item in folder.iterdir():
            print(f"\t{item.name}")

def main(folder_platform_path: str) -> None:
    extensions_info: DefaultDict[str, Set[str]] = collections.defaultdict(set)
    folder_path = pathlib.Path(folder_platform_path)

    if not folder_path.is_dir():
        raise RuntimeError("error: no such directory")

    with tempfile.TemporaryDirectory() as tmp_platform_path:
        tmp_path = pathlib.Path(tmp_platform_path)

        if diver(tmp_path, folder_path, extensions_info) is False:
            raise RuntimeError("It is an empty directory")

        os.makedirs("results", exist_ok=True)

        result_path = pathlib.Path(
            f"result/result_{datetime.datetime.now().strftime('%d.%m.%y_%H:%M')}"
        )

        shutil.copytree(
            str(tmp_path),
            str(result_path)
        )

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise RuntimeError(f"usage: {sys.argv[0]} folder_platform_path")

    main(sys.argv[1])
