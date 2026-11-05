#!/usr/bin/env python3
"""The Pages upload drops dot paths unless include-hidden-files is true.

Run 42083173913 archived dist with tar --exclude=.[^/]* and the live site
then 404ed /.well-known/mcp-registry-auth and /.nojekyll. This checks both
deploy workflows and rebuilds that tar from dist/.
"""
import os
import subprocess
import tarfile
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, "dist")
AUTH = ".well-known/mcp-registry-auth"
WORKFLOWS = (
    os.path.join(ROOT, ".github", "workflows", "pages.yml"),
    os.path.join(ROOT, ".github", "workflows", "refresh.yml"),
)


def names(archive):
    found = set()
    with tarfile.open(archive) as tar:
        for item in tar.getmembers():
            name = item.name
            if name.startswith("./"):
                name = name[2:]
            found.add(name)
    return found


def archive(dest, include_hidden):
    cmd = [
        "tar",
        "--dereference",
        "--hard-dereference",
        "--directory",
        DIST,
        "-cf",
        dest,
        "--exclude=.git",
        "--exclude=.github",
    ]
    if not include_hidden:
        cmd.append("--exclude=.[^/]*")
    cmd.append(".")
    subprocess.check_call(cmd, stdout=subprocess.DEVNULL)


def main():
    errors = []
    for path in WORKFLOWS:
        text = open(path, encoding="utf-8").read()
        if "actions/upload-pages-artifact@" not in text:
            errors.append(f"{os.path.basename(path)} does not upload a Pages artifact")
        elif "include-hidden-files: true" not in text:
            errors.append(
                f"{os.path.basename(path)} leaves include-hidden-files false, "
                "so .well-known is not deployed"
            )
    if not os.path.isdir(DIST):
        errors.append("dist/ is missing; build the site first")
    else:
        with tempfile.TemporaryDirectory() as tmp:
            hidden_off = os.path.join(tmp, "default.tar")
            hidden_on = os.path.join(tmp, "with-hidden.tar")
            archive(hidden_off, False)
            archive(hidden_on, True)
            dropped = names(hidden_off)
            kept = names(hidden_on)
            for rel in (AUTH, ".nojekyll"):
                if rel in dropped:
                    errors.append(f"default Pages tar still contains {rel}")
                if rel not in kept:
                    errors.append(f"include-hidden-files tar is missing {rel}")
            member = "./" + AUTH
            with tarfile.open(hidden_on) as tar:
                extracted = tar.extractfile(member)
                body = extracted.read().decode("utf-8").strip() if extracted else ""
            if body != "v=MCPv1; k=ed25519; p=PLACEHOLDER_REPLACE_AT_PUBLISH":
                errors.append(f"artifact auth file body is {body!r}")
            if any(name.endswith(".html") and "well-known" in name for name in kept):
                errors.append("the registry path was archived as HTML")
    if errors:
        raise SystemExit("pages artifact check failed:\n- " + "\n- ".join(errors))
    print("ok Pages artifact keeps .well-known and .nojekyll when hidden files are included")


if __name__ == "__main__":
    main()
