# Sprint 1 delivery: Fatoumata

| | |
| --- | --- |
| Team | 2, Diagnosis |
| Role | Person A: photo diagnosis model |
| Date | 25 November 2026 |
| Scope | Ghana only; the 4 crops of the CCMT dataset (cashew, cassava, maize, tomato), 22 classes |
| Pull requests | #14 `docs/photo-datasets` (CCMT data sheet): https://github.com/Primael75/PFE/pull/14; #15 `feat/diagnosis-baseline` (baseline model): https://github.com/Primael75/PFE/pull/15 |

## Summary

| Task | Status | Main result | Evidence |
| --- | --- | --- | --- |
| Ghana photos: originals only, no duplicates, three splits, test split locked | Done | 24,295 photos kept out of 24,881; 6 of 6 automatic checks pass | `docs/data/ccmt.md`, #14 |
| Data sheet (source, date, licence) | Done | CCMT, CC BY 4.0, checked on 21 November 2026 | `docs/data/ccmt.md` |
| First model and its score | Done | 83.4 % accuracy on the validation split (22 classes) | #15, `src/agritech/diagnosis/` |
| H-T2: diagnosis in under 5 s | Phone: done. Server: to do | Phone: 61 ms worst case over 18 photos. Server measurement of `diagnose_photo`: with Kelyan, by 28 November | `docs/trials/ht2-diagnosis-time.md` |
| H-T3: licences of the retained datasets | Done for CCMT | CC BY 4.0; open point on the ImageNet pretrained weights | `docs/trials/ht3-licences.md` |
| Tanzanian dataset and iCassava | Decided | No longer used (see "Decisions") | Meeting notes J1 |

## 1. Data preparation (CCMT, Ghana)

