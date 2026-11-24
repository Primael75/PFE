# H-T2: response time of the photo diagnosis

**Hypothesis (specification):** the diagnosis of a photo takes less than
5 seconds in the browser of a modest phone.

**Verdict: passed on the phone tested.** Worst case 61 ms per photo, far
under 5 s. Whether this phone counts as "modest" is not established (see
Limits).

## Result on a phone

| Measure | Value |
| --- | --- |
| Phone | iPhone, iOS 18.7, 4 cores (model: to fill in), inside the Claude app |
| Date | to fill in |
| Model file | `model_fp32.onnx` of run1, 16.9 MB, SHA-256 `baeb5f3f008375b360b5682550f48617b0e0ae957ccc8cc11236642dd6f0edef`; ONNX Runtime Web, WebAssembly, 1 thread |
| Photos | 17 from the validation split (CCMT, 400 x 400) + 1 phone photo |
| Photo to diagnosis, median | 51.5 ms |
| Photo to diagnosis, worst case | 61 ms |
| Model loading, first open | 157 ms (31 ms when reopened) |
| First full use, loading included | 209 ms at most |
| Answers on the 17 validation photos | 16 correct (not a score: sample too small) |

### Limits of the phone test

- **17 validation photos instead of 20.**
- **"Modest" not shown**: an iPhone is possibly not a modest phone. The
  margin is about 80 times (61 ms against 5 s), so a slower phone is
  likely to pass too, but a low-end Android phone remains to be tested.
- **Small photos**: validation photos (400 x 400) are smaller than real
  phone photos, so photo preparation may take longer in the field.
- **The 8-bit model is not used**: `model_int8.onnx` (4.7 MB) drops from
  83 % to 63 % accuracy on 500 validation photos (export check of run1).
  The phone runs the 32-bit model, which gives the same answer as PyTorch
  on all 500 photos of the same check.
- **Not reproducible from the repository yet**: the ONNX export script and
  the test page are not in the repository.

## Reference measure on a laptop (not H-T2)

### What is measured

Script: `src/agritech/diagnosis/latency.py`.

- **Per photo**, what one request does: read the file, decode it, apply the
  EXIF rotation, resize to 224 x 224, normalise, run the model, pick the
  class. One photo at a time, no batching.
- **Model loading**, apart: a server does it once at start-up.
- **First photo**, apart: the first call pays one-off setup costs. It is
  an extra photo, not one of the 20 measured.
- Photos: 20 photos of the CCMT validation split, drawn at random
  (seed 42), plus 1 warm-up photo. The list is in the JSON output.

### Setup

| Field | Value |
| --- | --- |
| Model | baseline run1, SHA-256 `da24a99f6d601c9783289f0ebb83ed6ae2515a284e7f223a49247b67d178b551` (see `src/agritech/diagnosis/README.md`) |
| Runtime | PyTorch 2.15.0, CPU build, float32 |
| Machine | AMD Ryzen 7 7730U laptop (8 cores, 16 threads), WSL2 on Windows, 6 GB of RAM given to WSL |
| Photos | CCMT JPEG, 400 x 400 pixels |
| Date | 2026-11-23 |

### Results (20 photos)

| PyTorch threads | Model loading | First photo | Median | 90th percentile | Mean | Max |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 8 (default) | 178 ms | 151 ms | 24.3 ms | 29.9 ms | 25.5 ms | 32.5 ms |
| 1 | 120 ms | 42 ms | 20.7 ms | 24.2 ms | 21.1 ms | 25.1 ms |

One photo at a time is slightly faster on a single thread: the model is too
small for 8 threads to pay off.

### Limits of both measures

- **Model time only**: the time of the whole chain (upload to Fred,
  Knowledge Flow, MCP tool, agent, answer) is measured by H-T4
  (`docs/trials/ht4-photo-tool.md`).
- **Small photos**: CCMT photos are 400 x 400. Phone photos are larger
  (often 12 megapixels); decoding them will take longer. To measure on
  real phone photos.
- **Not a phone**: these figures only show that the model itself is light;
  the verdict comes from the phone test above.

### Reproduce the laptop measure

```bash
uv sync --group diagnosis
uv run python -m agritech.diagnosis.latency --data data_ccmt --model runs/run1/best.pt --out runs/run1/latency.json
uv run python -m agritech.diagnosis.latency --data data_ccmt --model runs/run1/best.pt --threads 1
```
