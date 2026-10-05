# Canonical results reference

Rounded to two decimals with ROUND_HALF_UP (half away from zero), matching the
manuscript convention. Full precision lives in the CSVs. Every number in the
paper must match this file; do not recompute in drafting or plotting code.

## 1. Categorical (exact Clopper-Pearson 95% CI)

### primary (gemini-3.6-flash)
  accuracy_H             40/40 = 100.00% [91.19, 100.00]
  accuracy_H_L1          40/40 = 100.00% [91.19, 100.00]
  accuracy_H_L2          40/40 = 100.00% [91.19, 100.00]
  accuracy_H_L4          40/40 = 100.00% [91.19, 100.00]
  accuracy_H_L4_ALIGNED  40/40 = 100.00% [91.19, 100.00]
  accuracy_L4_H          40/40 = 100.00% [91.19, 100.00]
  EDR1                   0/40 = 0.00% [0.00, 8.81]
  EDR2                   0/40 = 0.00% [0.00, 8.81]
  EDR4                   0/40 = 0.00% [0.00, 8.81]
  order_disagreement     0/40 = 0.00% [0.00, 8.81]

### replication (gemini-3.6-flash)
  accuracy_H             259/260 = 99.62% [97.88, 99.99]
  accuracy_H_L1          257/260 = 98.85% [96.67, 99.76]
  accuracy_H_L2          258/260 = 99.23% [97.25, 99.91]
  accuracy_H_L4          258/260 = 99.23% [97.25, 99.91]
  accuracy_H_L4_ALIGNED  259/260 = 99.62% [97.88, 99.99]
  accuracy_L4_H          260/260 = 100.00% [98.59, 100.00]
  EDR1                   2/259 = 0.77% [0.09, 2.76]
  EDR2                   1/259 = 0.39% [0.01, 2.13]
  EDR4                   1/259 = 0.39% [0.01, 2.13]
  order_disagreement     2/260 = 0.77% [0.09, 2.75]

### gpt_oss_primary (openai/gpt-oss-120b)
  accuracy_H             40/40 = 100.00% [91.19, 100.00]
  accuracy_H_L1          40/40 = 100.00% [91.19, 100.00]
  accuracy_H_L2          40/40 = 100.00% [91.19, 100.00]
  accuracy_H_L4          40/40 = 100.00% [91.19, 100.00]
  accuracy_H_L4_ALIGNED  39/40 = 97.50% [86.84, 99.94]
  accuracy_L4_H          40/40 = 100.00% [91.19, 100.00]
  EDR1                   0/40 = 0.00% [0.00, 8.81]
  EDR2                   0/40 = 0.00% [0.00, 8.81]
  EDR4                   0/40 = 0.00% [0.00, 8.81]
  order_disagreement     0/40 = 0.00% [0.00, 8.81]

### latent_v2 (gemini-3.6-flash)
  accuracy_H             38/40 = 95.00% [83.08, 99.39]
  accuracy_H_L1          38/40 = 95.00% [83.08, 99.39]
  accuracy_H_L2          38/40 = 95.00% [83.08, 99.39]
  accuracy_H_L4          39/40 = 97.50% [86.84, 99.94]
  accuracy_H_L4_ALIGNED  39/40 = 97.50% [86.84, 99.94]
  accuracy_L4_H          39/40 = 97.50% [86.84, 99.94]
  EDR1                   1/38 = 2.63% [0.07, 13.81]
  EDR2                   1/38 = 2.63% [0.07, 13.81]
  EDR4                   0/38 = 0.00% [0.00, 9.25]
  order_disagreement     0/40 = 0.00% [0.00, 8.81]

