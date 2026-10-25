# Spatial SAM 2 local preview

The Spatial contour preview uses an Ultralytics SAM 2.1 box prompt followed by
OpenCV mask cleanup and polygon extraction. It is an optional local-development
feature; it is disabled unless explicitly enabled and is not included in the
Cloud Run runtime configuration.

Install Ultralytics into the Python environment used to run the app:

```powershell
python -m pip install ultralytics
```

Enable the preview in PowerShell and start the application:

```powershell
$env:SPATIAL_SAM2_ENABLED = "1"
$env:SPATIAL_SAM2_MODEL = "sam2.1_b.pt"
python app.py
```

For repeat local runs, the ignored `.env.spatial.local` file is also loaded
after `.env` and can hold `SPATIAL_SAM2_ENABLED=1`. Restart the app after
changing this setting. This local override is not committed or used in
deployments where the file is absent.

Ultralytics downloads the model checkpoint the first time it is needed. To use
an already downloaded checkpoint instead, set `SPATIAL_SAM2_MODEL` to its
absolute path. The first inference can take longer while weights are loaded.
Inference runs on CPU when CUDA is unavailable.

The normal scan pipeline sends the unchanged source photo to Gemini first.
Gemini's semantic names, clusters, and boxes become object variables and SAM 2
box prompts. OpenCV then cleans each SAM 2 mask, extracts a thin contour, and
computes Canny edge support. The Spatial overlay shows semantic labels and
unfilled outlines; detection boxes remain available for comparison. Annotated
pixels are not sent back to Gemini, since that could bias its visual analysis.

The same saved-evidence contour preview is also used by the Simulator and
Quarterly Surveillance Timeline pages. Both pages link a scan to its
`evidence_id`, show progress below the perspective readout, and keep the
SAM 2/OpenCV outline on a separate transparent overlay with an on/off control.
The original photo is still sent to Gemini; the contour endpoint runs only
after live detections have been saved. Timeline stage changes clear the
previous stage's outline, and fallback or unpersisted scans are clearly marked
as unavailable rather than being presented as image-verified segmentation.

A missing checkpoint or inference failure is shown as unavailable; the
application does not substitute an edge-only contour. SAM 2 masks and OpenCV
contours remain suggestions and require visual/ground-truth review before any
measurement or compliance use. Only images with a saved scan and original
image data can be processed by the preview endpoint. OpenCV static replay
applies a low-opacity diagnostic mask (alpha 28/255) and is independent from the
semantic hybrid outlines.

During a Spatial scan, the progress indicator reports the current Gemini and
SAM 2/OpenCV phase. It is intentionally indeterminate while a request is
running because those services do not expose reliable percentage progress; it
finishes with a result, a no-detections message, or an explicit unavailable or
error reason.

The separate **OpenCV static replay** control is only a diagnostic of the HSV
mask on a repeated still image. It is not camera streaming and does not validate
temporal noise rejection or motion compensation.
