# Tabulation of SOLAR polygenic results

## Requirements

* Python 3.6 or later

## Usage

The `tabulate_solar.py` script takes one or more paths, each of which must either represent a `polygenic.out` file or a directory containing `polygenic.out` file. In the latter case, the filename *must* be `polygenic.out`.

```
    $ ./tabulate_solar.py /path/to/polygenic.out > output.tsv
    $ ./tabulate_solar.py /path/to/solar/run/ > output.tsv
```

## Incomplete runs

By default the script will terminate if incomplete runs are detected:
```
    $ cat ./incomplete_run/polygenic.out
    The last run of polygenic did not run to completion.
    Check logs file, or individual fisher output files.
    $ ./tabulate_solar.py ./incomplete_run/polygenic.out > output.tsv
    ERROR: Failed to read './incomplete_run/polygenic.out': The last run of polygenic did not run to completion.
```

The script can instead be made to skip incomplete runs. These will instead result in a warning message being printed:

```
    $ ./tabulate_solar.py ./incomplete_run/polygenic.out --skip-failures > output.tsv
    WARNING: Failed to read './incomplete_run/polygenic.out': The last run of polygenic did not run to completion.
```

Note that this option currently only skips runs that were reported as being incomplete by SOLAR. Malformed files and other errors will still result in the script aborting.

## Example output

| A             | B                  | Pedigree    | Phenotypes        | Individuals | H2r.A     | H2r.A.stderr | H2r.A.pvalue | H2r.B     | H2r.B.stderr | RhoE       | RhoE.stderr | RhoE.pvalue | RhoG      | RhoG.stderr | RhoG.pNotZero | RhoG.pNot1.0 | RhoP.est   | RhoP.est.pNotZero |
|---------------|--------------------|-------------|-------------------|-------------|-----------|--------------|--------------|-----------|--------------|------------|-------------|-------------|-----------|-------------|---------------|--------------|------------|-------------------|
| quicki_normal | NA                 | ped_fam.csv | raw_pheno_fam.csv | 340         | 0.1177479 | 0.1178105    | 0.1626532    | NA        | NA           | NA         | NA          | NA          | NA        | NA          | NA            | NA           | NA         | NA                |
| quicki_normal | avignon_si0_normal | ped_fam.csv | raw_pheno_fam.csv | 340         | 0.1176543 | 0.1185254    | NA           | 0.2880177 | 0.1131847    | -0.1197477 | 0.1019261   | 0.2376698   | 0.4080990 | 0.4657988   | 0.3561600     | 0.2172107    | -0.0197879 | 0.7232246         |
|               |                    |             |                   |             |           |              |              |           |              |            |             |             |           |             |               |              |            |                   |
