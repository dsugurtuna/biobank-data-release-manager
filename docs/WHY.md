# Why it's built this way

## The problem

A genotype data release must contain exactly the participants a project was approved for. Mapping
approved barcodes to genotype sample IDs, extracting them and proving the result is exact is
routine work where small slips (a pasted list, an unchecked extraction) lead to real disclosure
errors.

## Design choices

**Why check the source header before extracting?** Because bcftools stops at the first unknown
sample, and forcing past it hides the gap. Reading the header first lists every missing sample at
once, and proceeding without them becomes a deliberate choice (`allow_missing=True`).

**Why compare sets, not counts?** Because one extra and one missing sample give the right count and
the wrong release. Success means the output header equals the request.

**Why a parameterised IN clause?** Because sample IDs arrive from spreadsheets and emails. Binding
values is the standard protection against broken or malicious SQL. The literal version remains for
pasting into a client, with quotes escaped.

**Why set bcftools' output type from the file name?** Because bcftools before 1.12 wrote
uncompressed text to a file called `.vcf.gz` unless `-O z` was given (1.12 started inferring the
type from the suffix). The file would look right and
fail downstream.

**Why return errors in the result instead of raising?** Because a release run should end with a
record of what happened, including bcftools' own message, not a stack trace.

**Why was the extractor rewritten?** It raised `TypeError` on every call, because a required field
was missing, and it had no tests. It now has tests that run against a small bcftools stand-in.

## Questions worth asking

**"The request is approved, but how do you know the barcode-to-sample mapping is right?"**
This tool trusts the metadata database for the mapping. It makes gaps visible (approved barcodes
with no genotype sample), but it cannot detect a wrong mapping. That needs checks upstream, such as
sex or genotype concordance against a reference, before release.

**"Why not just pass `--force-samples` every time?"**
Because it turns a data problem into a smaller release that nobody notices. The default is to stop
and report; forcing is available, and the result still lists what is missing.

**"What stops the wrong file being sent after a successful extraction?"**
Nothing in this repo. The next step is a checksum manifest and verified transfer, which
[secure-genomic-transfer](https://github.com/dsugurtuna/secure-genomic-transfer) and
[genomic-cohort-delivery-pipeline](https://github.com/dsugurtuna/genomic-cohort-delivery-pipeline)
cover.

## What's next

- Index the output and write a checksum manifest next to it.
- Name the approved barcodes that had no genotype data.
- Chunked or temporary-table lookups for very long lists.
