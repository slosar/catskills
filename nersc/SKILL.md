---
name: nersc
description: Run commands on, or transfer files to/from, NERSC (Perlmutter). Use whenever a task needs NERSC.
---

# Working on NERSC

Authentication is interactive (password + OTP) and only the user can do it.
A persistent SSH master connection is kept open by the user. You must reuse it.

## Rules
- ALWAYS use the host alias `nersc`. Never use `perlmutter`, or
  `perlmutter.nersc.gov` directly, and never try to authenticate or run sshproxy.
- Before the first NERSC command in a task, check the master:
  `ssh -O check nersc-ctrl`
  If it reports no master running (or any ssh command fails with a
  BatchMode/permission/connection error), STOP and ask the user to run
  `ssh -fN nersc-ctrl` in their terminal. Do not retry in a loop.
  

## Running commands
- Each ssh call is a fresh login shell. No cwd or `module load` carries over.
  Put everything in one call:
  `ssh nersc 'bash -lc "cd $SCRATCH/proj && module load python && python run.py --check"'`
- Keep calls short (seconds to minutes). For anything longer, submit with
  `sbatch` and poll with `squeue --me` / `sacct -j <id>`, or start it under
  `nohup ... &> log &` and tail the log.

## Queued jobs
- Do not run heavy computation on login nodes. Use `sbatch` or `salloc`.
- Use `$ALLOC` as the account number to use
- NERSC strongly prefers large-short jobs rather than long or many jobs:
    + Whenever possible parallelize 
    + Combine trivially paralelizable many jobs into a single `sbatch` job 
    + For runs that are over in less than 30 mins use the debug queue


## Files
- `rsync -av localdir/ nersc:/path/` and `scp file nersc:/path/`
  reuse the same connection.
- `$PROJ_DIR` is where you should install persistent codebases, data and similar. Lives under CFS.
- `$SCRATCH` is for large temporary files
- `$HOME` is limited and should only be used for small files

## Github
- `gh` is available, if not authenticated ask user to authenticate

## Data
Commonly used cosmological data are available under $CFS, in particular:
- Public DESI data under $CFS/desi/public
- Public SDSS/BOSS/eBOSS data under: $CFS/sdss
- Public Planck data under: $CFS/planck/data
- Public ACT data under $CFS/act/data
- DESI LegacySurvery under $CFS/cosmo/data/legacysurvey
- WISE survey under $CFS//cosmo/data/wise
- A lot of other public data can be found in $CFS/cosmo/data