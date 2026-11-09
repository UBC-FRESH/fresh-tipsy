# Synthetic parser fixtures

These files are **synthetic**. They are not BC TIPSY data and must not be used for golden or ecological validation.

They exist so parser tests can run without a TIPSY install. They exercise:

- the `[TASS SPECIES]` header block;
- 22 fields per `.tab` data row;
- 151 fields per `.taf` data row;
- two `[RUN,...]` blocks;
- a PCT treatment boundary with a repeated age-2 row in the `PCT=2` block;
- LF line endings, while the real source files use CRLF.

| File | Size | SHA-256 |
| --- | ---: | --- |
| `syn0010N02.tab` | 557 bytes | `038121b1afa939d16cebce93494d7abffc375dc53b259c649bcd59efc6ca9898` |
| `syn0010N02.taf` | 2,363 bytes | `4888ec98d0113e2a9ee1ac35ffad63e2a0dbe585f5e933f786c1aad53512786f` |

The header identifies the fixture as `DatabaseTitle=Synthetic fixture - not BC data` and `Source=synthetic`. The species code `SYN` is not a real BC species.

The grammar contract is in [`../../../../notes/reference/tab-taf-grammar.md`](../../../../notes/reference/tab-taf-grammar.md).
