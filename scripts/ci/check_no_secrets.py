from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[2]

EXCLUDED_PARTS = {
    ".git",
    "node_modules",
    "dist",
    "venv",
    "__pycache__",
    ".pytest_cache",
}

TEXT_SUFFIXES = {
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".json",
    ".yml",
    ".yaml",
    ".env",
    ".md",
    ".txt",
    ".toml",
    ".ini",
}

PROHIBITED_PATTERNS = {
    "private_key": re.compile(
        r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"
    ),
    "github_pat": re.compile(
        r"github_pat_[A-Za-z0-9_]{20,}"
    ),
    "github_token": re.compile(
        r"gh[pousr]_[A-Za-z0-9]{20,}"
    ),
    "aws_access_key": re.compile(
        r"AKIA[0-9A-Z]{16}"
    ),
}

ALLOWLIST_FILES = {
    ".env.example",
}


def should_scan(path: Path) -> bool:
    if any(part in EXCLUDED_PARTS for part in path.parts):
        return False

    if path.name in ALLOWLIST_FILES:
        return False

    return (
        path.suffix in TEXT_SUFFIXES
        or path.name.startswith(".env")
    )


findings = []

for path in ROOT.rglob("*"):
    if not path.is_file() or not should_scan(path):
        continue

    try:
        text = path.read_text(
            encoding="utf-8",
            errors="ignore",
        )
    except OSError:
        continue

    for name, pattern in PROHIBITED_PATTERNS.items():
        if pattern.search(text):
            findings.append(
                f"{path.relative_to(ROOT)}: {name}"
            )


if findings:
    print("FAIL: possible committed secrets detected")
    for finding in findings:
        print(f" - {finding}")
    sys.exit(1)

print("PASS: no prohibited committed-secret patterns found")
