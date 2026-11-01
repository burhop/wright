# Check related images before assigning validation views

Two files with different hashes can contain the same view after cropping,
resizing or recompression. Counting them as independent validation can make an
inaccurate reconstruction appear better supported than it is.

`measure_image_dependency.py FIRST SECOND OUTPUT_DIRECTORY` is a reusable local
measurement utility. It records original hashes, actual resize transforms,
mutual SIFT matches, robust similarity/homography fits, residuals in original
target pixels and a correspondence figure. It preserves the input files and
refuses to overwrite an existing output directory. It has no workflow executor,
CAD producer, provider protocol or approval authority.

Use a separately qualified environment with OpenCV and NumPy. The initial local
qualification used OpenCV 4.12.0.88 and NumPy 2.2.6. The technique follows the
[OpenCV feature-matching and homography documentation](https://docs.opencv.org/4.x/d1/de0/tutorial_py_feature_homography.html).
A known crop/resize control checks original-pixel coordinate bookkeeping; it is
separate from any engineering tolerance.

Review the correspondence locations and provenance before grouping sources.
A high agreement across relevant features supports treating images as dependent;
it does not prove source authorship or physical authenticity. A poor match does
not prove independence. Shared backgrounds, planar regions, rendering assets,
repeated features and reflective surfaces all affect the result. A homography
does not calibrate a camera or rectify a non-planar vehicle into a drawing.

Retain the report with the survey's source identities through Wright's existing
file/result mechanisms. Any new input bytes require a new measurement. Keep
dependent images together when dividing fitting and validation evidence. This
preparation does not change frozen CAD requirements, tolerances or review state.
