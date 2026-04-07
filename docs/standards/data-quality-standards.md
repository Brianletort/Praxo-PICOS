# Data Quality Standards

## Dimensions

| Dimension | Definition | How measured |
|-----------|-----------|--------------|
| Completeness | All expected fields present | Schema validation on extraction output |
| Correctness | Extracted values match source | Golden fixture comparison |
| Consistency | Same source produces same output | Deterministic extraction tests |
| Freshness | Data is recent enough | Last-record timestamp vs SLA threshold |
| Deduplication | No duplicate records | Unique key constraints + dedup checks |
| Privacy | No sensitive data leaks | PII pattern scanning on outputs |

## Freshness SLAs per source

| Source | SLA | Check interval |
|--------|-----|----------------|
| Mail | 30 minutes | 15 min |
| Calendar | 30 minutes | 15 min |
| Screen (Screenpipe) | 5 minutes | 5 min |
| Documents folder | 1 hour | 15 min |
| Obsidian vault | 1 hour | 15 min |

## Golden fixture requirements

Each extractor must have at least one golden fixture that defines:
- Source input (synthetic, realistic data)
- Expected normalized output record
- Expected indexed fields

Golden fixtures live in `tests/fixtures/golden/<source>/`.

## Data Flow Monitor

The Data Flow Monitor runs on a schedule and checks:
1. Freshness: last record timestamp vs now minus SLA
2. Completeness: required fields present on latest N records
3. Volume: records ingested in last interval > 0 (when source is enabled)

Results surface in Health Center with green/yellow/red per source.
