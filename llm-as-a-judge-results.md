# LLM-as-a-Judge Structural Evaluation Results

This document presents the detailed results of the LLM-as-a-Judge evaluation across 4 randomized runs (N=20 repositories per run), comparing four architectures: Dev-Plan (Developer-Guided MAS), MAS (Autonomous Multi-Agent System), Single-Agent, and Golden (Original Ground Truth).

## 1. Aggregated Results (Averaged across 4 Runs)

| Architecture | Mean Score (/10) | Average Placement | 1st Place Win Rate | Failure Rate (Score ≤ 5) |
| :--- | :---: | :---: | :---: | :---: |
| **Dev-Plan (HITL)** | 8.60 | 1.75 | 53.75% | 1.25% |
| **MAS (Autonomous)** | 7.55 | 2.50 | 16.25% | 2.50% |
| **Golden (Human)** | 7.36 | 2.75 | 20.00% | 17.50% |
| **Single-Agent** | 7.25 | 3.00 | 10.00% | 6.25% |

---

## Appendix: Raw Data per Run

### A. Mean Scores (/10)
| Run | Dev-Plan | MAS | Single-Agent | Golden |
| :--- | :---: | :---: | :---: | :---: |
| Run 1 | 8.15 | 7.20 | 8.00 | 7.75 |
| Run 2 | 7.10 | 8.50 | 7.70 | 7.35 |
| Run 3 | 9.40 | 7.05 | 6.40 | 7.15 |
| Run 4 | 9.75 | 7.45 | 6.90 | 7.20 |
| **Average**| **8.60** | **7.55** | **7.25** | **7.36** |

### B. Failure Rate / Scores ≤ 5 (%)
| Run | Dev-Plan | MAS | Single-Agent | Golden |
| :--- | :---: | :---: | :---: | :---: |
| Run 1 | 0% | 0% | 0% | 20% |
| Run 2 | 5% | 0% | 0% | 10% |
| Run 3 | 0% | 0% | 15% | 30% |
| Run 4 | 0% | 10% | 10% | 10% |
| **Average**| **1.25%** | **2.50%** | **6.25%** | **17.50%** |

### C. 1st Place Win Rate (%)
| Run | Dev-Plan | MAS | Single-Agent | Golden |
| :--- | :---: | :---: | :---: | :---: |
| Run 1 | 25% | 0% | 30% | 45% |
| Run 2 | 15% | 60% | 10% | 15% |
| Run 3 | 85% | 0% | 0% | 15% |
| Run 4 | 90% | 5% | 0% | 5% |
| **Average**| **53.75%**| **16.25%**| **10.00%**| **20.00%**|

### D. Average Placement (Rank 1-4)
| Run | Dev-Plan | MAS | Single-Agent | Golden |
| :--- | :---: | :---: | :---: | :---: |
| Run 1 | 1 | 4 | 2 | 3 |
| Run 2 | 4 | 1 | 2 | 3 |
| Run 3 | 1 | 3 | 4 | 2 |
| Run 4 | 1 | 2 | 4 | 3 |
| **Average**| **1.75** | **2.50** | **3.00** | **2.75** |
