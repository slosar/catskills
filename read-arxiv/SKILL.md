---
name: read-arxiv
description: Read arXiv papers by downloading and unpacking their LaTeX source instead of scraping the HTML or extracting the PDF. Use this whenever a user points at an arXiv paper in any form — an arxiv.org/abs, /pdf or /html link, an ar5iv or alphaxiv link, a bare identifier like 2401.12345 or astro-ph/0605001, or just a title plus "look this paper up" — and wants it read, summarized, checked, compared against another paper, or wants its equations, tables, derivations, assumptions, numbers or figures extracted. Also use it when a paper has already been fetched as HTML or PDF but the equations, tables or notation matter, since the source is authoritative and the renderings are lossy.
---

# Reading arXiv papers from LaTeX source

arXiv distributes the author's original LaTeX for nearly every submission. Get that
instead of a rendering. The workflow is: **identifier → `/e-print/` → unpack → read the
`.tex`**.

## Why the source and not the rendering

- **PDF text extraction is lossy in exactly the places that matter.** Two-column layouts
  interleave, sub/superscripts flatten (`σ_8` becomes `σ8` or `σ 8`), math becomes
  glyph soup, and table cells lose their column association. A number read out of a
  mangled table is worse than no number.
- **The `/html/` and ar5iv renderings are LaTeXML conversions** that silently drop or
  garble macro-heavy math, custom environments, and some tables. They exist for
  accessibility, not fidelity, and not every paper has one.
- **The source has things no rendering does**: macro definitions that fix notation,
  exact table values, `\label`/`\ref` structure, author comments, and the `.bbl` with
  full reference strings.
- It is also usually *smaller* than the PDF and far cheaper to read selectively with
  `grep` and ranged reads.

## Step 1 — Canonicalize the reference to an identifier

Every arXiv URL form contains the identifier; pull it out and discard the rest.

| Input | Identifier |
|---|---|
| `arxiv.org/abs/2401.12345` | `2401.12345` |
| `arxiv.org/pdf/2401.12345v2` | `2401.12345v2` |
| `arxiv.org/html/2401.12345v1`, `browse.arxiv.org/html/...` | `2401.12345v1` |
| `ar5iv.labs.arxiv.org/html/1809.06635`, `ar5iv.org/abs/...` | `1809.06635` |
| `alphaxiv.org/abs/2405.00123`, `huggingface.co/papers/2405.00123` | `2405.00123` |
| `arxiv.org/abs/astro-ph/0605001` (pre-2007 style) | `astro-ph/0605001` |

Keep the version suffix if the user gave one — versions differ, and a claim checked
against v1 may not be in v3. Without a suffix you get the latest version.

The source URL is then `https://arxiv.org/e-print/<identifier>`. Note there is no file
extension: what comes back is a bare blob whose type you have to sniff.

If the user gave only a title or author, resolve it first with the arXiv API
(`http://export.arxiv.org/api/query?search_query=ti:"..."&max_results=5`) or a web
search, confirm you have the right paper, then proceed.

## Step 2 — Download and unpack

Use the bundled script; it handles every case below in one shot and caches into
`/tmp/arxiv/<id>/` so re-reading a paper costs nothing:

```bash
python3 ~/.claude/skills/read-arxiv/scripts/fetch_arxiv_source.py <url-or-id>
# optional: --dest DIR   --mirror export.arxiv.org   --flatten /tmp/whole_paper.tex
```

It prints the unpack directory, the main `.tex`, the other `.tex` files, the
bibliography, local `.sty`/`.cls`, and the figure list. `--flatten` writes a single file
with `\input`/`\include` inlined, which is convenient for reading a paper end to end.

If you would rather do it by hand, the pitfalls to respect are:

```bash
mkdir -p /tmp/arxiv/2401.12345 && cd /tmp/arxiv/2401.12345
curl -sL -A "arxiv-source-reader" -o src https://arxiv.org/e-print/2401.12345
file src                     # decide what you actually got
tar xzf src || gunzip -c src > main.tex
```

- **Always unpack into a dedicated directory.** Many submissions are flat tarballs with
  no top-level folder and will strew fifty files across your working directory.
- **`curl -L` is required**; `/e-print/` redirects.
- The blob may be a gzipped tar, a gzipped single `.tex`, a plain tar, or a **PDF**
  (some authors submit PDF-only — then no source exists, and you fall back to reading
  the PDF properly, e.g. with the `pdf-reading` skill).
- An HTML payload means an error or rate-limit page, not a paper.
- If egress is restricted in your sandbox, `arxiv.org` may need to be allowlisted. Say
  so plainly rather than silently falling back to a worse source.

## Step 3 — Orient before reading

Find the main file: it is the one with `\documentclass` *and* `\begin{document}`. If
`00README.json` or `00README.XXX` is present, it names the top-level file explicitly and
overrides your guess. `main.tex`, `ms.tex`, `paper.tex` are common names but not
reliable — long papers often split into `sec_intro.tex`, `results.tex`, and so on, pulled
in via `\input`.

