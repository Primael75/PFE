# Data sheet: CCMT, Dataset for Crop Pest and Disease Detection

Leaf photos from Ghana (cashew, cassava, maize, tomato), used to train the
photo diagnosis model of axis 2. CCMT is the only photo dataset retained.

| Field | Value |
| --- | --- |
| Link | https://data.mendeley.com/datasets/bwh3zbpkpv/1 |
| DOI | https://doi.org/10.17632/bwh3zbpkpv.1 |
| Host | Mendeley Data |
| Version | 1, published on 2023-04-26 |
| Paper | Mensah et al. (2023), "CCMT: Dataset for crop pest and disease detection", *Data in Brief*, vol. 49, article 109306 |
| Licence | CC BY 4.0, checked on the Mendeley page on 2026-11-21 (see `docs/trials/ht3-licences.md`) |
| Licence obligation | cite the authors (reference above) |
| Country | Ghana, photos taken on local farms |
| Downloaded on | 2026-11-14, `Raw Data` folder only |
| Role in the project | training, validation and test of the baseline model |
| Images | **outside Git** (see "Reproduce the preparation") |

## Description

The Mendeley page announces 24,881 original photos of 4 crops in 22 classes:
diseases, pests and healthy leaves. The downloaded `Raw Data` folder holds
25,220 JPEG files (counted below); the gap with the announced figure is not
explained by the authors. The photos are 400 x 400 pixel squares (848 of the
850 photos inspected).

The archive contains two folders:

- `Raw Data`: the original photos. **This is the only version used.**
- `CCMT Dataset-Augmented`: 102,976 edited copies of the same photos, already
  split into training and test by the authors. **Not used**: one copy of a
  photo could land in training and another in test, which would inflate the
  score. Augmentation is done during training, on the training split only.

Each class is named `crop_disease`, because some folder names exist for
several crops (`healthy` for all 4, `leaf blight` for 2).

## Preparation

Scripts: `src/agritech/data/prepare_data.py`, checked by
`src/agritech/data/check_split.py`.

1. Folders whose name contains "augment" are skipped.
2. Exact duplicates (same MD5 hash) are removed; the first file in path
   order is kept.
3. Unreadable photos are set aside, after a full decode of each image.
4. Near-duplicates are grouped by visual fingerprint (dHash, Hamming
   distance <= 4 out of 64 bits). A group is never split between two sets.
5. Split per class: 70 % training, 15 % validation, 15 % test (seed 42).
6. The test split is locked: read-only file and recorded SHA-256 hash.

### Images per crop, before and after

| Crop | Before | Exact duplicates | Unreadable | After | Training | Validation | Test |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Cashew | 6,549 | 1 | 0 | 6,548 | 4,579 | 984 | 985 |
| Cassava | 7,508 | 129 | 0 | 7,379 | 5,160 | 1,109 | 1,110 |
| Maize | 5,358 | 247 | 69 | 5,042 | 3,524 | 759 | 759 |
| Tomato | 5,805 | 454 | 25 | 5,326 | 3,720 | 804 | 802 |
| **Total** | **25,220** | **831** | **94** | **24,295** | **16,983** | **3,656** | **3,656** |

"Before" is the number of image files in `Raw Data`, outside "augment"
folders. Duplicates are listed in `duplicates.csv` and unreadable photos in
`broken.csv`; the 94 unreadable photos were already damaged in the
downloaded archive (byte-for-byte comparison with the original archive).

### Images per class, before and after

