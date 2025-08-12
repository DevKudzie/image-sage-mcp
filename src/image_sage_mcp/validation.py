from __future__ import annotations

import ipaddress
import os
import socket
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse


PRIVATE_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("::1/128"),
]


@dataclass
class ValidationResult:
    ok: bool
    message: Optional[str] = None


class URLValidator:
    def validate_url(self, url: str) -> ValidationResult:
        parsed = urlparse(url)
        if parsed.scheme in {"http", "https"}:
            if not parsed.netloc:
                return ValidationResult(False, "Missing host in URL")
            if not self.is_safe_url(url):
                return ValidationResult(False, "URL points to a private or unsafe address")
            return ValidationResult(True)
        elif parsed.scheme == "file" or (parsed.scheme == "" and (url.startswith("/") or ":\\" in url)):
            path = parsed.path if parsed.scheme == "file" else url
            if not self.check_file_permissions(path):
                return ValidationResult(False, "File access denied or path invalid")
            return ValidationResult(True)
        else:
            return ValidationResult(False, "Unsupported URL scheme")

    def is_safe_url(self, url: str) -> bool:
        parsed = urlparse(url)
        try:
            addr_info = socket.getaddrinfo(parsed.hostname, None)
        except socket.gaierror:
            return False
        for family, _, _, _, sockaddr in addr_info:
            ip_str: Optional[str] = None
            if family == socket.AF_INET:
                ip_str = sockaddr[0]
            elif family == socket.AF_INET6:
                ip_str = sockaddr[0]
            if not ip_str:
                continue
            ip_obj = ipaddress.ip_address(ip_str)
            if any(ip_obj in net for net in PRIVATE_NETWORKS):
                return False
        return True

    def check_file_permissions(self, path: str) -> bool:
        # Restrict to current working directory subtree by default
        try:
            abs_path = os.path.abspath(path)
            cwd = os.path.abspath(os.getcwd())
            return abs_path.startswith(cwd) and os.path.exists(abs_path) and os.path.isfile(abs_path)
        except Exception:
            return False