### veto (gemini-3.6-flash)
  accuracy_H             15/15 = 100.00% [78.20, 100.00]
  accuracy_H_L1          15/15 = 100.00% [78.20, 100.00]
  accuracy_H_L2          15/15 = 100.00% [78.20, 100.00]
  accuracy_H_L4          15/15 = 100.00% [78.20, 100.00]
  accuracy_H_L4_ALIGNED  15/15 = 100.00% [78.20, 100.00]
  accuracy_L4_H          15/15 = 100.00% [78.20, 100.00]
  EDR1                   0/15 = 0.00% [0.00, 21.80]
  EDR2                   0/15 = 0.00% [0.00, 21.80]
  EDR4                   0/15 = 0.00% [0.00, 21.80]
  order_disagreement     0/15 = 0.00% [0.00, 21.80]
  VFR_H                  0/15 = 0.00% [0.00, 21.80]
  VFR_H_L1               0/15 = 0.00% [0.00, 21.80]
  VFR_H_L2               0/15 = 0.00% [0.00, 21.80]
  VFR_H_L4               0/15 = 0.00% [0.00, 21.80]
  VFR_H_L4_ALIGNED       0/15 = 0.00% [0.00, 21.80]
  VFR_L4_H               0/15 = 0.00% [0.00, 21.80]

### gpt_oss_veto (openai/gpt-oss-120b)
  accuracy_H             15/15 = 100.00% [78.20, 100.00]
  accuracy_H_L1          15/15 = 100.00% [78.20, 100.00]
  accuracy_H_L2          15/15 = 100.00% [78.20, 100.00]
  accuracy_H_L4          15/15 = 100.00% [78.20, 100.00]
  accuracy_H_L4_ALIGNED  15/15 = 100.00% [78.20, 100.00]
  accuracy_L4_H          15/15 = 100.00% [78.20, 100.00]
  EDR1                   0/15 = 0.00% [0.00, 21.80]
  EDR2                   0/15 = 0.00% [0.00, 21.80]
  EDR4                   0/15 = 0.00% [0.00, 21.80]
  order_disagreement     0/15 = 0.00% [0.00, 21.80]
  VFR_H                  0/15 = 0.00% [0.00, 21.80]
  VFR_H_L1               0/15 = 0.00% [0.00, 21.80]
  VFR_H_L2               0/15 = 0.00% [0.00, 21.80]
  VFR_H_L4               0/15 = 0.00% [0.00, 21.80]
  VFR_H_L4_ALIGNED       0/15 = 0.00% [0.00, 21.80]
  VFR_L4_H               0/15 = 0.00% [0.00, 21.80]

## 2. Confidence contrasts (paired bootstrap, 10,000, seed 68020260909)

### primary
  conflict_minus_H         -5.13 [-6.50, -3.75]  n=40  means 84.50 vs 89.63  down/eq/up 32/6/2  median -5.0
  aligned_minus_H          +2.15 [+0.98, +3.53]  n=40  means 91.78 vs 89.63  down/eq/up 1/27/12  median +0.0
  conflict_minus_aligned   -7.28 [-8.23, -6.30]  n=40  means 84.50 vs 91.78  down/eq/up 38/2/0  median -8.5

### replication
  conflict_minus_H         -4.64 [-5.13, -4.16]  n=260  means 85.48 vs 90.12  down/eq/up 181/74/5  median -5.0
  aligned_minus_H          +1.87 [+1.43, +2.31]  n=260  means 91.99 vs 90.12  down/eq/up 11/159/90  median +0.0
  conflict_minus_aligned   -6.51 [-7.07, -5.95]  n=260  means 85.48 vs 91.99  down/eq/up 224/27/9  median -5.0

### latent_v2
  conflict_minus_H         -4.63 [-6.13, -3.13]  n=40  means 84.38 vs 89.00  down/eq/up 24/15/1  median -5.0
  aligned_minus_H          +1.85 [+0.93, +2.75]  n=40  means 90.85 vs 89.00  down/eq/up 3/19/18  median +0.0
  conflict_minus_aligned   -6.48 [-7.83, -5.10]  n=40  means 84.38 vs 90.85  down/eq/up 34/5/1  median -5.0

### gpt_oss_primary
  conflict_minus_H         -6.35 [-7.95, -4.68]  n=40  means 79.70 vs 86.05  down/eq/up 31/7/2  median -5.0
  aligned_minus_H          -0.60 [-3.00, +1.63]  n=40  means 85.45 vs 86.05  down/eq/up 17/10/13  median +0.0
  conflict_minus_aligned   -5.75 [-7.45, -3.60]  n=40  means 79.70 vs 85.45  down/eq/up 35/4/1  median -5.0

