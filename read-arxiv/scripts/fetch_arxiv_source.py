#!/usr/bin/env python3
"""Fetch, unpack and inspect the LaTeX source of an arXiv paper.

Usage:
    python3 fetch_arxiv_source.py <arxiv-url-or-id> [--dest DIR] [--flatten OUT.tex]

Accepts anything that contains an arXiv identifier: /abs/, /pdf/, /html/,
/format/, ar5iv or alphaxiv links, or a bare id (2401.12345v2, hep-th/9901001).

Prints a manifest: where the source was unpacked, which file is the main
document, the other .tex files, the bibliography, and the figures.
Stdlib only; no network libraries beyond urllib.

Plays nice with arXiv's robot policy (https://info.arxiv.org/help/robots.html):
fetches from export.arxiv.org, the host set aside for programmatic access, and
spaces requests at least one second apart across all concurrent invocations
(well inside the "bursts of 4 per second, then sleep 1 second" guideline).
"""

import argparse
import gzip
import io
import json
import os
import re
import sys
import tarfile
import time
import urllib.error
import urllib.request

try:
    import fcntl
except ImportError:  # non-POSIX: throttle within this process only
    fcntl = None

UA = "arxiv-source-reader/1.0 (LaTeX source reading; one paper per request)"

CACHE_ROOT = "/tmp/arxiv"
DEFAULT_HOST = "export.arxiv.org"
# Minimum spacing between request starts, shared by every running copy of this
# script through a lock file. One per second is stricter than arXiv's guideline.
MIN_INTERVAL = 1.0
THROTTLE_FILE = os.path.join(CACHE_ROOT, ".last_request")
MAX_RETRY_WAIT = 60

NEW_ID = r"\d{4}\.\d{4,5}(?:v\d+)?"
OLD_ID = r"[a-z][a-z-]+(?:\.[A-Z]{2})?/\d{7}(?:v\d+)?"
ID_RE = re.compile(rf"({NEW_ID}|{OLD_ID})")

TEX_EXT = {".tex", ".ltx"}
FIG_EXT = {".pdf", ".png", ".jpg", ".jpeg", ".eps", ".ps", ".gif", ".svg"}
INPUT_RE = re.compile(r"^(?P<pre>[^%\n]*?)\\(?:input|include)\s*\{(?P<name>[^}]+)\}", re.M)


def extract_id(ref: str) -> str:
    m = ID_RE.search(ref.strip())
    if not m:
        sys.exit(f"No arXiv identifier found in {ref!r}")
    return m.group(1)


def throttle() -> None:
    """Block until MIN_INTERVAL has passed since the last request by any process."""
    os.makedirs(CACHE_ROOT, exist_ok=True)
    with open(THROTTLE_FILE, "a+") as f:
        if fcntl:
            fcntl.flock(f, fcntl.LOCK_EX)  # held while sleeping, so callers queue up
        f.seek(0)
        try:
            last = float(f.read().strip() or 0)
        except ValueError:
            last = 0.0
        wait = last + MIN_INTERVAL - time.time()
        if wait > 0:
            time.sleep(wait)
        f.seek(0)
        f.truncate()
        f.write(f"{time.time():.3f}")
        f.flush()


def download(arxiv_id: str, mirror: str) -> bytes:
    url = f"https://{mirror}/e-print/{arxiv_id}"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(2):
        throttle()
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            # 429/503 are arXiv asking us to back off; honour Retry-After once.
            if e.code in (429, 503) and attempt == 0:
                try:
                    wait = int(e.headers.get("Retry-After", "10"))
                except ValueError:
                    wait = 10
                if wait <= MAX_RETRY_WAIT:
                    print(f"HTTP {e.code} from {mirror}; waiting {wait}s before one retry",
                          file=sys.stderr)
                    time.sleep(wait)
                    continue
            hint = {
                403: "arXiv refused the request (blocked user agent or rate limit).",
                404: "No such paper, or the version does not exist.",
                429: "Rate limited - wait a few minutes before retrying.",
                503: "arXiv asked us to back off - wait a few minutes before retrying.",
            }.get(e.code, "")
            sys.exit(f"HTTP {e.code} fetching {url}. {hint}")
        except urllib.error.URLError as e:
            sys.exit(f"Could not reach {url}: {e.reason}. "
                     f"If this sandbox restricts egress, {mirror} may need allowlisting.")
    sys.exit(f"Giving up on {url} after a retry.")


def safe_extract(tf: tarfile.TarFile, dest: str) -> None:
    for member in tf.getmembers():
        target = os.path.realpath(os.path.join(dest, member.name))
        if not target.startswith(os.path.realpath(dest) + os.sep):
            sys.exit(f"Refusing to extract outside destination: {member.name}")
        if member.issym() or member.islnk():
            continue
    tf.extractall(dest, filter="data")


