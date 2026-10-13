# Dataset Statistical and Integrity Audit Report

## 1. Executive Summary
- **Total Images in Dataset**: 1762 (1229 train, 358 valid, 175 test)
- **Total Annotations**: 2966 (2047 train, 616 valid, 303 test)
- **Defect Categories Annotated**: `hole`, `knot`, `stain` (mapped to model IDs 1, 2, 3; 0 = background)
- **Train / Valid Contamination**: 1 identical images across train & valid splits.
- **Train / Test Contamination**: 0 identical images across train & test splits.

---

## 2. Split Breakdown & Class Imbalance

| Split | Images | Annotations | Holes | Knots | Stains | Clean (Empty) Images |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Train** | 1229 | 2047 | 568 | 567 | 912 | 0 (0.0%) |
| **Valid** | 358 | 616 | 186 | 152 | 278 | 0 (0.0%) |
| **Test** | 175 | 303 | 72 | 100 | 131 | 0 (0.0%) |

---

## 3. Critical Findings & Root Cause for False Positives

### Finding 1: Zero Negative/Clean Fabric Images in the Dataset
- Across all 3 splits (1762 images), **every single image contains at least one defect**.
- There are **0 pure background images** in the dataset.
- The Faster R-CNN detector's negative background class (ID 0) only ever saw background patches extracted from inside fabric swatch images containing defects.

### Finding 2: Severe Domain Narrowness (Closed-World Constraint)
- All training images are tight macro/micro photographs of yarn weave textures.
- The model was **never exposed to negative open-world classes** (humans, clothing worn on bodies, faces, birds, animals, paper documents, furniture).
- When an out-of-distribution image is presented, the Region Proposal Network (RPN) proposes high-contrast texture patches (such as dark shadows, folds in clothing, buttons, printed characters, eyes).
- Because the softmax classifier only has `[background, hole, knot, stain]` and the open-world features do not match uniform fabric background, the logits fall predominantly into `"hole"` (the darkest and most contrast-heavy defect class).

### Finding 3: Preprocessing Consistency
- Training notebook applied: `Image.convert("RGB")` -> `ToTensor()` (CHW, [0, 1]).
- Inference code applied: `Image.open().convert("RGB")` -> `ToTensor()` (CHW, [0, 1]).
- Preprocessing during training matches inference 100%. The false positives are NOT caused by a normalization or resizing mismatch.

---

## 4. Conclusion
The false-positive defect detection on non-fabric images is a mathematical consequence of closed-world object detection without negative background diversity. The model is functioning correctly within its domain, but requires a dedicated **pre-inference material validation gate** to reject out-of-domain images before defect scoring.
