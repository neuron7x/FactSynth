#!/usr/bin/env python3
# ruff: noqa: I001
"""Sanitize ZIP files for CI usage."""

import sys
import zipfile

from pathlib import PurePosixPath

ZIP_UNIX_SYSTEM = 3
SYMLINK_MODE = 0o120000

zf = zipfile.ZipFile(sys.argv[1])
bad = []
for i in zf.infolist():
    name = i.filename
    p = PurePosixPath(name)
    if name.startswith("/") or ".." in p.parts:
        bad.append(name)
    # symlink detection via unix attrs
    is_unix = i.create_system == ZIP_UNIX_SYSTEM
    if is_unix and ((i.external_attr >> 16) & 0o170000) == SYMLINK_MODE:
        bad.append(name + " (symlink)")
    if name.startswith(".git/") or "/.git/" in name or name == ".git":
        bad.append(name + " (.git forbidden)")
if bad:
    print("Forbidden entries:\n- " + "\n- ".join(bad))
    sys.exit(1)
print("ZIP safe")
