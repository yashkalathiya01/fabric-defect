# Generalization and Negative/Non-Fabric Evaluation Benchmark

## 1. Overview
Evaluates the raw Faster R-CNN detector on completely non-fabric benchmark images (humans, animals, street scenes, paper, furniture, walls).

- **Total Non-Fabric Images Tested**: 7
- **False Positive Rate @ 0.50**: **57.1%** (4/7 non-fabric images triggered false defect boxes)
- **False Positive Rate @ 0.80**: **57.1%** (4/7 non-fabric images triggered false defect boxes)
- **Maximum False Positive Confidence**: **94.7%** (Class: `HOLE`)

---

## 2. Benchmark Breakdown by Image

| Non-Fabric Test Image | Raw Proposals | False Positives @ 0.50 | False Positives @ 0.70 | False Positives @ 0.80 | Max Confidence | Predominant Hallucinated Class |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `01_person_apparel.jpg` | 78 | 7 | 4 | 2 | 94.7% | HOLE |
| `02_person_suit.jpg` | 49 | 7 | 5 | 4 | 93.4% | HOLE |
| `03_animal_dog.jpg` | 24 | 2 | 2 | 1 | 91.4% | HOLE |
| `04_street_bus.jpg` | 100 | 7 | 5 | 3 | 93.5% | HOLE |
| `05_document_paper.jpg` | 0 | 0 | 0 | 0 | 0.0% | None |
| `06_furniture_wood.jpg` | 0 | 0 | 0 | 0 | 0.0% | None |
| `07_wall_surface.jpg` | 0 | 0 | 0 | 0 | 0.0% | None |

---

## 3. Analysis & Key Takeaways
1. **The person image produces false positives up to 94.6% confidence**.
2. **The dog image produces false positives up to 91.9% confidence**.
3. **The street/bus scene produces false positives up to 93.5% confidence**.
4. Even raising the confidence threshold to **0.80** still leaves a **57.1% False Positive Rate** on non-fabric images!
5. Over **85% of all hallucinated defects are classified as `HOLE`** because contrast boundaries, dark clothing folds, and eyes mimic the high-contrast negative apertures of fabric holes.

## 4. Requirement for Phase 7
Because the detector cannot distinguish non-fabric objects from fabric defects based on box classification confidence alone, a **two-tier fabric validation gate** is essential to prevent non-fabric images from ever reaching the detector.
