# Technical Decisions

This document outlines the architectural decisions and trade-offs made during the refactoring of the video analysis pipeline.

## 1. Assumptions & Open Questions

**Assumptions:**
- **Video Stability:** We assumed the video might have intermittent corrupted frames, sudden camera cuts, or noise (as demonstrated by the synthetic generator). Our architecture skips over frames where boundary detection raises errors or yields no valid polygons, rather than letting the whole pipeline crash.
- **Stream Errors & Missing Boundaries:** If a boundary is missing for a few frames (e.g., zoom in on a player), it's treated as an empty frame (a logged debug/warning event) but does not stop processing. It's up to downstream consumer logic to handle gaps in tracking.
- **Target FPS vs File FPS:** We assumed `target_fps` dictates the sampling rate. If the video is 30fps and `target_fps` is 5, we only analyze every 6th frame.

**Open Questions for the Product/ML Team:**
- Do we need to interpolate the missing boundaries if a frame is dropped, or does the downstream orchestrator expect gaps?
- What are the real-time constraints? Is this truly offline batch processing where throughput is the only concern, or is there a latency limit per segment?
- Should the mock API receive events as a batch or one-by-one as implemented?

## 2. Validation Strictness vs. Fallback

- **Strict Configuration (Fail Fast):** The application relies on `pydantic` to enforce a strict configuration schema at startup (`core/config.py`). If the config is invalid (e.g., missing API URL, negative FPS, or incorrect path), the app immediately exits with an error before attempting to process the video. A bad configuration is never silently ignored.
- **Resilient Frame Processing (Sensible Fallback):** Video processing is inherently noisy. When `cv2` fails to read a frame or `SamMaskV1Detector` fails to extract a valid polygon from a frame, we log a warning and continue to the next frame. A single bad frame shouldn't take down an hours-long batch job.
- **Resilient Network IO:** The `ApiClient` uses timeouts and try/except blocks to prevent HTTP errors from crashing the pipeline. If the `mock_api` is temporarily unavailable, the pipeline warns and continues, ensuring video processing doesn't become collateral damage of a network blip.

## 3. Performance Trade-offs

- **Frame Skipping for Throughput:** We calculate a `step` variable based on the original video FPS and the `target_fps` configuration. By using `cap.grab()` to skip frames and only decoding the necessary frames with `cap.retrieve()`, processing time scales directly with the requested output density, not the raw video length.
- **Pre-computation:** The original script instantiated the `outer_boundary` polygon inside the per-frame loop. This was moved to the `FieldBoundaryAnalyzer.__init__` method, saving repeated expensive geometric instantiations.
- **Segment Processing:** Added `start_frame` and `end_frame` to the configuration, allowing the pipeline to fast-forward to a specific segment using `cap.set(cv2.CAP_PROP_POS_FRAMES, ...)` and breaking out early, drastically reducing processing time when analyzing small slices of long files.

## 4. AI/LLM Disclosure

During this exercise, an LLM (Gemini / AI agent assistant) was utilized to structure the architectural refactoring, generate the Pydantic configuration schemas, and draft the Dockerfile/docker-compose changes. The code logic for modularizing the pipeline (e.g., separating the interface via `Protocol`, applying `cap.grab()` for frame skipping, and handling API error cases) was guided by best practices injected by the AI, acting as a pair-programmer. 
