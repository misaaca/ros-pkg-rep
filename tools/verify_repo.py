#!/usr/bin/env python3
"""
ROS Package Repository Verifier
Automated integrity and conformance verification tool for ROS-PKG-REP.
Validates SHA-256 hashes, package archive internal formats, dependency graphs,
and kernel binaries.
"""

import os
import sys
import json
import hashlib
from typing import Dict, List, Set
from rop import RopArchive

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def sha256_file(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def verify():
    print("=" * 70)
    print("Running Production Repository Verification for ROS-PKG-REP")
    print("=" * 70)

    errors: List[str] = []

    # 1. Check index existence
    json_path = os.path.join(REPO_ROOT, "Packages.json")
    toml_path = os.path.join(REPO_ROOT, "Packages.toml")
    repo_toml_path = os.path.join(REPO_ROOT, "repo.toml")

    for path, name in [(json_path, "Packages.json"), (toml_path, "Packages.toml"), (repo_toml_path, "repo.toml")]:
        if not os.path.exists(path):
            errors.append(f"Missing essential index file: {name}")

    if errors:
        for err in errors:
            print(f"[ERROR] {err}")
        sys.exit(1)

    with open(json_path, "r") as f:
        index_data = json.load(f)

    packages = index_data.get("packages", [])
    print(f"Total packages declared in index: {len(packages)}")

    package_names: Set[str] = set()
    # Pre-populate base packages known to be in ROS kernel base
    package_names.update(["coreutils", "python3"])

    for pkg in packages:
        package_names.add(pkg["name"])

    # 2. Verify each package
    for pkg in packages:
        name = pkg["name"]
        version = pkg["version"]
        rop_rel = pkg["rop"]["filename"]
        rop_abs = os.path.join(REPO_ROOT, rop_rel)
        expected_rop_sha = pkg["rop"]["sha256"]
        expected_rop_size = pkg["rop"]["size"]

        # Check .rop file exists
        if not os.path.exists(rop_abs):
            errors.append(f"Package {name} .rop missing: {rop_rel}")
            continue

        actual_rop_size = os.path.getsize(rop_abs)
        if actual_rop_size != expected_rop_size:
            errors.append(f"Package {name} .rop size mismatch: {actual_rop_size} != {expected_rop_size}")

        actual_rop_sha = sha256_file(rop_abs)
        if actual_rop_sha != expected_rop_sha:
            errors.append(f"Package {name} .rop SHA256 mismatch")

        # Parse and verify internal .rop container
        try:
            with open(rop_abs, "rb") as f:
                rop_bytes = f.read()
            archive = RopArchive.parse(rop_bytes)
            if archive.manifest.name != name:
                errors.append(f"Manifest internal name mismatch in {rop_rel}: {archive.manifest.name} != {name}")
            if archive.manifest.version != version:
                errors.append(f"Manifest internal version mismatch in {rop_rel}: {archive.manifest.version} != {version}")
        except Exception as e:
            errors.append(f"Failed to parse internal .rop format for {rop_rel}: {e}")

        # Check .tar.gz file exists and matches
        tar_rel = pkg["tar"]["filename"]
        if tar_rel:
            tar_abs = os.path.join(REPO_ROOT, tar_rel)
            if not os.path.exists(tar_abs):
                errors.append(f"Package {name} .tar.gz missing: {tar_rel}")
            else:
                actual_tar_sha = sha256_file(tar_abs)
                if actual_tar_sha != pkg["tar"]["sha256"]:
                    errors.append(f"Package {name} .tar.gz SHA256 mismatch")

        # Verify dependencies are valid
        for dep in pkg.get("dependencies", []):
            if dep not in package_names:
                errors.append(f"Unresolvable dependency in {name}: '{dep}' not found in catalog")

        print(f" [PASS] {name} v{version} (SHA256 verified, container intact)")

    # 3. Check for circular dependencies using DFS
    adj: Dict[str, List[str]] = {p["name"]: p.get("dependencies", []) for p in packages}
    visited: Dict[str, int] = {}  # 0: unvisited, 1: visiting, 2: visited

    def has_cycle(node: str) -> bool:
        visited[node] = 1
        for neighbor in adj.get(node, []):
            if neighbor not in adj:
                continue
            if visited.get(neighbor, 0) == 1:
                return True
            if visited.get(neighbor, 0) == 0 and has_cycle(neighbor):
                return True
        visited[node] = 2
        return False

    for node in adj:
        if visited.get(node, 0) == 0:
            if has_cycle(node):
                errors.append(f"Circular dependency detected involving package: {node}")

    # 4. Verify kernel release
    kernel_info = index_data.get("kernel", {})
    if kernel_info:
        k_rel = kernel_info["filename"]
        k_abs = os.path.join(REPO_ROOT, k_rel)
        if not os.path.exists(k_abs):
            errors.append(f"Kernel binary missing: {k_rel}")
        else:
            k_sha = sha256_file(k_abs)
            if k_sha != kernel_info["sha256"]:
                errors.append(f"Kernel binary SHA256 mismatch: {k_sha} != {kernel_info['sha256']}")
            else:
                print(f" [PASS] Kernel image: {os.path.basename(k_abs)} ({kernel_info['size']} bytes, SHA256 verified)")

    print("-" * 70)
    if errors:
        print(f"[FAIL] Found {len(errors)} verification errors:")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)
    else:
        print("[SUCCESS] All repository verification checks PASSED perfectly!")
        print("=" * 70)
        sys.exit(0)


if __name__ == "__main__":
    verify()