### veto
  conflict_minus_H         -1.33 [-2.33, -0.33]  n=15  means 94.33 vs 95.67  down/eq/up 4/11/0  median +0.0
  aligned_minus_H          -0.47 [-1.27, +0.00]  n=15  means 95.20 vs 95.67  down/eq/up 2/13/0  median +0.0
  conflict_minus_aligned   -0.87 [-1.87, +0.00]  n=15  means 94.33 vs 95.20  down/eq/up 3/12/0  median +0.0

### gpt_oss_veto
  conflict_minus_H         -6.13 [-8.73, -3.27]  n=15  means 85.53 vs 91.67  down/eq/up 13/1/1  median -7.0
  aligned_minus_H          -3.00 [-5.80, +0.27]  n=15  means 88.67 vs 91.67  down/eq/up 10/3/2  median -5.0
  conflict_minus_aligned   -3.13 [-5.00, -1.33]  n=15  means 85.53 vs 88.67  down/eq/up 9/5/1  median -3.0

## 3. Stratified conflict-vs-aligned (Gemini replication, post-hoc)

  Overall                      n=260  -6.51 [-7.07, -5.95]  224/27/9  median -5.0
  High / support               n= 65  -6.65 [-7.68, -5.54]  57/4/4  median -7.0
  High / do_not_support        n= 65  -3.49 [-4.23, -2.69]  47/16/2  median -5.0
  Moderate / support           n= 65  -8.63 [-9.85, -7.37]  60/3/2  median -10.0
  Moderate / do_not_support    n= 65  -7.26 [-8.29, -6.23]  60/4/1  median -5.0

## 4. Degradation (conditioned on H correct)

  replication      H->H_L1   denom=259 total=2 to_insufficient=2 wrong_direction=0 other=0
  replication      H->H_L2   denom=259 total=1 to_insufficient=1 wrong_direction=0 other=0
  replication      H->H_L4   denom=259 total=1 to_insufficient=1 wrong_direction=0 other=0
  gpt_oss_primary  H->H_L1   denom= 40 total=0 to_insufficient=0 wrong_direction=0 other=0
  gpt_oss_primary  H->H_L2   denom= 40 total=0 to_insufficient=0 wrong_direction=0 other=0
  gpt_oss_primary  H->H_L4   denom= 40 total=0 to_insufficient=0 wrong_direction=0 other=0

## 5. McNemar exact

  primary          H_L4_ALIGNED_vs_H_L4   p=1.000
  primary          L4_H_vs_H_L4           p=1.000
  replication      H_L4_ALIGNED_vs_H_L4   p=1.000
  replication      L4_H_vs_H_L4           p=0.500
  latent_v2        H_L4_ALIGNED_vs_H_L4   p=1.000
  latent_v2        L4_H_vs_H_L4           p=1.000
  veto             H_L4_ALIGNED_vs_H_L4   p=1.000
  veto             L4_H_vs_H_L4           p=1.000
  gpt_oss_primary  H_L4_ALIGNED_vs_H_L4   p=1.000
  gpt_oss_primary  L4_H_vs_H_L4           p=1.000
  gpt_oss_veto     H_L4_ALIGNED_vs_H_L4   p=1.000
  gpt_oss_veto     L4_H_vs_H_L4           p=1.000

## 6. Anonymization sensitivity

  all cases                                      n=260  -6.51 [-7.07, -5.95]
  excluding intervention-identifying questions   n=251  -6.44 [-7.02, -5.87]
  intervention-identifying questions only        n=  9  -8.33 [-11.11, -6.11]
  excluded (9): R0037;R0041;R0048;R0094;R0122;R0139;R0140;R0158;R0262

## 7. Flip threshold (PRESPECIFIED, score_results.py)

  primary          n= 40  {'>4': 40}
  replication      n=259  {'>4': 257, '1': 2}
  latent_v2        n= 38  {'>4': 36, '1': 1, '2': 1}
  veto             n= 15  {'>4': 15}
  gpt_oss_primary  n= 40  {'>4': 40}
