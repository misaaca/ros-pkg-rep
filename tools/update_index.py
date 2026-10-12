#!/usr/bin/env python3
"""
ROS Package Repository Index Generator
Scans pool/ and kernel/ to generate Packages.toml, Packages.json, repo.toml,
and gzip-compressed index files.
"""

import os
import sys
import json
import gzip
import hashlib
from typing import List, Dict, Any
from rop import RopArchive

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POOL_DIR = os.path.join(REPO_ROOT, "pool")
KERNEL_DIR = os.path.join(REPO_ROOT, "kernel")


def sha256_file(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def update_indices():
    print("=" * 70)
    print("Updating Repository Indices for ROS-PKG-REP")
    print("=" * 70)

    packages: List[Dict[str, Any]] = []

    # 1. Scan pool/
    for section in sorted(os.listdir(POOL_DIR)):
        sec_path = os.path.join(POOL_DIR, section)
        if not os.path.isdir(sec_path):
            continue

        for fname in sorted(os.listdir(sec_path)):
            if not fname.endswith(".rop"):
                continue

            rop_path = os.path.join(sec_path, fname)
            tar_fname = fname[:-4] + ".tar.gz"
            tar_path = os.path.join(sec_path, tar_fname)

            with open(rop_path, "rb") as f:
                rop_data = f.read()

            archive = RopArchive.parse(rop_data)
            manifest = archive.manifest

            rop_sha = hashlib.sha256(rop_data).hexdigest()
            rop_size = len(rop_data)

            tar_sha = sha256_file(tar_path) if os.path.exists(tar_path) else ""
            tar_size = os.path.getsize(tar_path) if os.path.exists(tar_path) else 0

            pkg_entry = {
                "name": manifest.name,
                "version": manifest.version,
                "section": section,
                "arch": manifest.arch,
                "description": manifest.description,
                "installed_size": manifest.installed_size,
                "dependencies": manifest.dependencies,
                "files": manifest.files,
                "rop": {
                    "filename": f"pool/{section}/{fname}",
                    "size": rop_size,
                    "sha256": rop_sha,
                },
                "tar": {
                    "filename": f"pool/{section}/{tar_fname}" if tar_sha else "",
                    "size": tar_size,
                    "sha256": tar_sha,
                },
            }
            packages.append(pkg_entry)
            print(f"Indexed: {manifest.name} v{manifest.version} ({section}) - {rop_size} bytes")

    # 2. Scan kernel/
    kernel_entry = {}
    if os.path.exists(KERNEL_DIR):
        for kfile in sorted(os.listdir(KERNEL_DIR), reverse=True):
            if kfile.startswith("ros_kernel-") and not kfile.endswith(".sha256") and not kfile.endswith(".toml"):
                kpath = os.path.join(KERNEL_DIR, kfile)
                k_sha = sha256_file(kpath)
                k_size = os.path.getsize(kpath)

                # e.g., ros_kernel-v0.3.29-rumi
                parts = kfile.split("-")
                ver = parts[1].lstrip("v") if len(parts) > 1 else "0.3.29"
                codename = parts[2] if len(parts) > 2 else "rumi"

                kernel_entry = {
                    "name": "ros_kernel",
                    "version": ver,
                    "codename": codename,
                    "arch": "x86_64",
                    "filename": f"kernel/{kfile}",
                    "size": k_size,
                    "sha256": k_sha,
                    "release_date": "2026-10-12",
                    "changelog": "OpenSSH Production Fix: RFC 8032 Ed25519 host key signatures, RFC 8439 Poly1305 26-bit limbs, ChaCha20 packet padding alignment, remote exec & interactive shell.",
                }

                # Update kernel-latest.sha256
                with open(os.path.join(KERNEL_DIR, "kernel-latest.sha256"), "w") as f:
                    f.write(f"{k_sha}  {kfile}\n")

                # Update kernel/kernel.toml
                with open(os.path.join(KERNEL_DIR, "kernel.toml"), "w") as f:
                    f.write(
                        f"[kernel]\n"
                        f'name = "{kernel_entry["name"]}"\n'
                        f'version = "{kernel_entry["version"]}"\n'
                        f'codename = "{kernel_entry["codename"]}"\n'
                        f'arch = "{kernel_entry["arch"]}"\n'
                        f'filename = "{kernel_entry["filename"]}"\n'
                        f'size = {kernel_entry["size"]}\n'
                        f'sha256 = "{kernel_entry["sha256"]}"\n'
                        f'release_date = "{kernel_entry["release_date"]}"\n'
                        f'changelog = "{kernel_entry["changelog"]}"\n'
                    )
                print(f"Indexed Kernel: {kfile} (v{ver}-{codename}) - {k_size} bytes - {k_sha[:16]}...")
                break

    # 3. Generate Packages.json
    index_json = {
        "repository": "ros-official",
        "description": "Official Package Repository for ROS (Rust Operating System)",
        "upstream_url": "https://raw.githubusercontent.com/misaaca/ros-pkg-rep/main",
        "total_packages": len(packages),
        "kernel": kernel_entry,
        "packages": packages,
    }
    json_path = os.path.join(REPO_ROOT, "Packages.json")
    with open(json_path, "w") as f:
        json.dump(index_json, f, indent=2)

    # 4. Generate Packages.toml
    toml_lines = [
        "# Official ROS Master Package Index",
        '[repository]',
        'name = "ros-official"',
        'description = "Official Package Repository for ROS (Rust Operating System)"',
        'url = "https://raw.githubusercontent.com/misaaca/ros-pkg-rep/main"',
        f'package_count = {len(packages)}',
        '',
    ]
    if kernel_entry:
        toml_lines.extend([
            "[kernel]",
            f'name = "{kernel_entry["name"]}"',
            f'version = "{kernel_entry["version"]}"',
            f'codename = "{kernel_entry["codename"]}"',
            f'arch = "{kernel_entry["arch"]}"',
            f'filename = "{kernel_entry["filename"]}"',
            f'size = {kernel_entry["size"]}',
            f'sha256 = "{kernel_entry["sha256"]}"',
            f'release_date = "{kernel_entry["release_date"]}"',
            f'changelog = "{kernel_entry["changelog"]}"',
            '',
        ])

    for pkg in packages:
        deps_str = ", ".join(f'"{d}"' for d in pkg["dependencies"])
        toml_lines.extend([
            f'[[package]]',
            f'name = "{pkg["name"]}"',
            f'version = "{pkg["version"]}"',
            f'section = "{pkg["section"]}"',
            f'arch = "{pkg["arch"]}"',
            f'description = "{pkg["description"]}"',
            f'installed_size = {pkg["installed_size"]}',
            f'dependencies = [{deps_str}]',
            f'filename = "{pkg["rop"]["filename"]}"',
            f'size = {pkg["rop"]["size"]}',
            f'sha256 = "{pkg["rop"]["sha256"]}"',
            f'tar_filename = "{pkg["tar"]["filename"]}"',
            f'tar_size = {pkg["tar"]["size"]}',
            f'tar_sha256 = "{pkg["tar"]["sha256"]}"',
            '',
        ])

    toml_content = "\n".join(toml_lines)
    toml_path = os.path.join(REPO_ROOT, "Packages.toml")
    with open(toml_path, "w") as f:
        f.write(toml_content)

    # 5. Generate gzip compressed Packages.gz
    gz_path = os.path.join(REPO_ROOT, "Packages.gz")
    with gzip.open(gz_path, "wb") as f:
        f.write(toml_content.encode("utf-8"))

    # 6. Generate repo.toml
    repo_toml_content = f"""[repository]
name = "ros-official"
description = "Official Package Repository for ROS (Rust Operating System)"
maintainer = "Mohammad <m.isaac.ahmadi@gmail.com>"
origin = "misaaca/ros-pkg-rep"
url = "https://raw.githubusercontent.com/misaaca/ros-pkg-rep/main"
default_branch = "main"
architectures = ["x86_64"]
sections = ["python", "nodejs", "rust", "system", "kernel"]
packages_index = "Packages.toml"
packages_json = "Packages.json"
packages_gz = "Packages.gz"
signing_enabled = true
"""
    with open(os.path.join(REPO_ROOT, "repo.toml"), "w") as f:
        f.write(repo_toml_content)

    print("Generated:")
    print(f"  - {json_path}")
    print(f"  - {toml_path}")
    print(f"  - {gz_path}")
    print(f"  - {os.path.join(REPO_ROOT, 'repo.toml')}")
    print("=" * 70)


if __name__ == "__main__":
    update_indices()