def unpack(blob: bytes, dest: str) -> str:
    """Write source into dest. Returns a short description of what it was."""
    os.makedirs(dest, exist_ok=True)

    if blob[:4] == b"%PDF":
        path = os.path.join(dest, "paper.pdf")
        with open(path, "wb") as f:
            f.write(blob)
        return ("pdf-only submission - no LaTeX source exists for this paper; "
                f"saved to {path}, read it with the pdf-reading skill")

    if blob[:2] == b"\x1f\x8b":
        raw = gzip.decompress(blob)
    else:
        raw = blob

    if raw[:6] == b"<!DOCT" or raw[:5] == b"<html":
        sys.exit("Got an HTML page instead of source - likely an error or captcha page.")

    try:
        with tarfile.open(fileobj=io.BytesIO(raw)) as tf:
            safe_extract(tf, dest)
        return "tar archive"
    except tarfile.ReadError:
        pass

    # Single (gzipped) file submission - almost always one .tex
    path = os.path.join(dest, "main.tex")
    with open(path, "wb") as f:
        f.write(raw)
    return "single-file submission"


def walk(dest: str):
    out = []
    for root, _dirs, files in os.walk(dest):
        for name in files:
            p = os.path.join(root, name)
            out.append((os.path.relpath(p, dest), p))
    return sorted(out)


def find_main(dest: str, entries) -> str | None:
    readme = os.path.join(dest, "00README.json")
    if os.path.exists(readme):
        try:
            data = json.load(open(readme))
            for src in data.get("sources", []):
                if src.get("usage") == "toplevelfile":
                    return src["filename"]
        except Exception:
            pass

    candidates = []
    for rel, path in entries:
        if os.path.splitext(rel)[1].lower() not in TEX_EXT:
            continue
        try:
            text = open(path, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        score = 0
        if re.search(r"^[^%]*\\documentclass", text, re.M):
            score += 2
        if re.search(r"^[^%]*\\begin\{document\}", text, re.M):
            score += 2
        if rel.lower() in ("main.tex", "ms.tex", "paper.tex"):
            score += 1
        if score:
            candidates.append((score, len(text), rel))
    if not candidates:
        return None
    candidates.sort(reverse=True)
    return candidates[0][2]


def resolve(dest: str, name: str) -> str | None:
    for cand in (name, name + ".tex", name + ".ltx"):
        p = os.path.join(dest, cand)
        if os.path.isfile(p):
            return p
    return None


def flatten(dest: str, main: str, out_path: str) -> None:
    def expand(rel: str, depth: int = 0) -> str:
        path = resolve(dest, rel)
        if path is None or depth > 10:
            return f"% [fetch_arxiv_source: could not inline {rel}]\n"
        text = open(path, encoding="utf-8", errors="replace").read()

        def repl(m):
            return (m.group("pre") + "\n% >>> inlined from " + m.group("name") + "\n"
                    + expand(m.group("name"), depth + 1) + "\n")

        return INPUT_RE.sub(repl, text)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(expand(main))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("ref", help="arXiv URL or identifier")
    ap.add_argument("--dest", help=f"destination directory (default {CACHE_ROOT}/<id>)")
    ap.add_argument("--mirror", default=DEFAULT_HOST,
                    help=f"host to fetch from (default {DEFAULT_HOST}, arXiv's "
                         "designated host for programmatic access)")
    ap.add_argument("--flatten", metavar="OUT.tex",
                    help="also write a copy with \\input/\\include inlined")
    args = ap.parse_args()

    arxiv_id = extract_id(args.ref)
    dest = args.dest or os.path.join(CACHE_ROOT, arxiv_id.replace("/", "_"))

    if os.path.isdir(dest) and os.listdir(dest):
        kind = "cached (already downloaded)"
    else:
        kind = unpack(download(arxiv_id, args.mirror), dest)

    entries = walk(dest)
    print(f"arXiv id:   {arxiv_id}")
    print(f"source:     {kind}")
    print(f"unpacked:   {dest}")

    if any(rel == "paper.pdf" for rel, _ in entries) and len(entries) == 1:
        return

    main_tex = find_main(dest, entries)
    print(f"main file:  {main_tex or 'UNKNOWN - inspect manually'}")

    def group(exts):
        return [rel for rel, _ in entries if os.path.splitext(rel)[1].lower() in exts]

    tex = [r for r in group(TEX_EXT) if r != main_tex]
    if tex:
        print("other tex:  " + ", ".join(tex))
    bib = group({".bbl", ".bib"})
    if bib:
        print("bibliography: " + ", ".join(bib))
    sty = group({".sty", ".cls"})
    if sty:
        print("local style: " + ", ".join(sty))
    figs = group(FIG_EXT)
    if figs:
        print(f"figures:    {len(figs)} files ({', '.join(figs[:6])}"
              f"{', ...' if len(figs) > 6 else ''})")

    if args.flatten and main_tex:
        flatten(dest, main_tex, args.flatten)
        print(f"flattened:  {args.flatten}")


if __name__ == "__main__":
    main()
