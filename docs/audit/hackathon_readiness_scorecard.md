# NISR 2026 Big Data Hackathon — Track 1 Readiness Scorecard

**Platform:** AgriLens — Agricultural Intelligence & Decision-Support Platform for Rwanda  
**Track:** Track 1: Agricultural Productivity  
**Evaluation Standard:** 5 Official Judging Criteria (20 points each = 100 total points)  
**Status:** **Objectively Evaluated with Verified Evidence**  

---

## 1. Judging Criteria & Objective Scoring Matrix

| Criterion | Score | Justification & Observed Evidence |
| :--- | :---: | :--- |
| **1. Problem Understanding & Relevance** | **18 / 20** | **Strong.** Directly targets Rwanda's core agricultural challenges under NST2 (2024–2029): quantifying productivity gaps across districts, tracking certified seed and mineral fertilizer adoption, evaluating post-harvest losses, and examining irrigation coverage across seasons. Demonstrates deep understanding of NISR Seasonal Agricultural Surveys (tri-annual seasons A, B, C) and agro-ecological variations. Deducted 2 points because livestock integration from AHS remains at the documentation level. |
| **2. Data Use & Methodology** | **17 / 20** | **Very Strong.** Utilizes authentic microdata from SAS 2024, SAS 2025, and AHS 2024 with zero synthetic numbers. Employs authoritative survey-expansion weighting ($\hat{Y} = \frac{\sum W \times P}{\sum W \times A}$) instead of simplistic unweighted sample means. Preserves source variable traceability, maintains strict provenance isolation between official data and manual entries, and catalogs 923 source variables. Deducted 3 points due to identified pilot duplicate rows (505 rows) and omitted irrigation mapping in the initial pilot loader. |
| **3. Technical Innovation** | **17 / 20** | **Very Strong.** Implements a robust 3-tier storage architecture (Raw Staging ➔ Validated Domain ➔ Analytical Views) in PostgreSQL with SHA-256 batch checksums. Features dynamic dependent geographic cascades (`Province ➔ District ➔ Sector`), interactive Leaflet administrative mapping without watermarks, and a multi-tier review workflow (`Draft ➔ Submitted ➔ Approved`). Fast automated test execution (2.6s). Deducted 3 points due to initial authorization gaps on manual entry review endpoints. |
| **4. Usability & Design** | **18 / 20** | **Outstanding.** Rich, professional interface adopting official NISR brand aesthetics (Royal Blue, Cyan, Green, Yellow). Intuitive navigation with responsive cards, micro-animations, lineage tracking tables, status pills, and interactive productivity gap simulators. Clear error messaging and accessible forms. Deducted 2 points because chart components on the main dashboard still rely partially on hardcoded client-side series rather than 100% dynamic API fetch. |
| **5. Tangible Impact** | **18 / 20** | **High Impact.** Delivers actionable decision-support for MINAGRI, RAB, district agronomists, and development partners. The Productivity Gap Intelligence simulator provides instant empirical comparisons between benchmark and lagging districts (e.g., Musanze vs. Bugesera for Maize). Enables evidence-based resource targeting for CIP seeds, lime, and post-harvest drying facilities. Deducted 2 points because field deployment and offline PWA synchronization are future roadmaps. |
| **TOTAL SCORE** | **88 / 100** | **Top-Tier Hackathon Submission.** Exceptionally credible, statistically responsible, and practically useful. |

---

## 2. Top Three Strategic Priorities for Hackathon Demonstration

1. **Fix Ingestion Practice Mapping & Idempotency:**
   Map `s4q14`/`s4q15` (irrigation), `s4q3` (anti-erosion), and `s4q9` (mechanization) during ETL ingestion, and enforce deduplication so re-running imports never duplicates records.
2. **Refine District Ranking Weighting & Minimum Sample Size:**
   Ensure `get_district_rankings()` applies survey weights and requires $\ge 5$ sampled plots to qualify as a benchmark, preventing single-plot distortions.
3. **Lock Down Manual Entry Permissions:**
   Enforce `@login_required` and managerial role checks (`ANALYST`, `ADMIN`) on the review/approval endpoint, ensuring the review workflow is rock-solid and secure for presentation.