| Class | Before | Exact duplicates | Unreadable | After | Training | Validation | Test |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| cashew_anthracnose | 1,729 | 0 | 0 | 1,729 | 1,209 | 260 | 260 |
| cashew_gumosis | 392 | 0 | 0 | 392 | 274 | 59 | 59 |
| cashew_healthy | 1,368 | 0 | 0 | 1,368 | 957 | 205 | 206 |
| cashew_leaf_miner | 1,378 | 0 | 0 | 1,378 | 964 | 207 | 207 |
| cashew_red_rust | 1,682 | 1 | 0 | 1,681 | 1,175 | 253 | 253 |
| cassava_bacterial_blight | 2,614 | 20 | 0 | 2,594 | 1,814 | 390 | 390 |
| cassava_brown_spot | 1,481 | 16 | 0 | 1,465 | 1,025 | 220 | 220 |
| cassava_green_mite | 1,015 | 0 | 0 | 1,015 | 710 | 153 | 152 |
| cassava_healthy | 1,193 | 0 | 0 | 1,193 | 835 | 179 | 179 |
| cassava_mosaic | 1,205 | 93 | 0 | 1,112 | 776 | 167 | 169 |
| maize_fall_armyworm | 285 | 1 | 0 | 284 | 198 | 43 | 43 |
| maize_grasshoper | 673 | 0 | 0 | 673 | 471 | 101 | 101 |
| maize_healthy | 208 | 0 | 4 | 204 | 142 | 31 | 31 |
| maize_leaf_beetle | 948 | 0 | 15 | 933 | 653 | 140 | 140 |
| maize_leaf_blight | 1,006 | 3 | 16 | 987 | 689 | 149 | 149 |
| maize_leaf_spot | 1,259 | 195 | 20 | 1,044 | 730 | 157 | 157 |
| maize_streak_virus | 979 | 48 | 14 | 917 | 641 | 138 | 138 |
| tomato_healthy | 470 | 3 | 4 | 463 | 322 | 71 | 70 |
| tomato_leaf_blight | 1,301 | 2 | 13 | 1,286 | 899 | 195 | 192 |
| tomato_leaf_curl | 518 | 0 | 7 | 511 | 355 | 78 | 78 |
| tomato_septoria_leaf_spot | 2,743 | 449 | 0 | 2,294 | 1,604 | 346 | 344 |
| tomato_verticulium_wilt | 773 | 0 | 1 | 772 | 540 | 114 | 118 |
| **Total** | **25,220** | **831** | **94** | **24,295** | **16,983** | **3,656** | **3,656** |

For every class, before = duplicates + unreadable + after, and after =
training + validation + test.

### Test split hash

```
sha256(test.csv) = c22092e845b21c6297645cc6a6a3da7d662df6655155cc9c9ff374d04ebdadc7
```

Any change to `test.csv` changes this hash. The final evaluation must check
it before computing the score.

### Automatic checks (`check_split.py`): 6 of 6 passed

- no near-duplicate group is shared by two splits;
- no identical photo (byte for byte) in two splits;
- no photo from an "augment" folder;
- every photo comes from the 4 expected crops;
- every class carries its crop name;
- no photo appears twice.

## Common classes

CCMT is the only photo dataset retained, so there is no cross-dataset class
mapping to maintain. Within CCMT, two folder names are shared between crops
(`healthy` for all 4, `leaf blight` for maize and tomato); they stay separate
classes thanks to the crop prefix, which gives 22 classes.

## Points of attention

- **Imbalanced classes**: from 142 training photos (`maize_healthy`) to
  1,814 (`cassava_bacterial_blight`). Training compensates with class
  weights; small classes have only 31 to 59 test photos, so their per-class
  score is imprecise.
- **Misspelled folder names** in the original dataset: `gumosis`
  (gummosis), `grasshoper` (grasshopper), `verticulium` (verticillium). They
  are kept as they are in class identifiers and fixed only for display.
- **Causal agent not specified** for several classes (maize blight and leaf
  spot, tomato blight, grasshopper, leaf beetle).
- **Varied backgrounds** (blurred foliage, soil, black surface, paper):
  check that no background type is tied to a class.
- **400 x 400 square photos**: phone photos are rectangular and larger; the
  gap between CCMT and real photos is still to be measured.

## Reproduce the preparation

1. Download the archive from the Mendeley page and extract it outside the
   Git repository, for example in `~/pfe/raw_data`.
2. From the repository root:

```bash
uv sync --group diagnosis
uv run python -m agritech.data.prepare_data --root ~/pfe/raw_data --out data_ccmt
uv run python -m agritech.data.check_split --data data_ccmt
sha256sum data_ccmt/test.csv
```

3. Check that the hash of `data_ccmt/test.csv` matches the one above.

Before counts per class, from the `Raw Data` folder:

```bash
find . -type f \( -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' \) -not -ipath '*augment*' \
  | awk -F/ '{print $(NF-2)"/"$(NF-1)}' | sort | uniq -c
```
