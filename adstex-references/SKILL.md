---
name: adstex-references
description: Use this skill whenever asked to fill in, add, complete, or fix bibliography/references/citations in a LaTeX (.tex) document, especially for astronomy/physics papers. This covers requests like "add the references for this paper", "fill in the citations", "generate the bibtex file", "find the ADS bibcode for this paper and cite it", or any task involving turning informal citations (author names, paper titles, arXiv IDs) into proper \cite{} commands backed by a working .bib file. Always use this skill instead of hand-writing bibtex entries from memory when the document is a LaTeX file and NASA ADS / arXiv is a plausible source — hand-written bibtex entries are frequently wrong (typos, wrong volume/page, missing DOI) and adstex generates them from the authoritative ADS record instead.
---

# Filling in LaTeX references with adstex

## What this skill does

`adstex` (https://github.com/yymao/adstex) is a command-line tool that scans a
`.tex` file for citation keys used in `\cite`-family commands, looks each one up
on NASA's Astrophysics Data System (ADS), and writes/updates a `.bib` file with
the correct bibtex entries. It does **not** search for papers by topic and it
does **not** decide what to cite — it only resolves identifiers that are
already sitting inside `\cite{...}` commands into full bibtex entries.

So the actual intellectual work — figuring out *which* papers should be cited
for a given claim or sentence — is Claude's job. `adstex` is the last mile:
turning a correct identifier into a correct, complete bibtex entry, with zero
risk of the kind of hallucinated volume/page/DOI numbers that come from
hand-writing bibtex from memory.

## Workflow

1. **Identify what needs a citation.** Read the .tex file (or the relevant
   section) and find claims/statements that need a supporting reference, or
   locate existing placeholder/incomplete `\cite{}` commands.

2. **Find the right identifier for each citation, preferring in this order:**
   - **arXiv ID** (e.g. `2404.14498`, or the older `astro-ph/0501171` style) — preferred, since it's what Claude will most often find/recall directly.
   - **ADS bibcode** (e.g. `2024ApJ...976..118G`) — 19-character fixed-format identifier, use when the arXiv ID isn't known or the paper predates arXiv.
   - Use `web_search` (and `web_fetch` on the ADS/arXiv abstract page) to confirm the correct identifier — do not guess or recall arXiv numbers from memory, they are easy to misremember and adstex will silently fetch the wrong paper if the ID is wrong.
   - DOIs and `FirstAuthor:Year` keys also work with adstex as a fallback, but are less reliable to resolve automatically (author:year triggers an interactive disambiguation prompt — see Step 4) — prefer arXiv ID or bibcode whenever available.

3. **Insert `\cite` commands using that identifier as the key**, e.g.:
   ```latex
   Recent measurements of the CMB \citep{2020A&A...641A...6P} confirm...
   As shown by \citet{2404.14498}, the effect...
   ```
   Any `\cite`-family command works (`\cite`, `\citet`, `\citep`, `\citealt`,
   etc.) — adstex recognizes all variants. Do not fabricate a bibtex entry by
   hand; just place the identifier as the key and let adstex resolve it.

4. **Run adstex** to generate/update the `.bib` file:
   ```bash
   adstex paper.tex -o paper.bib
   ```
   - Multiple `.tex` files (e.g. a main file plus `\input`-ed sections) can be
     passed at once: `adstex main.tex intro.tex results.tex -o paper.bib`.
   - If citation keys are `FirstAuthor:Year` style rather than identifiers,
     adstex will run interactively, prompting to pick from a list of ADS
     search candidates — this requires a human in the loop, so give the user
     the prompt output rather than trying to answer it yourself. This is one
     more reason to prefer arXiv ID/bibcode keys, which resolve non-interactively.
   - If a `.bib` file already exists at the `-o` path, adstex only fetches
     entries for new/changed keys and leaves the rest untouched (a backup of
     the old file is made automatically unless `--no-backup` is passed).
   - See `references/adstex-reference.md` for the full option list
     (`--no-update`, `--no-backup`, `-r` for extra reference `.bib` files to
     check against, `--include-physics`, `--parallel`, etc.) and troubleshooting
     (missing API token, SSL errors, Overleaf usage).

5. **Check the tool's own output.** adstex prints warnings for keys it
   couldn't resolve and for duplicate keys pointing at the same paper — surface
   these to the user rather than silently ignoring them.

## Prerequisites

`adstex` must be installed (`pip install adstex` or
`conda install adstex --channel conda-forge`) and an `ADS_API_TOKEN`
environment variable must be set (obtained from
https://ui.adsabs.harvard.edu/user/settings/token). If a call to `adstex`
fails with an auth error or "command not found," check these two things first
— see `references/adstex-reference.md` for setup details — and ask the user to
supply the token if it's missing rather than trying to guess or fabricate one.

## Common pitfall

Never write the bibtex entry yourself as a substitute for running adstex, even
if you're confident about the paper's details. The entire point of this
workflow is to source bibliographic metadata (authors, journal, volume, pages,
DOI) from ADS directly rather than from memory, which is exactly where errors
creep in.
