# catskills

A collection of [Claude Code](https://claude.com/claude-code) skills for writing and maintaining LaTeX scientific papers, especially in astronomy/physics.

## Skills

### [read-arxiv](read-arxiv/)
Reads arXiv papers from their original LaTeX source instead of scraping the HTML/PDF rendering. Downloads and unpacks the `/e-print/` source for a given arXiv link or ID, so equations, tables, macros, and the bibliography can be read exactly as the authors wrote them rather than through a lossy PDF/HTML conversion.

### [adstex-references](adstex-references/)
Fills in bibliography/citations in a LaTeX document using [`adstex`](https://github.com/yymao/adstex). Given citation keys (arXiv IDs or ADS bibcodes) already placed in `\cite`-family commands, it looks each one up on NASA ADS and generates a correct, complete `.bib` file — avoiding hallucinated bibtex entries.

### [agentic-latex](agentic-latex/)
Enables agentic editing of LaTeX papers via placeholder macros that Claude fills in on request: `\acite` (add a citation, via adstex-references), `\afill` (fill in a small placeholder value/number backed by real evidence), `\awrite` (write a new section/paragraph), `\atable` (generate a table), `\afigure` (generate a figure) and `\adiag` (generate a diagram), each with reproducibility instructions.

## License

MIT
