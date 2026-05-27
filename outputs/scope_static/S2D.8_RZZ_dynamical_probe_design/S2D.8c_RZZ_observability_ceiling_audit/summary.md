# S2D.8c RZZ Observability Ceiling Audit

```text
S2D.8c verdict:
  setB: FAIL
  setC: FAIL
  global: GLOBAL_FAILURE
```

| run | role | verdict | macro F1 | balanced acc | real-scrambled bal | real-permutation bal | min recall |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| phys9_setA | regression_context | SKIP | n/a | n/a | n/a | n/a | n/a |
| phys9_multicircuit_setB_balanced | primary | FAIL | 0.2500 | 0.2222 | -0.2222 | -0.0217 | 0.0000 |
| phys9_multicircuit_setC_balanced | primary | FAIL | 0.5278 | 0.5833 | -0.0833 | 0.4017 | 0.0000 |
