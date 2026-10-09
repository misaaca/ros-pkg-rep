#!/usr/bin/env python3
"""
ROS Package Archive (.rop) Module
Tamper-evident, high-performance binary package format for the ROS operating system.

Binary Container Layout:
┌────────────────────────────────────────────────────────────────┐
│ Header (56 bytes): Magic b"ROP\x01", Version, Offsets, SHA-256 │
├────────────────────────────────────────────────────────────────┤
│ Manifest Section: TOML metadata (name, version, deps, files)   │
├────────────────────────────────────────────────────────────────┤
│ Payload Section: Packed files with path, mode, sha256 & data   │
└────────────────────────────────────────────────────────────────┘
"""

import struct
import hashlib
from typing import List, Dict, Any, Optional

ROP_MAGIC = b"ROP\x01"
ROP_FORMAT_VERSION = 1
ROP_HEADER_SIZE = 56


class RopFile:
    def __init__(self, path: str, mode: int, content: bytes):
        self.path = path.strip()
        self.mode = mode
        self.content = content
        self.sha256_hash = hashlib.sha256(content).digest()
        self.size = len(content)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "mode": oct(self.mode),
            "size": self.size,
            "sha256": self.sha256_hash.hex(),
        }


class RopManifest:
    def __init__(
        self,
        name: str,
        version: str,
        description: str,
        arch: str = "x86_64",
        installed_size: int = 0,
        dependencies: Optional[List[str]] = None,
        files: Optional[List[str]] = None,
        sha256_hash: str = "",
    ):
        self.name = name.strip()
        self.version = version.strip()
        self.description = description.strip()
        self.arch = arch.strip()
        self.installed_size = installed_size
        self.dependencies = dependencies or []
        self.files = files or []
        self.sha256_hash = sha256_hash

    def to_toml(self) -> str:
        deps_str = ", ".join(f'"{d}"' for d in self.dependencies)
        files_str = ", ".join(f'"{f}"' for f in self.files)
        return (
            f"[package]\n"
            f'name = "{self.name}"\n'
            f'version = "{self.version}"\n'
            f'description = "{self.description}"\n'
            f'arch = "{self.arch}"\n'
            f"installed_size = {self.installed_size}\n"
            f'sha256 = "{self.sha256_hash}"\n'
            f"dependencies = [{deps_str}]\n\n"
            f"[files]\n"
            f"files = [{files_str}]\n"
        )

    @classmethod
    def parse(cls, toml_str: str) -> "RopManifest":
        data = {
            "name": "",
            "version": "",
            "description": "",
            "arch": "x86_64",
            "installed_size": 0,
            "dependencies": [],
            "files": [],
            "sha256_hash": "",
        }
        for line in toml_str.splitlines():
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("["):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip()
                if k == "name":
                    data["name"] = v.strip('"\'')
                elif k == "version":
                    data["version"] = v.strip('"\'')
                elif k == "description":
                    data["description"] = v.strip('"\'')
                elif k == "arch":
                    data["arch"] = v.strip('"\'')
                elif k in ("installed_size", "size"):
                    data["installed_size"] = int(v.strip('"\'') or 0)
                elif k == "sha256":
                    data["sha256_hash"] = v.strip('"\'')
                elif k in ("dependencies", "deps"):
                    inner = v.strip("[]")
                    data["dependencies"] = [x.strip().strip('"\'') for x in inner.split(",") if x.strip()]
                elif k == "files":
                    inner = v.strip("[]")
                    data["files"] = [x.strip().strip('"\'') for x in inner.split(",") if x.strip()]

        if not data["name"]:
            raise ValueError("Manifest missing mandatory 'name'")
        if not data["version"]:
            raise ValueError("Manifest missing mandatory 'version'")
        return cls(**data)


class RopArchive:
    def __init__(self, manifest: RopManifest, files: List[RopFile]):
        self.manifest = manifest
        self.files = files

    def pack(self) -> bytes:
        self.manifest.files = [f.path for f in self.files]
        self.manifest.installed_size = sum(len(f.content) for f in self.files)

        payload = bytearray()
        payload.extend(struct.pack("<H", len(self.files)))
        for f in self.files:
            p_bytes = f.path.encode("utf-8")
            payload.extend(struct.pack("<H", len(p_bytes)))
            payload.extend(p_bytes)
            payload.extend(struct.pack("<I", f.mode))
            payload.extend(struct.pack("<I", len(f.content)))
            payload.extend(f.sha256_hash)
            payload.extend(f.content)

        payload_bytes = bytes(payload)

        manifest_str = self.manifest.to_toml()
        manifest_bytes = manifest_str.encode("utf-8")

        combined = manifest_bytes + payload_bytes
        archive_checksum = hashlib.sha256(combined).digest()

        manifest_offset = ROP_HEADER_SIZE
        manifest_len = len(manifest_bytes)
        payload_offset = manifest_offset + manifest_len
        payload_len = len(payload_bytes)

        header = struct.pack(
            "<4sHHIIII32s",
            ROP_MAGIC,
            ROP_FORMAT_VERSION,
            0,
            manifest_offset,
            manifest_len,
            payload_offset,
            payload_len,
            archive_checksum,
        )

        return header + combined

    @classmethod
    def parse(cls, data: bytes) -> "RopArchive":
        if len(data) < ROP_HEADER_SIZE:
            raise ValueError(f"Data too short: {len(data)} < {ROP_HEADER_SIZE}")

        magic, version, flags, m_offset, m_len, p_offset, p_len, checksum = struct.unpack(
            "<4sHHIIII32s", data[:ROP_HEADER_SIZE]
        )

        if magic != ROP_MAGIC:
            raise ValueError(f"Invalid ROP magic: {magic}")
        if version != ROP_FORMAT_VERSION:
            raise ValueError(f"Unsupported ROP version: {version}")

        if m_offset + m_len > len(data) or p_offset + p_len > len(data):
            raise ValueError("Corrupt ROP offsets exceed file size")

        manifest_bytes = data[m_offset : m_offset + m_len]
        payload_bytes = data[p_offset : p_offset + p_len]

        computed_checksum = hashlib.sha256(manifest_bytes + payload_bytes).digest()
        if computed_checksum != checksum:
            raise ValueError("Integrity check failed: overall archive SHA256 mismatch")

        manifest = RopManifest.parse(manifest_bytes.decode("utf-8"))

        if len(payload_bytes) < 2:
            raise ValueError("Payload missing file count")
        file_count = struct.unpack("<H", payload_bytes[:2])[0]
        offset = 2
        files: List[RopFile] = []

        for _ in range(file_count):
            if offset + 2 > len(payload_bytes):
                raise ValueError("Corrupt payload: truncated path length")
            path_len = struct.unpack("<H", payload_bytes[offset : offset + 2])[0]
            offset += 2

            if offset + path_len + 40 > len(payload_bytes):
                raise ValueError("Corrupt payload: truncated file header")
            path_str = payload_bytes[offset : offset + path_len].decode("utf-8")
            offset += path_len

            mode, file_size, expected_hash = struct.unpack(
                "<II32s", payload_bytes[offset : offset + 40]
            )
            offset += 40

            if offset + file_size > len(payload_bytes):
                raise ValueError("Corrupt payload: truncated file content")
            content = payload_bytes[offset : offset + file_size]
            offset += file_size

            actual_hash = hashlib.sha256(content).digest()
            if actual_hash != expected_hash:
                raise ValueError(f"File integrity mismatch for {path_str}")

            files.append(RopFile(path_str, mode, content))

        return cls(manifest, files)
