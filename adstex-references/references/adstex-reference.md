# adstex reference

Source: https://github.com/yymao/adstex

## Installation

```bash
conda install adstex --channel conda-forge
# or
pip install adstex
```

## API token setup

adstex needs an ADS API token to query the database.

1. Sign up / log in at https://ui.adsabs.harvard.edu/
2. Get a token at https://ui.adsabs.harvard.edu/user/settings/token
3. Set it as an environment variable:
   ```bash
   export ADS_API_TOKEN="your token string here"
   ```
   Put this line in `~/.bashrc` (or `~/.cshrc` using `setenv` instead of
   `export`) to persist it.

If a token is missing, adstex will fail to authenticate — ask the user to set
`ADS_API_TOKEN` rather than guessing or inventing a value.

## Basic usage

```bash
adstex your_tex_source.tex
```

By default this writes to the `.bib` file already referenced by
`\bibliography{}` in the tex source. For more explicit control (or on adstex
v0.2.x), specify the output file:

```bash
adstex your_tex_source.tex -o your_bib_source.bib
```

Multiple tex source files can be passed at once:

```bash
adstex source1.tex source2.tex -o combined.bib
```

You can also point adstex at an *existing* `.bib` file (no tex source) to
refresh all entries with the latest ADS data:

```bash
adstex your_bibtex_file.bib
```

## What citation key formats adstex recognizes

- **arXiv ID**: e.g. `2404.14498` (new style) or `astro-ph/0501171` (old style, pre-2007)
- **ADS bibcode**: 19-character fixed format, e.g. `2024ApJ...976..118G`
- **DOI**: e.g. `10.1093/mnras/stx3111`
- **FirstAuthor:Year** (and variants like `FirstAuthor:CoAuthor:Year`,
  `FirstAuthorYear`): triggers an ADS search and an **interactive prompt** to
  pick the right paper from a candidate list, or manually enter an identifier.
  This only works well for simple, unambiguous surnames — compound surnames
  should be written without spaces (`deSitter:1913`) or with hyphens kept
  (`Boylan-Kolchin:1913`).

All variants of `\cite` commands are recognized (`\cite`, `\citet`, `\citep`,
`\citealt`, optional-argument forms like `\citep[e.g.,][]{...}`, multiple keys
in one command, etc.) — this is regex-based, not AI, so it depends on standard
LaTeX cite syntax.

## Useful optional arguments

Run `adstex --help` for the full list. Notable ones:

| Flag | Effect |
|---|---|
| `-o FILE` | Output/target bibtex file |
| `-r FILE [FILE ...]` | Additional existing `.bib` files to check against (read-only; only the `-o` file is modified) — useful for skipping keys already defined in a shared/software bibliography |
| `--use-coauthors` | Use coauthor surnames in `FirstAuthor:CoAuthor:Year` style keys when searching ADS |
| `--include-physics` | Also search the ADS physics database (not just astronomy) for `author:year` keys |
| `--parallel` (`-p`) | Use multiple threads to speed up lookups; `--threads=N` sets the count (default 8) |
| `--no-update` | Skip re-checking keys already in the bib file (faster, but won't catch arXiv→journal updates) |
| `--force-regenerate` | Regenerate bibtex for *all* existing entries from the latest ADS version, even if already up to date |
| `--merge-other` | Merge entries from the `-r` reference file(s) into the output file, instead of just checking against them |
| `--no-backup` | Don't write a backup of the previous `.bib` file |
| `--disable-ssl-verification` | Workaround for `SSLCertVerificationError`; weakens security, only use temporarily |
| `--ignore-env-args` | Ignore anything set via the `ADSTEX_ARGS` environment variable |

Default flags can be set persistently via the `ADSTEX_ARGS` environment
variable, e.g.:
```bash
export ADSTEX_ARGS="--use-coauthors --include-physics --parallel"
```

## Behavior notes

- adstex never edits the `.tex` source — only the `.bib` output file.
- If an arXiv preprint you already cited has since been published in a
  journal, re-running adstex will detect and update the bibtex entry
  automatically (unless `--no-update` is passed).
- If two different citation keys in the document turn out to refer to the
  same paper (e.g. one collaborator used an author:year key, another used the
  arXiv ID), adstex will warn about this at the end of its run but will *not*
  merge them — the keys need to be reconciled manually in the tex source.
- Works with any paper in the ADS system, not just astronomy — arXiv ID,
  bibcode, or DOI keys resolve regardless of database. Only bare
  `author:year` search is restricted to astronomy by default (see
  `--include-physics`).

## Overleaf usage

adstex is a local CLI tool, so it can't run inside Overleaf directly:

- With an Overleaf Git or Dropbox sync subscription: sync locally, run
  `adstex`, then push/sync the updated `.bib` back.
- Without premium sync: download the `.tex` and `.bib` files, run `adstex`
  locally, and re-upload only the updated `.bib` file (the `.tex` file is
  never modified by adstex).

## Troubleshooting

- **`SSLCertVerificationError`**: usually a stale local SSL certificate store.
  Update it, or use `--disable-ssl-verification` as a temporary workaround
  (note: this can expose the API token to a man-in-the-middle attack — if
  concerned, regenerate the token afterward at the ADS token page).
- **Auth/401 errors**: `ADS_API_TOKEN` is missing, expired, or malformed —
  check it's exported in the current shell.
- **A citation isn't resolving**: confirm the identifier is correct (arXiv ID
  or bibcode) by checking the paper on https://ui.adsabs.harvard.edu/ or
  https://arxiv.org/ directly — adstex can only find what actually exists in
  ADS under that exact identifier.

## Acknowledgment convention

Papers using adstex conventionally add to their acknowledgements section:

> This research has made use of NASA's Astrophysics Data System.

and optionally:

> This research has made use of adstex (\url{https://github.com/yymao/adstex}).