Source: [Mendeley Data](https://data.mendeley.com/datasets/bwh3zbpkpv/1), DOI 10.17632/bwh3zbpkpv.1, version 1 (26 April 2023). Only the `Raw Data` folder is used. The `Augmented` folder is left out: a copy of one photo could land in training and another copy in test, which would inflate the score.

What `prepare_data.py` does:

1. skips any folder whose name contains "augment";
2. names each class with its crop (`maize_healthy`, `tomato_healthy`…), because `healthy` exists in all 4 crops;
3. removes exact duplicates (same MD5 hash);
4. drops unreadable photos after fully decoding each image;
5. groups near-duplicates (dHash, Hamming distance ≤ 4) so that a group never spans two splits;
6. splits each class 70 / 15 / 15 (train / validation / test, seed 42);
7. locks the test split (read-only file and SHA-256 hash).

| Crop | Before | Unreadable | Exact duplicates | After | Train | Validation | Test |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Cashew | 6,549 | 0 | 1 | 6,548 | 4,579 | 984 | 985 |
| Cassava | 7,508 | 0 | 129 | 7,379 | 5,160 | 1,109 | 1,110 |
| Maize | 5,389 | 69 | 278 | 5,042 | 3,524 | 759 | 759 |
| Tomato | 5,435 | 25 | 84 | 5,326 | 3,720 | 804 | 802 |
| **Total** | **24,881** | **94** | **492** | **24,295** | **16,983** | **3,656** | **3,656** |

Test split hash: `sha256(test.csv) = c22092e845b21c6297645cc6a6a3da7d662df6655155cc9c9ff374d04ebdadc7`.

`check_split.py`: 6 of 6 checks pass (no near-duplicate group shared between splits, no identical file between splits, no augmented photo, only the 4 expected crops, every class carries its crop name, no photo listed twice).

## 2. Baseline model

- **Model**: MobileNetV3-Large (4.2 million weights), pretrained on ImageNet (torchvision), last layer replaced by 22 outputs. Library: PyTorch.
- **Preprocessing**: EXIF orientation, RGB, resize to 224 × 224, ImageNet normalisation. Augmentation (crop, flip, rotation, colour, blur) on the training split only.
- **Training, step 1**: only the last layer learns (28,182 weights); class weights compensate for imbalance. CPU only (WSL), 5 epochs.

| Epoch | Train accuracy | Validation accuracy | Validation loss | Time |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 69.2 % | 79.1 % | 1.179 | 335 s |
| 2 | 78.0 % | 81.5 % | 1.121 | 337 s |
| 3 | 80.1 % | 81.5 % | 1.110 | 342 s |
| 4 | 80.6 % | 82.2 % | 1.097 | 398 s |
| 5 | 81.6 % | **83.4 %** | 1.078 | 451 s |

**Score: 83.4 % accuracy on the validation split** (3,656 photos), against about 4.5 % for random guessing. Train and validation accuracy rise together, so the model is not memorising. The gain slows down while only the last layer learns: step 2 (unfreezing the last 3 blocks) is the next lever.

Per-class scores: see `src/agritech/diagnosis/README.md` (PR 2).

## 3. H-T2: diagnosis time

Details and per-photo table: `docs/trials/ht2-diagnosis-time.md`.

- **On a phone (done, 23 November)**: `model_fp32.onnx` (16.9 MB) runs in the phone's browser (ONNX Runtime Web, 1 thread). Over 18 photos, photo to diagnosis takes 51.5 ms (median) and 61 ms at most (also the p95). Loading the model takes 157 ms the first time. **Under 5 s on this phone.**
- **On the server, through the `diagnose_photo` tool (to do, with Kelyan, by 28 November)**: this is the measurement asked for by the review. 20 photos, p95 compared with 5 s.
- The 8-bit model (4.7 MB) is not used: its accuracy drops from 83 % to 63 %.

## 4. H-T3: licences

- **CCMT**: CC BY 4.0, checked on the Mendeley page on 21 November 2026. Obligation: cite Mensah et al. (2023), *Data in Brief* 49, 109306.
- **Libraries** (PyTorch, torchvision, NumPy, Pillow, scikit-learn, ONNX, ONNX Runtime): BSD, MIT or Apache 2.0. None is AGPL or non-commercial (ENF-11).
- **Open point**: torchvision states that pretrained weights may carry terms from their training data (ImageNet). To check before any commercial use.

## 5. Decisions

- **Scope**: the 4 CCMT crops (22 classes), Ghana only.
- **Tanzanian dataset and iCassava: no longer used** (team decision, to be recorded in the J1 meeting notes). Consequences:
  - EF-17 (evaluation on two other countries, before and after light retraining) leaves the scope;
  - H-B (a model trained in one country stays reliable in others) is not tested;
  - in CA-05, the part "results of the two other countries are reported" is dropped.
- **Model format**: PyTorch for training, ONNX for export (ADR-0001).

## 6. Limits

- The validation split was also used to pick the best epoch, so 83.4 % is slightly optimistic. The reference score will be the test split, measured once at the end.
- Classes are imbalanced: 142 training photos for `maize_healthy`, 1,814 for `cassava_bacterial_blight`. Small classes have 31 to 59 test photos, so their scores are imprecise.
- CCMT photos are 400 × 400 squares; real phone photos are larger and rectangular. A tomato leaf photographed by me was misdiagnosed (`cassava_mosaic`, 32 % confidence): the gap with real photos remains to be measured.
- Confidence is not calibrated yet; there is no "not sure" threshold and no "off-topic" class yet.

## 7. Next (sprint 2)

1. Measure `diagnose_photo` on the server with Kelyan (H-T2, by 28 November).
2. Step 2 of training (last 3 blocks), compared with this baseline on the same validation split.
3. Calibrate confidence, set the "not sure" threshold, build the "off-topic" class (100 photos).
4. Check that photo backgrounds are not linked to classes.
5. Fix the 8-bit export, or keep the full-size model if the server is the target.

## Cross-validation

| Reviewer | Verdict | Date |
| --- | --- | --- |
| | | |
