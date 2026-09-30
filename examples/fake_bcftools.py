"""A tiny stand-in for bcftools (query -l, view -S), used by the demo and tests.

It reads and writes plain-text VCF whatever the file name, and mimics the
one behaviour the extractor relies on: `view -S` fails when a requested
sample is missing, unless --force-samples is given.
"""

import sys
from pathlib import Path

args = sys.argv[1:]


def header_samples(path):
    for line in Path(path).read_text().splitlines():
        if line.startswith("#CHROM"):
            return line.split("\t")[9:]
    return []


def main():
    if args[:2] == ["query", "-l"]:
        path = Path(args[2])
        if not path.exists():
            print(f"[E::hts_open_format] Failed to open {path}", file=sys.stderr)
            return 255
        print("\n".join(header_samples(path)))
        return 0

    if args[0] == "view":
        wanted = Path(args[args.index("-S") + 1]).read_text().split()
        out = args[args.index("-o") + 1]
        src = args[-1]
        have = header_samples(src)
        missing = [s for s in wanted if s not in have]
        if missing and "--force-samples" not in args:
            msg = (
                f"subset called for sample that does not exist in header: {missing[0]}"
            )
            print(f"Error: {msg}", file=sys.stderr)
            return 255
        keep = [i for i, s in enumerate(have) if s in wanted]
        lines = []
        for line in Path(src).read_text().splitlines():
            if line.startswith("##"):
                lines.append(line)
                continue
            cols = line.split("\t")
            lines.append("\t".join(cols[:9] + [cols[9 + i] for i in keep]))
        Path(out).write_text("\n".join(lines) + "\n")
        return 0

    print(f"fake bcftools: unsupported command {args}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
