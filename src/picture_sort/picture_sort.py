from pathlib import Path
import shutil
import questionary
import re


class File:
    def __init__(self, name: str, subfolder: str = ""):
        self.name = name
        self.subfolder = subfolder

    def __repr__(self) -> str:
        return f"File(name={self.name!r}, subfolder={self.subfolder!r})"


def readFile(MK_LIST, CAMERA_PREFIX, FILE_ENDING):
    elements = []
    subfolder = ""

    with open(MK_LIST, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()

            # Headings define destination subfolders.
            if line.startswith("#"):
                subfolder = line.lstrip("#").strip()
                continue
            
            if not line or "#" in line:
                continue

            parts = line.split("/")

            #? Keep only digits in each part.
            parts = [
                re.sub(r"\D", "", part)
                for part in parts
            ]

            parts = [part for part in parts if part]

            if not parts:
                continue

            prefix = parts[0]

            elements.append(
                File(
                    CAMERA_PREFIX + prefix + FILE_ENDING,
                    subfolder
                )
            )

            for part in parts[1:]:
                elements.append(
                    File(
                        CAMERA_PREFIX + prefix[:2] + part + FILE_ENDING,
                        subfolder
                    )
                )

    # Deduplicate by filename and destination folder.
    unique = []
    seen = set()

    for element in elements:
        key = (element.name.lower(), element.subfolder.lower())

        if key not in seen:
            seen.add(key)
            unique.append(element)

    return unique



def copySelected(INPUT_FOLDER, OUTPUT_FOLDER, elements):
    INPUT_FOLDER = Path(INPUT_FOLDER)
    OUTPUT_FOLDER = Path(OUTPUT_FOLDER)

    OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

    copied = 0
    skipped = 0
    missing_source = []
    copy_errors = []

    # Index source files by exact filename, ignoring case.
    source_files = {
        file.name.lower(): file
        for file in INPUT_FOLDER.iterdir()
        if file.is_file()
    }

    for element in elements:
        source = source_files.get(element.name.lower())

        if source is None:
            missing_source.append(element)
            print(f"NOT FOUND: {element.name}")
            continue

        # Build the destination using the Markdown heading.
        destination_folder = OUTPUT_FOLDER

        if element.subfolder:
            destination_folder /= element.subfolder

        destination = destination_folder / source.name

        # Never overwrite an existing file.
        if destination.exists():
            if destination.is_file():
                skipped += 1
                print(f"SKIPPED (already exists): {destination}")
            else:
                copy_errors.append((element, "Destination exists but is not a file"))
                print(f"ERROR: Destination is not a file: {destination}")
            continue

        try:
            destination_folder.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            copied += 1
            print(f"COPIED: {source.name} -> {destination}")
        except OSError as error:
            copy_errors.append((element, str(error)))
            print(f"ERROR copying {source.name}: {error}")

    # Verify every requested file at its expected relative path.
    verified = []
    not_verified = []

    for element in elements:
        destination = OUTPUT_FOLDER

        if element.subfolder:
            destination /= element.subfolder

        destination /= element.name

        if destination.is_file():
            verified.append(element)
        else:
            not_verified.append(element)

    print("\n" + "=" * 55)
    print("COPY AND INTEGRITY REPORT")
    print("=" * 55)
    print(f"Requested from Markdown : {len(elements)}")
    print(f"Copied during this run  : {copied}")
    print(f"Already existed         : {skipped}")
    print(f"Missing source files    : {len(missing_source)}")
    print(f"Copy errors             : {len(copy_errors)}")
    print(f"Verified in output      : {len(verified)}")
    print(f"Missing from output     : {len(not_verified)}")

    if missing_source:
        print("\nMissing source files:")
        for element in missing_source:
            print(f"  - {element.name} (folder: {element.subfolder or '.'})")

    if copy_errors:
        print("\nCopy errors:")
        for element, error in copy_errors:
            print(f"  - {element.name}: {error}")

    if not_verified:
        print("\nFiles missing from expected output locations:")
        for element in not_verified:
            print(f"  - {element.subfolder + '/' if element.subfolder else ''}{element.name}")

    success = not missing_source and not copy_errors and not not_verified

    if success:
        print("\nSUCCESS: All requested files are present in their expected folders.")
    else:
        print("\nERROR: The integrity check failed. Review the report above.")

    return success


def searchMatch(PATH, file_ending=None, prompt="Search", directories=False):
    PATH = Path(PATH)

    if not PATH.is_dir():
        print(f"Folder does not exist: {PATH}")
        return None

    search = input(f"{prompt}: ").strip().lower()

    matches = [
        item
        for item in PATH.iterdir()
        if (
            item.is_dir() if directories
            else (
                item.is_file()
                and (
                    file_ending is None
                    or item.suffix.lower() == file_ending.lower()
                )
            )
        )
        and search in item.name.lower()
    ]

    matches.sort(key=lambda item: item.name.lower())

    if not matches:
        print("No matches found.")
        return None

    if len(matches) > 100:
        print(f"Found {len(matches)} matches. Showing first 100.")

    selected = questionary.select(
        "Select:",
        choices=[item.name for item in matches[:100]]
    ).ask()

    if selected is None:
        return None

    return PATH / selected


def selectWithRetry(
    PATH,
    file_ending=None,
    prompt="Search",
    directories=False,
    attempts=3
):
    for attempt in range(1, attempts + 1):
        print(f"\nAttempt {attempt}/{attempts}")

        selected = searchMatch(
            PATH,
            file_ending=file_ending,
            prompt=prompt,
            directories=directories
        )

        if selected is not None:
            return selected

    print(f"{attempts} unsuccessful attempts. Aborting.")
    return None


def initFilename():
    FUJI_CAMERA_PREFIX = "_DSF"
    FUJI_CAMERA_POSTFIX = ".RAF"

    answer = input(
        f"Use Fuji filenames? "
        f"[{FUJI_CAMERA_PREFIX}XXXX{FUJI_CAMERA_POSTFIX}] (y/n): "
    ).strip().lower()

    if answer != "n":
        return FUJI_CAMERA_PREFIX, FUJI_CAMERA_POSTFIX

    SONY_CAMERA_PREFIX = "_DSC"
    SONY_CAMERA_POSTFIX = ".ARW"

    answer = input(
        f"Use Sony filenames? "
        f"[{SONY_CAMERA_PREFIX}XXXX{SONY_CAMERA_POSTFIX}] (y/n): "
    ).strip().lower()

    if answer != "n":
        return SONY_CAMERA_PREFIX, SONY_CAMERA_POSTFIX

    CAMERA_PREFIX = input("Prefix: ").strip()
    CAMERA_POSTFIX = input("Postfix: ").strip()

    return CAMERA_PREFIX, CAMERA_POSTFIX


def initMarkdown(MK_FOLDER):
    print(
        f"Markdown Base-path: {MK_FOLDER}\n"
        "Select Markdown file:"
    )

    return selectWithRetry(
        MK_FOLDER,
        file_ending=".md",
        prompt="Search Markdown"
    )


def initFolder(BASE_PATH):
    BASE_PATH = Path(BASE_PATH)

    print(
        f"\nPicture Base-path: {BASE_PATH}\n"
        "Select Picture folder for input:"
    )

    current_path = BASE_PATH

    for attempt in range(1, 10):
        print(f"\nAttempt {attempt}/9")

        INPUT_PATH = searchMatch(
            current_path,
            prompt="Search folder",
            directories=True
        )

        if INPUT_PATH is None:
            continue

        files = [
            item for item in INPUT_PATH.iterdir()
            if item.is_file()
        ]

        if not files:
            print(
                f"No files found in '{INPUT_PATH.name}'. "
                "Searching inside this folder instead."
            )
            current_path = INPUT_PATH
            continue

        OUTPUT_PATH = INPUT_PATH / "sel"
        return INPUT_PATH, OUTPUT_PATH

    print("Nine unsuccessful attempts. Aborting.")
    return None


def main():
    SMB_PATH = Path("Z:/")
    CLOUD_PATH = Path(r"G:\Nextcloud")
    EXTERNAL_PATH = Path(r"F:\backup")

    # Adjust these paths for your machines.
    if SMB_PATH.exists():
        BASE_PATH = SMB_PATH
        print("Using SMB path.")
    elif CLOUD_PATH.exists():
        BASE_PATH = CLOUD_PATH
        print("Using Nextcloud path.")
    else:
        print("ERROR: Neither configured base path is available.")
        print(f"  SMB:   {SMB_PATH}")
        print(f"  Cloud: {CLOUD_PATH}")
        return

    MK_PATH = BASE_PATH / "Documents" / "Cloud" / "Notes" / "Galaxy"
    # PICTURE_PATH = BASE_PATH / "Data" / "Awayfromfalling"
    PICTURE_PATH = EXTERNAL_PATH

    print(
        f"Base path:     {BASE_PATH}\n"
        f"Picture path:  {PICTURE_PATH}\n"
        f"Markdown path: {MK_PATH}"
    )

    if not MK_PATH.is_dir():
        print(f"ERROR: Markdown path does not exist: {MK_PATH}")
        return

    if not PICTURE_PATH.is_dir():
        print(f"ERROR: Picture path does not exist: {PICTURE_PATH}")
        return

    try:
        result = initFilename()
        if result is None:
            return
        CAMERA_PREFIX, CAMERA_POSTFIX = result

        MK_LIST = initMarkdown(MK_PATH)
        if MK_LIST is None:
            return

        result = initFolder(PICTURE_PATH)
        if result is None:
            return
        INPUT_PATH, OUTPUT_PATH = result

        elements = readFile(
            MK_LIST,
            CAMERA_PREFIX,
            CAMERA_POSTFIX
        )

        print(f"\nInput:   {INPUT_PATH}")
        print(f"Output:  {OUTPUT_PATH}")
        print(f"Markdown: {MK_LIST}")
        print(f"Files selected: {len(elements)}")

        success = copySelected(
            INPUT_PATH,
            OUTPUT_PATH,
            elements
        )

        if not success:
            print("\nWARNING: The copy operation was not completely successful.")

    except Exception as error:
        print(f"Error: {error}")


if __name__ == "__main__":
    main()
