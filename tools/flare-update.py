#!/usr/bin/python3
import os, argparse, difflib

lookup = {
    "flare-form-field": "viur-form-bone",
    "flare-form-submit": "viur-form-submit",
    "flare-form": "viur-form",

    "boneField": "ViurFormBone",
    "sendForm": "ViurFormSubmit",
    "viurForm": "ViurForm",

    "boneSelector": "BoneSelector",
    "moduleWidgetSelector": "ModuleWidgetSelector",
    "displayDelegateSelector": "DisplayDelegateSelector",

    "from flare.forms.formtags import": "from flare.viur import",
    "from flare.forms": "from flare.viur",
}

if __name__ == "__main__":
    # Get arguments
    ap = argparse.ArgumentParser(
        description="Flare source code porting tool"
    )

    ap.add_argument(
        "project_root",
        type=str,
        help="Flare project root"
    )

    ap.add_argument(
        "-d", "--dryrun",
        action="store_true",
        help="Dry-run for testing, don't modify files"
    )
    ap.add_argument(
        "-x", "--daredevil",
        action="store_true",
        help="Don't make backups of files, just replace and deal with it"
    )

    args = ap.parse_args()

    # Iterate all files in current folder
    for root, dirs, files in os.walk(args.project_root):
        # Ignore ViUR library folders
        if any(ignore in root for ignore in ["flare"]):
            continue

        for filename in files:
            # Ignore anything without a .py-extension
            ext = os.path.splitext(filename)[1].lower()[1:]
            if ext not in ["py"]:
                continue

            filename = os.path.join(root, filename)

            with open(filename, "r") as f:
                original_content = content = f.read()

            count = 0
            for k, v in lookup.items():
                if k in content:
                    content = content.replace(k, v)
                    count += 1

            if count:
                if not args.dryrun:
                    if not args.daredevil:
                        os.rename(filename, filename + ".bak")

                    with open(filename, "w") as f:
                        f.write(content)

                    print("Modified %r" % filename)
                else:
                    print(
                        "\n".join(
                            difflib.unified_diff(
                                original_content.splitlines(),
                                content.splitlines(),
                                filename,
                                filename
                            )
                        )
                    )
