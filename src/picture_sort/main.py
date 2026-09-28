from pathlib import Path
import shutil
import questionary


def readFile(MK_LIST, CAMERA_PREFIX, FILE_ENDING):
    elements = []

    with open(MK_LIST, "r", encoding="utf-8") as file:
        lines = file.readlines()

    for line in lines:
        parts = line.strip()

        # Skip empty lines and Markdown headings/comments
        if not line or "#" in line:
            continue

        parts = line.split("/")

        if not parts[0]:
            continue

        prefix = parts[0]

        elements.append(
            CAMERA_PREFIX + prefix + FILE_ENDING
        )

        for part in parts[1:]:
            part = part.strip()
            if part:
                elements.append(
                    CAMERA_PREFIX + prefix[:2] + part + FILE_ENDING
                )

    return elements


def copySelected(INPUT_FOLDER, OUTPUT_FOLDER, elements):
    INPUT_FOLDER = Path(INPUT_FOLDER)
    OUTPUT_FOLDER = Path(OUTPUT_FOLDER)

    OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

    # Remove duplicate filenames while preserving order
    elements = list(dict.fromkeys(elements))

    requested = len(elements)
    copied = 0
    skipped = 0
    missing = []

    for element in elements:
        matches = [
            file
            for file in INPUT_FOLDER.iterdir()
            if file.is_file()
            and element.lower() in file.name.lower()
        ]

        if not matches:
            missing.append(element)
            print(f"NOT FOUND: {element}")
            continue

        for source in matches:
            destination = OUTPUT_FOLDER / source.name

            if destination.exists():
                skipped += 1
                print(f"SKIPPED (already exists): {source.name}")
                continue

            shutil.copy2(source, destination)
            copied += 1
            print(f"COPIED: {source.name}")

    # Cross-check output
    output_files = {
        file.name.lower()
        for file in OUTPUT_FOLDER.iterdir()
        if file.is_file()
    }

    verified = []
    not_verified = []

    for element in elements:
        if element.lower() in output_files:
            verified.append(element)
        else:
            not_verified.append(element)

    print("\n" + "=" * 50)
    print("COPY REPORT")
    print("=" * 50)

    print(f"Requested from Markdown : {requested}")
    print(f"Copied                   : {copied}")
    print(f"Already existed          : {skipped}")
    print(f"Not found in input       : {len(missing)}")
    print(f"Verified in output       : {len(verified)}")
    print(f"NOT verified             : {len(not_verified)}")

    if missing:
        print("\nMissing source files:")
        for file in missing:
            print(f"  - {file}")

    if not_verified:
        print("\nFiles missing from output:")
        for file in not_verified:
            print(f"  - {file}")

    # Final result
    if not missing and not not_verified:
        print("\n✓ SUCCESS: All selected files are present in the output folder.")
        return True

    print("\n✗ ERROR: Something is missing. Please check the report above.")
    return False


def searchMatch(PATH, file_ending=None, prompt="Search", directories=False):
    PATH = Path(PATH)

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

    if not matches:
        print("No matches found.")
        return None

    matches = sorted(matches, key=lambda item: item.name.lower())

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
    directories=False
):
    for attempt in range(1, 4):
        print(f"\nAttempt {attempt}/3")

        selected = searchMatch(
            PATH,
            file_ending=file_ending,
            prompt=prompt,
            directories=directories
        )

        if selected is not None:
            return selected

    print("Three unsuccessful attempts. Aborting.")
    return None

def initFilename():
    CAMERA_PREFIX = "_DSF"
    CAMERA_POSTFIX = ".RAF"

    answer = input(
        f"Use default filenames? "
        f"[{CAMERA_PREFIX}XXXX{CAMERA_POSTFIX}] (y/n): "
    ).strip().lower()

    if answer == "n":
        CAMERA_PREFIX = input("Prefix: ").strip()
        CAMERA_POSTFIX = input("Postfix: ").strip()

    return CAMERA_PREFIX, CAMERA_POSTFIX



def initMarkdown(MK_FOLDER):

    print(
        f"Markdown Base-path: {MK_FOLDER}\n"
        "Select Markdown file:"
    )

    MK_LIST = selectWithRetry(
        MK_FOLDER,
        file_ending=".md",
        prompt="Search Markdown"
    )

    if MK_LIST is None:
        return None

    return MK_LIST


def initFolder(BASE_PATH):
    BASE_PATH = Path(BASE_PATH)

    print(
        f"\nPicture Base-path: {BASE_PATH}\n"
        "Select Picture folder for input:"
    )

    for attempt in range(1, 10):
        print(f"\nAttempt {attempt}/9")

        INPUT_PATH = searchMatch(
            BASE_PATH,
            prompt="Search folder",
            directories=True
        )

        if INPUT_PATH is None:
            continue

        # Check whether the selected folder contains files
        files = [
            item for item in INPUT_PATH.iterdir()
            if item.is_file()
        ]

        if not files:
            print(
                f"No files found in '{INPUT_PATH.name}'. "
                "Please select desired child-folder."
            )
            BASE_PATH = INPUT_PATH
            continue

        OUTPUT_PATH = INPUT_PATH / "sel"

        return INPUT_PATH, OUTPUT_PATH

    print("Three unsuccessful attempts. Aborting.")
    return None


def main():
    SMB_PATH = Path("Z:/")
    CLOUD_PATH = Path(r"G:\Nextcloud")

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
    PICTURE_PATH = BASE_PATH / "Data" / "Awayfromfalling"

    print(f"Base path: {BASE_PATH}\nPicture path: {PICTURE_PATH}\nMarkdown path: {MK_PATH}")

    try:

        result = initFilename()
        if result is None:
            return
        CAMERA_PREFIX, CAMERA_POSTFIX = result

        result = initMarkdown(MK_PATH)
        if result is None:
            return
        MK_LIST = result

        result = initFolder(PICTURE_PATH)
        if result is None:
            return
        INPUT_PATH, OUTPUT_PATH = result

        elements = readFile(
            MK_LIST,
            CAMERA_PREFIX,
            CAMERA_POSTFIX
        )

        print(elements)

        print(f"\nInput:       {INPUT_PATH}")
        print(f"Output:      {OUTPUT_PATH}")
        print(f"Markdown:    {MK_LIST}")
        print(f"Files selected for copy: {len(elements)}")

        if not MK_PATH.is_dir():
            print(f"ERROR: Markdown path does not exist: {MK_PATH}")
            return

        if not PICTURE_PATH.is_dir():
            print(f"ERROR: Picture path does not exist: {PICTURE_PATH}")
            return
    
        success = copySelected(
            INPUT_PATH,
            OUTPUT_PATH,
            elements
        )
    
        if not success:
            print("\nWARNING: The copy operation was not completely successful.")


    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()