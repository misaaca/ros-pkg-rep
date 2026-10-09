#!/usr/bin/env python3
"""
ROS Package Builder Tool
Builds production-grade .rop and .tar.gz packages for the ROS package repository.
"""

import os
import sys
import tarfile
import io
import gzip
import hashlib
import argparse
from typing import List, Dict, Any, Tuple
from rop import RopArchive, RopManifest, RopFile


def build_package_from_payloads(
    name: str,
    version: str,
    description: str,
    arch: str,
    dependencies: List[str],
    files: List[Tuple[str, int, bytes]],
    output_dir: str,
) -> Dict[str, Any]:
    os.makedirs(output_dir, exist_ok=True)

    rop_files = [RopFile(path, mode, content) for (path, mode, content) in files]
    manifest = RopManifest(
        name=name,
        version=version,
        description=description,
        arch=arch,
        dependencies=dependencies,
    )

    archive = RopArchive(manifest, rop_files)
    rop_bytes = archive.pack()

    # Base names
    pkg_base = f"{name}-{version}"
    rop_path = os.path.join(output_dir, f"{pkg_base}.rop")
    tar_path = os.path.join(output_dir, f"{pkg_base}.tar.gz")

    # Write .rop
    with open(rop_path, "wb") as f:
        f.write(rop_bytes)

    # Write .tar.gz
    tar_buffer = io.BytesIO()
    with tarfile.open(fileobj=tar_buffer, mode="w:gz") as tar:
        for path, mode, content in files:
            clean_path = path.lstrip("/")
            tar_info = tarfile.TarInfo(name=clean_path)
            tar_info.size = len(content)
            tar_info.mode = mode
            tar_info.mtime = 1728489600  # deterministic timestamp
            tar_info.uname = "root"
            tar_info.gname = "root"
            tar.addfile(tar_info, io.BytesIO(content))

    tar_bytes = tar_buffer.getvalue()
    with open(tar_path, "wb") as f:
        f.write(tar_bytes)

    rop_sha256 = hashlib.sha256(rop_bytes).hexdigest()
    tar_sha256 = hashlib.sha256(tar_bytes).hexdigest()

    return {
        "name": name,
        "version": version,
        "description": description,
        "arch": arch,
        "dependencies": dependencies,
        "files_count": len(files),
        "installed_size": sum(len(c) for _, _, c in files),
        "rop_file": os.path.basename(rop_path),
        "rop_size": len(rop_bytes),
        "rop_sha256": rop_sha256,
        "tar_file": os.path.basename(tar_path),
        "tar_size": len(tar_bytes),
        "tar_sha256": tar_sha256,
    }


def main():
    parser = argparse.ArgumentParser(description="ROS Package Builder")
    parser.add_argument("--name", required=True, help="Package name")
    parser.add_argument("--version", required=True, help="Package version")
    parser.add_argument("--description", required=True, help="Package description")
    parser.add_argument("--arch", default="x86_64", help="Architecture (default: x86_64)")
    parser.add_argument("--deps", default="", help="Comma-separated dependencies")
    parser.add_argument("--out", default="pool", help="Output directory")
    args = parser.parse_args()

    deps = [d.strip() for d in args.deps.split(",") if d.strip()]
    print(f"Building package {args.name}-{args.version} for {args.arch}...")


if __name__ == "__main__":
    main()
