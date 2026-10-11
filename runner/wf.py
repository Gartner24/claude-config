#!/usr/bin/env python3
# The workflow runner (spec 0001). Stdlib only, so a fresh clone works with no
# install step. Subcommands land per release: `next` in Release 1, `run` later.
import argparse
import sys


def build_parser():
    parser = argparse.ArgumentParser(prog="wf", description="Workflow runner for repo scopes.")
    parser.add_subparsers(dest="command", metavar="<command>")
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help(sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
