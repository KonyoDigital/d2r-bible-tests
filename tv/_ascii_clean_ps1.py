# One-shot: strip non-ASCII from Windows PowerShell scripts + UTF-8 BOM (PS 5.1 safe)
from pathlib import Path

REPL = {
    "\u2014": "-",
    "\u2013": "-",
    "\u2012": "-",
    "\u2011": "-",
    "\u2026": "...",
    "\u00b7": " - ",
    "\u2192": "->",
    "\u2018": "'",
    "\u2019": "'",
    "\u201c": '"',
    "\u201d": '"',
    "\u00a0": " ",
    "\u2500": "-",
    "\u2501": "-",
    "\u2550": "=",
}


def ascii_clean(s: str) -> str:
    for a, b in REPL.items():
        s = s.replace(a, b)
    return "".join(ch if ord(ch) < 128 else "" for ch in s)


def main() -> None:
    root = Path(__file__).resolve().parent
    for name in ("start_tvd_win.ps1", "install-tvd.ps1"):
        p = root / name
        raw = p.read_text(encoding="utf-8", errors="replace")
        clean = ascii_clean(raw)
        p.write_bytes(("\ufeff" + clean).encode("utf-8"))
        non = sum(1 for c in clean if ord(c) > 127)
        print(f"{name}: non_ascii={non} bytes={p.stat().st_size}")


if __name__ == "__main__":
    main()
