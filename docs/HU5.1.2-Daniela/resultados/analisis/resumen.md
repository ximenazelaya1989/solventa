C = 20 rps, cuota = 12.0 rps por socio

|   corrida | cuota   | socio   |    n | p50_ms        | p95_ms        | p99_ms        |   error_pct | cumple_asr   |
|----------:|:--------|:--------|-----:|:--------------|:--------------|:--------------|------------:|:-------------|
|         1 | sin     | A       | 3789 | fuera (fallo) | fuera (fallo) | fuera (fallo) |       87.86 | False        |
|         1 | sin     | B       | 3752 | fuera (fallo) | fuera (fallo) | fuera (fallo) |       88.62 | False        |
|         1 | sin     | C       | 3842 | fuera (fallo) | fuera (fallo) | fuera (fallo) |       88.81 | False        |
|         2 | con     | A       | 3724 | 22            | 83            | 504           |        0    | False        |
|         2 | con     | B       | 3893 | 22            | 69            | 470           |        0    | True         |
|         2 | con     | C       | 3846 | 22            | 77            | 477           |        0.03 | True         |
|         3 | sin     | A       | 3844 | fuera (fallo) | fuera (fallo) | fuera (fallo) |       87.1  | False        |
|         3 | sin     | B       | 3791 | fuera (fallo) | fuera (fallo) | fuera (fallo) |       87.52 | False        |
|         3 | sin     | C       | 3738 | fuera (fallo) | fuera (fallo) | fuera (fallo) |       87.4  | False        |
|         4 | con     | A       | 3785 | 28            | 43            | 136           |        0    | True         |
|         4 | con     | B       | 3740 | 28            | 46            | 129           |        0    | True         |
|         4 | con     | C       | 3781 | 28            | 45            | 133           |        0    | True         |
|         5 | sin     | A       | 3708 | fuera (fallo) | fuera (fallo) | fuera (fallo) |       85.73 | False        |
|         5 | sin     | B       | 3830 | fuera (fallo) | fuera (fallo) | fuera (fallo) |       87.21 | False        |
|         5 | sin     | C       | 3833 | fuera (fallo) | fuera (fallo) | fuera (fallo) |       86.3  | False        |
|         6 | con     | A       | 3819 | 30            | 86            | 1030          |        0    | False        |
|         6 | con     | B       | 3749 | 30            | 76            | 840           |        0.03 | False        |
|         6 | con     | C       | 3825 | 30            | 66            | 757           |        0    | False        |

|   corrida | cuota   |   ofrecidas_rps |   aceptadas_rps |   aceptadas |   rechazadas_429 |   otros_errores |   max_aceptadas_1s |   limite_teorico |
|----------:|:--------|----------------:|----------------:|------------:|-----------------:|----------------:|-------------------:|-----------------:|
|         1 | sin     |              90 |             1   |         357 |                0 |           32043 |                117 |              nan |
|         2 | con     |              90 |            12   |        4333 |            28081 |               2 |                 15 |             4344 |
|         3 | sin     |              90 |             1.2 |         426 |                0 |           31972 |                 93 |              nan |
|         4 | con     |              90 |            12   |        4324 |            28070 |               1 |                 14 |             4344 |
|         5 | sin     |              90 |             1.5 |         551 |                0 |           31847 |                 91 |              nan |
|         6 | con     |              90 |            12   |        4325 |            28069 |               0 |                 14 |             4344 |

{
  "condicion_1": false,
  "condicion_1_solo_p95": true,
  "condicion_2": true,
  "condicion_3": true,
  "condicion_3_estricta": false,
  "confirmada": false
}
