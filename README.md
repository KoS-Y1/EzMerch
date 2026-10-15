# EzMerch

[简体中文](doc/README.zh-CN.md)

EzMerch is a desktop tool for preparing artwork. Import PNG images, trim transparent margins, add dielines and white bleed borders, and export individual images or a kiss-cut sheet.

## Download

- [Download v0.1.0](https://github.com/KoS-Y1/EzMerch/releases/tag/v0.1.0)

## Features

- Automatically crop transparent margins around artwork.
- Add a dieline with adjustable distance and thickness.
- Add a white bleed border with adjustable distance.
- Resize individual stickers while preserving their aspect ratio.
- Arrange multiple stickers on a sheet with adjustable margins and spacing.
- Work in pixels or millimeters, with configurable output resolution.
- Export flattened PNG images or layered RGB PSD files.

## Getting started

### Run the Windows executable

Download `EzMerch.exe` from the release page above, place it in a folder you can write to, and double-click it to launch. Python is not required for the packaged executable.

### Run from source on Windows

Install Python 3.13, then download or clone this repository. Open PowerShell in the project folder and run:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

These commands use the virtual environment directly, so you do not need to activate it. Dependencies and their pinned versions are listed in [requirements.txt](requirements.txt).

## Using EzMerch

### Load your artwork

1. Click **Select Images** and choose one or more PNG files. Use artwork with a transparent background so generated contours follow the artwork's shape.
2. Click **Load** to prepare the selected images. EzMerch automatically removes transparent outer margins.
3. Review the load results for any failed files.

If you add, remove, or clear images, click **Load** again before exporting.

### Export individual items

1. Choose the **Individual Items** tab.
2. To resize your artwork, select **Enable Resizing**, then set the width, height, unit, and resolution in **Output Settings**. Each image fits within the requested canvas while preserving its aspect ratio and leaving room for any enabled borders.
3. Optionally select **Enable Dieline** and adjust its distance, thickness, and unit.
4. Optionally select **Enable Bleed Line** and adjust its distance and unit. This adds a white border around the artwork.
5. Choose `png` or `psd`, select an **Export Folder**, and click **Export**.
6. Review the export results. Each loaded image produces a separate output file.

Without resizing, artwork keeps its cropped pixel dimensions, with additional space for enabled borders. Output resolution defaults to 300 dpi.

### Export a kiss-cut sheet

1. Choose the **Kiss Cut** tab after loading your images.
2. Set the sheet width, height, unit, and resolution in **Output Settings**.
3. Set **Canvas Margin** for the space inside the sheet edges and **Sticker Spacing** for the gap between stickers.
4. Optionally enable dielines and white bleed borders in the sticker settings.
5. Choose `png` or `psd`, select an **Export File**, and click **Export**.
6. Review the export results for the combined sheet.

EzMerch automatically arranges stickers in a grid and resizes each one to fit its cell while preserving its aspect ratio.

Millimeter measurements are converted to pixels using the output DPI. Choose the dimensions and resolution required for your intended print size.

## TODO

- [ ] Provide executables for macOS and Linux.
- [ ] Complete the command-line interface (CLI).
- [ ] Improve space usage in kiss-cut sheet layouts beyond the current brute-force grid search.
- [ ] Add smoothing and noise reduction for generated dielines and bleed borders.
