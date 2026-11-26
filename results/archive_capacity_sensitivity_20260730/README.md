# Archive-capacity sensitivity analysis

The results for archive capacities 100, 500, and 2000 were computed in separate runs. The capacity-1000 baseline was extracted read-only from the existing main-experiment results by matching ciphertext length, trial index, and seed.

## Design

- Archive sizes: 100, 500, 1000, 2000
- Ciphertext lengths: 100, 150, 200, 300
- Trials per setting: 300
- Search protocol: 4-gram, 30 restarts, 10,000 iterations, patience 2,000
- Paired seed: 20260712

## Key result

- Across all paired trials, capacities 100, 500, 1000 and 2000 produced exactly the same observed rank, Hit@1/5/10/50/100, retention, MRR, score gap and failure mechanism.
- No visited-then-pruned event occurred at any tested capacity.
- Oracle-score rank differed only for capacity 100 in two length-100 trials, where the capacity-100 archive truncated ranks 120 and 148 to 101.
- True-score percentile changes mechanically because its denominator is the archive-dependent candidate count; it should not be interpreted as a capacity-robust effect measure.

## Summary

| archive_size | length | hit@1 | hit@10 | retention_rate | mrr | mean_score_gap | proportion_visited_then_pruned | mean_seconds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 100 | 100 | 0.3333 | 0.5067 | 0.5267 | 0.3915 | 0.338527 | 0.0000 | 2.796 |
| 100 | 150 | 0.7233 | 0.8700 | 0.8867 | 0.7796 | 0.113431 | 0.0000 | 4.118 |
| 100 | 200 | 0.8200 | 0.9767 | 0.9833 | 0.8809 | 0.061547 | 0.0000 | 5.417 |
| 100 | 300 | 0.8900 | 0.9867 | 0.9967 | 0.9281 | 0.055317 | 0.0000 | 8.344 |
| 500 | 100 | 0.3333 | 0.5067 | 0.5267 | 0.3915 | 0.338527 | 0.0000 | 2.802 |
| 500 | 150 | 0.7233 | 0.8700 | 0.8867 | 0.7796 | 0.113431 | 0.0000 | 3.947 |
| 500 | 200 | 0.8200 | 0.9767 | 0.9833 | 0.8809 | 0.061547 | 0.0000 | 5.114 |
| 500 | 300 | 0.8900 | 0.9867 | 0.9967 | 0.9281 | 0.055317 | 0.0000 | 7.731 |
| 1000 | 100 | 0.3333 | 0.5067 | 0.5267 | 0.3915 | 0.338527 | 0.0000 | 2.304 |
| 1000 | 150 | 0.7233 | 0.8700 | 0.8867 | 0.7796 | 0.113431 | 0.0000 | 3.397 |
| 1000 | 200 | 0.8200 | 0.9767 | 0.9833 | 0.8809 | 0.061547 | 0.0000 | 4.521 |
| 1000 | 300 | 0.8900 | 0.9867 | 0.9967 | 0.9281 | 0.055317 | 0.0000 | 6.738 |
| 2000 | 100 | 0.3333 | 0.5067 | 0.5267 | 0.3915 | 0.338527 | 0.0000 | 2.587 |
| 2000 | 150 | 0.7233 | 0.8700 | 0.8867 | 0.7796 | 0.113431 | 0.0000 | 3.821 |
| 2000 | 200 | 0.8200 | 0.9767 | 0.9833 | 0.8809 | 0.061547 | 0.0000 | 5.074 |
| 2000 | 300 | 0.8900 | 0.9867 | 0.9967 | 0.9281 | 0.055317 | 0.0000 | 7.799 |

## Audit

- capacity 100 paired invariants match capacity 1000
- capacity 500 paired invariants match capacity 1000
- capacity 2000 paired invariants match capacity 1000
- Capacity-1000 baseline was derived without recomputation.
- Existing formal result files were treated as read-only sources.
