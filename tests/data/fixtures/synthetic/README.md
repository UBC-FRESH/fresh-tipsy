# Synthetic parser fixtures

These files are **synthetic**. They are not BC TIPSY data and must not be used for golden or ecological validation.

They exist so parser tests can run without a TIPSY install. They exercise:

- the `[TASS SPECIES]` header block;
- 22 fields per `.tab` data row;
- 151 fields per `.taf` data row;
- two `[RUN,...]` blocks;
- a PCT treatment boundary with `PCT=2`;
- LF line endings, while the real source files use CRLF.

| File | Size | SHA-256 |
| --- | ---: | --- |
| `syn0010N00.tab` | 511 bytes | `df903e29bab725c3f1c77cb704a46e2c96cead70745ece9f6b64ebd002e1d25f` |
| `syn0010N00.taf` | 2,059 bytes | `b7d2477f32707c3f6a10982bb460038881487da901934d358d17b6534e94da93` |

The header identifies the fixture as `DatabaseTitle=Synthetic fixture - not BC data` and `Source=synthetic`. The species code `SYN` is not a real BC species.

The grammar contract is in [`../../../../notes/reference/tab-taf-grammar.md`](../../../../notes/reference/tab-taf-grammar.md).
