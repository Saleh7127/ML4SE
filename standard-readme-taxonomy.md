# README.md Structural Taxonomy

This document outlines the standard 12-section taxonomy used for the **Manual Section Coverage Analysis (RQ2)** in our paper. 

To evaluate the structural completeness and precision of the generated READMEs, we derived this baseline taxonomy from established empirical studies on open-source documentation practices (e.g., [wang2023study](https://doi.org/10.1016/j.jss.2023.111806), [liu2022readme](https://doi.org/10.1016/j.infsof.2022.106924)). 

During our manual evaluation, a generated section was counted as a "True Positive" match if its heading conceptually aligned with one of the standard sections or its associated keywords/aliases.

## 1. Essential Sections
These sections represent the core components necessary for basic repository comprehension and usability.

| Standard Section | Accepted Keywords / Aliases |
| :--- | :--- |
| **Description / Introduction** | `describe`, `description`, `overview`, `about`, `summary`, `introduction`, `what is`, `project` |
| **Table of Contents** | `contents`, `toc` |
| **Installation / Setup** | `install`, `build`, `setup`, `download`, `compile`, `get` |
| **Usage / Getting Started** | `use`, `usage`, `run`, `quickstart`, `start`, `learn` |
| **Contributing / Development** | `contribute`, `contributing`, `development`, `dev setup` |
| **License** | `license`, `legal` |

## 2. Strongly Recommended Sections
These sections significantly enhance user onboarding, trust, and code reusability.

| Standard Section | Accepted Keywords / Aliases |
| :--- | :--- |
| **Credits / Authors** | `credit`, `acknowledge`, `author`, `acknowledgements` |
| **Examples / Features** | `example`, `demo`, `sample`, `feature`, `code samples`, `highlights` |
| **Documentation / Support** | `document`, `docs`, `support`, `wiki`, `help` |

## 3. Optional Enhancements
These sections provide lifecycle context and quality assurance for enterprise or mature projects.

| Standard Section | Accepted Keywords / Aliases |
| :--- | :--- |
| **Troubleshooting** | `troubleshoot`, `faq`, `common issues`, `errors` |
| **Testing** | `test`, `testing`, `run tests` |
| **Project Status / Lifecycle** | `archive`, `deprecate`, `retire`, `status`, `roadmap` |

---
**Note on Evaluation:** In our study, *Structural Precision* calculates the percentage of AI-generated sections that map to this standard taxonomy (penalizing AI "fluff", ), while *Structural Recall* calculates how many of these 12 target sections the AI successfully generated.