```bash
grep -rl '\\begin{document}' . --include='*.tex'
grep -n '\\\(input\|include\)' ms.tex        # the reading order of the sections
wc -l *.tex
```

Then read the preamble first, whole. It tells you the journal class (which sets the
paper's conventions), the packages, and — most importantly — the `\newcommand` /
`\def` block. Papers routinely define `\sigeight`, `\Msun`, `\lcdm`, `\eq`. If you read
the body without those definitions you will misread the notation, and macro names are
frequently *not* self-explanatory. Local `.sty` files can hold more of them.

## Step 4 — Read the body

For a short paper, read the flattened file straight through. For a long one, work
section by section: `grep -n '\\section\|\\subsection'` to get the map, then ranged
reads. Things worth knowing while you do:

- **`%` comments are not the paper.** Source often contains deleted paragraphs, referee
  notes, alternative wordings, and TODOs. They are genuinely informative about what the
  authors considered, but never attribute a commented-out claim to the published text.
  If you use one, say it came from a comment.
- **The bibliography is usually `.bbl`, not `.bib`.** arXiv submissions include the
  compiled `.bbl` because the `.bib` isn't needed for compilation. Resolve `\cite{...}`
  keys against it. If neither is present, the references are inline in a
  `thebibliography` environment.
- **Tables are exact in the source** — this is the single biggest advantage over PDF
  extraction. Read `tabular` bodies directly, minding `\\` row breaks, `&` separators,
  `\multicolumn`, and units stated in the header.
- **Equations come with their labels.** Reporting "Eq. (12)" is only right if you count
  numbered environments the way LaTeX does; prefer citing by `\label` name or by
  quoting the equation itself.
- **Figures are not readable as text**, but they are sitting right there as `.pdf`,
  `.png` or `.eps` files. Captions plus the surrounding discussion usually suffice; when
  they don't, rasterize the figure and look at it — see the next section.
- **Don't stop at `\end{document}`-adjacent sections.** Appendices frequently hold the
  derivation, the systematics budget, or the caveats that the abstract soft-pedals.

Reproduce equations in LaTeX when the user is technical; that is lossless and they can
paste it. Keep verbatim prose quotation short and attributed — the source is copyrighted
by its authors.

## Step 5 — Look at the figures when they carry the argument

Don't paraphrase a caption and pretend you've seen the plot. If the figure is where the
result actually lives, open it. Cases that warrant it: the user asks what a figure shows
or asks you to describe or reproduce it; the text asserts agreement, a trend, a
detection or a null result that is only demonstrated visually; you need a value the text
never states (a turnover scale, where curves cross, the size of a residual); the caption
is terse or refers to panels the text never walks through; or something in the text looks
inconsistent and the figure would settle it.

Find the file the `\includegraphics` actually points at — it is often extensionless in
the source, may live under a `\graphicspath` directory, and the caption order in the
`.tex` need not match the filenames:

```bash
grep -n 'includegraphics\|graphicspath' ms.tex
```

Then rasterize just that file and view it with your image-viewing tool:

```bash
pdftoppm -png -r 150 figs/f3.pdf /tmp/f3        # vector PDF -> /tmp/f3-1.png
pdftocairo -png -r 150 figs/f3.pdf /tmp/f3      # equivalent, also poppler
convert -density 200 figs/f3.eps /tmp/f3.png    # EPS/PS, needs ImageMagick + ghostscript
```

`.png`/`.jpg` figures need no conversion — view them as they are. If the tools are
missing, `apt-get install -y poppler-utils` (or `ghostscript` for EPS) is usually enough;
if the sandbox forbids that, say so rather than guessing at the figure's content.

Practical notes:

- 150 dpi is a good default. Go to 300 for a dense multi-panel figure or when you need to
  read small tick labels; low resolution is the usual reason a plot looks unreadable.
- Multi-panel figures are frequently *one* file with panels (a), (b), (c) — check the
  caption's panel labels against what you see before attributing a claim to the wrong
  panel.
- Reading numbers off a plot is interpolation, not measurement. Say "roughly 0.3" and
  say that you read it off the figure, and prefer a number stated in the text or a table
  whenever one exists.
- A few papers ship figures as raw data plus a plotting script, or as TikZ/PGFPlots code
  inline in the `.tex`. That is better than an image: read the data or the code directly.

## Etiquette and limits

One `/e-print/` request per paper, reuse the cached unpack, and leave a few seconds
between papers if you're fetching several. Don't loop over large identifier lists —
arXiv publishes bulk-access channels for that. Use `export.arxiv.org` as the host if
`arxiv.org` rate-limits you.

Two things this workflow cannot give you: papers whose authors submitted PDF only, and
papers withdrawn or on hold (the e-print may be a stub). In both cases say so instead of
quietly substituting the abstract page for the paper.
