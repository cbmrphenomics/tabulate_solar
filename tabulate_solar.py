#!/usr/bin/env python3
# -*- coding: utf8 -*-
import argparse
import collections
import itertools
import re
import string
import sys

from pathlib import Path

# https://hpc.nih.gov/docs/solar-8.1.1/00.contents.html

_RE_VARIABLE_IS = re.compile(r"^(.+) is ([-0-9\.]+)(?:\s+p\s+=\s+([-0-9\.]+))?")
_RE_NAME_AND_TRAIT = re.compile(r"(.+)\((.+)\)")
_RE_STD_ERROR = re.compile(r"^(.+)\s+Std. Error:\s+([-.\d]+)")
_RE_DIFFERENT_FROM = re.compile(r"^(.+) different from\s+(zero|1.0)\s+p = ([-.\d]+)")


class ParseError(RuntimeError):
    pass


def eprint(*args, **kwargs):
    kwargs["file"] = sys.stderr
    print(*args, **kwargs)


def parse_name(name, traits):
    match = _RE_NAME_AND_TRAIT.match(name)
    if match is not None:
        return match.groups()
    elif len(traits) == 1:
        # if there is only one trait then there are only statistics
        # assosiated with that trait
        (trait,) = traits
        return name, trait
    else:
        return name, None


def read_polygenic_out(filepath):
    metadata = {}
    values = {}

    with filepath.open("rt") as handle:
        # Parse metadata; terminated by empty line
        line = handle.readline().strip()
        if line == "The last run of polygenic did not run to completion.":
            raise ParseError(line)

        while line:
            last_value = None
            for value in line.split():
                if value.endswith(":"):
                    last_key = value[:-1]
                    last_value = metadata[last_key] = []
                elif last_value is not None:
                    last_value.append(value)

            line = handle.readline().strip()

        # Parse results
        for line in handle:
            # Results are indented twice with a mix of tabs/spaces
            if not line.replace("    ", "\t").startswith("\t\t"):
                continue

            line = line.strip()

            # H2r is 0.1234567
            # H2r is 0.1234567  p = 0.0123456
            # H2r is 0.1234567  p = 0.1234567  (Not Significant)
            # Variable may include a trait, e.g. "H2r(trait)"
            match = _RE_VARIABLE_IS.match(line)
            if match is not None:
                name, value, pvalue = match.groups()
                name, trait = parse_name(name, metadata["Trait"])

                # Estimates look like other variables:
                #   Derived Estimate of RhoP is 0.1234567
                estimated = False
                if name.startswith("Derived Estimate of "):
                    estimated = True
                    name = name[20:]

                values[(name, trait)] = {
                    "estimated": estimated,
                    "value": value,
                    "pvalue": pvalue,
                    "stderr": None,
                    "different": [],
                }

                continue

            # H2r Std. Error:  0.1234567
            # Variable may include a trait, e.g. "H2r(trait)"
            match = _RE_STD_ERROR.match(line)
            if match is not None:
                name, value = match.groups()
                name, trait = parse_name(name, metadata["Trait"])

                # The record should have been created by the previous line
                current = values.get((name, trait))
                if current is None:
                    raise ParseError()

                current["stderr"] = value

                continue

            # RhoG different from zero  p = 0.1234567
            # RhoG different from 1.0   p = 0.1234567
            match = _RE_DIFFERENT_FROM.match(line)
            if match is not None:
                name, value, pvalue = match.groups()
                name, trait = parse_name(name, metadata["Trait"])

                current = values[(name, trait)]
                current["different"].append((value, pvalue))

                continue

    return {
        "metadata": metadata,
        "traits": metadata.pop("Trait"),
        "values": values,
    }


def build_table(rows):
    # Shorthands for traits
    num_traits = max((len(row["traits"]) for row in rows), default=0)
    traits = string.ascii_uppercase[:num_traits]

    table = []
    for row in rows:
        result = collections.OrderedDict()

        result.update(itertools.zip_longest(traits, row["traits"]))
        result.update((k, " ".join(v)) for k, v in row["metadata"].items())

        for (name, trait), values in row["values"].items():
            key = name
            if values["estimated"]:
                key += ".est"

            if trait is not None:
                idx = row["traits"].index(trait)
                key = "{}.{}".format(name, traits[idx])

            result[key] = values["value"]
            result[f"{key}.stderr"] = values["stderr"]
            result[f"{key}.pvalue"] = values["pvalue"]

            for value, pvalue in values["different"]:
                result[f"{key}.pNot{value.title()}"] = pvalue

        table.append(result)

    return table


def build_header(table):
    header = collections.OrderedDict()
    for row in table:
        for key, value in row.items():
            header[key] = header.get(key, 0) + 0 if value is None else 1

    # Return non-empty columns while maintaining order
    return [k for k, v in header.items() if v]


def parse_args(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "files",
        nargs="+",
        type=Path,
        metavar="PATH",
        help="One or more SOLAR polygenic.out files or directories containing "
        "polygenic.out files",
    )

    parser.add_argument(
        "--na-value",
        default="NA",
        metavar="STR",
        help="Value used for missing values [%(default)s].",
    )

    parser.add_argument(
        "--skip-failures",
        default=False,
        action="store_true",
        help="Skip failed SOLAR runs.",
    )

    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)

    rows = []
    for filepath in args.files:
        # Directories are assumed to be from SOLAR runs
        if filepath.is_dir():
            filepath = filepath / "polygenic.out"

        if not filepath.exists():
            eprint(f"ERROR: SOLAR results not found at '{filepath}'")
            return 1

        try:
            rows.append(read_polygenic_out(filepath))
        except ParseError as error:
            eprint(f"ERROR: Failed to read '{filepath}': {error}")
            if not args.skip_failures:
                return 1
        except Exception:
            eprint(f"ERROR: Error while reading '{filepath}':")
            raise

    table = build_table(rows)
    header = build_header(table)

    print("\t".join(header))
    for row in table:
        result = []
        for key in header:
            value = row.get(key)
            if value is None:
                value = args.na_value

            result.append(value)

        print("\t".join(result))

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
