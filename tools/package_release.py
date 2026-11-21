"""Đóng gói bản chạy từ mã nguồn và asset, không cần GitHub hay .git."""

import argparse
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parent.parent
VERSION = "1.0.0"
FILES = ("game.contract.json", "README.md", "CREDITS.md", "LICENSE", "CHANGELOG.md",
         "RELEASE_NOTES.md", "chonoi", "cho-noi-assets", "tests", "tools", "docs/members",
         "docs/contracts", "docs/adr", "docs/verification", "docs/plan", "docs/proof",
         "docs/ai-usage-log.md", "docs/clarify.md", "docs/retro.md", "TEAM.md",
         "TICKET-02.md", "TICKET-03.md", "TICKET-04.md")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    sources = []
    for name in FILES:
        path = ROOT / name
        if not path.exists():
            parser.error(f"Thiếu nội dung cần đóng gói: {name}")
        sources.extend(path.rglob("*") if path.is_dir() else [path])
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(args.out, "w", compression=ZIP_DEFLATED) as archive:
        for path in sorted(sources):
            if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
                name = f"cho-noi-v{VERSION}/{path.relative_to(ROOT).as_posix()}"
                entry = ZipInfo(name)
                archive.writestr(entry, path.read_bytes(), compress_type=ZIP_DEFLATED)
    print(args.out)


if __name__ == "__main__":
    main()
