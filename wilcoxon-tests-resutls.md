# Section Coverage Performance and Statistical Analysis

## 1. Overall Performance Metrics

| Method | Precision | Recall | F1-Score |
| :--- | :---: | :---: | :---: |
| **Dev-Plan** | 0.892962 | 0.750000 | 0.798912 |
| **Golden** | 0.776796 | 0.666667 | 0.676820 |
| **MAS** | 0.985357 | 0.695833 | 0.811589 |
| **Single-Agent** | 0.778968 | 0.491667 | 0.601170 |

---

## 2. Wilcoxon Signed-Rank Test Results (with Holm Correction)

*(Note: Holm-adjusted p-values $< 0.05$ are marked in **bold** to indicate statistical significance).*

### A. Precision

| Comparison | W-Statistic | p-value | Holm p-value |
| :--- | :---: | :---: | :---: |
| **Dev-Plan vs MAS** | 39.0 | 0.07583 | 0.1517 |
| **Dev-Plan vs Single-Agent** | 28.0 | 0.00699 | **0.02796** |
| **Dev-Plan vs Golden** | 28.5 | 0.01304 | **0.03912** |
| **MAS vs Single-Agent** | 4.0 | 0.0002374 | **0.001425** |
| **MAS vs Golden** | 5.0 | 0.0004545 | **0.002273** |
| **Single-Agent vs Golden** | 88.0 | 0.77810 | 0.7781 |

### B. Recall

| Comparison | W-Statistic | p-value | Holm p-value |
| :--- | :---: | :---: | :---: |
| **Dev-Plan vs MAS** | 37.5 | 0.19970 | 0.3995 |
| **Dev-Plan vs Single-Agent** | 0.0 | 0.0001281 | **0.0007689** |
| **Dev-Plan vs Golden** | 28.5 | 0.02235 | 0.06704 |
| **MAS vs Single-Agent** | 0.0 | 0.0001897 | **0.0009483** |
| **MAS vs Golden** | 76.0 | 0.44310 | 0.4431 |
| **Single-Agent vs Golden** | 24.0 | 0.0073010 | **0.0292** |

### C. F1-Score

| Comparison | W-Statistic | p-value | Holm p-value |
| :--- | :---: | :---: | :---: |
| **Dev-Plan vs MAS** | 86.5 | 0.73230 | 0.7323 |
| **Dev-Plan vs Single-Agent** | 0.0 | 0.00008845 | **0.0005307** |
| **Dev-Plan vs Golden** | 19.5 | 0.0023770 | **0.009507** |
| **MAS vs Single-Agent** | 0.0 | 0.0001308 | **0.000654** |
| **MAS vs Golden** | 25.0 | 0.0028180 | **0.009507** |
| **Single-Agent vs Golden** | 56.0 | 0.06733 | 0.1347 |