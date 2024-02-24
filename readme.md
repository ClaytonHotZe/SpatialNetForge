# SLICE_DET: Image Slicing and Object Detection

SLICE_DET is a Python tool designed for image slicing and object detection using pre-trained models. It facilitates the processing of large geospatial images by slicing them into smaller, manageable pieces, applying object detection algorithms, and optionally merging the results.

## Features

- **Customizable Image Slicing:** Define slice dimensions and overlap ratios to optimize processing.
- **Object Detection:** Leverages YOLOv8 for detecting objects with adjustable confidence thresholds.
- **Multiprocessing Support:** Enhances processing efficiency by utilizing multiple cores.
- **Flexible Input and Output:** Supports a range of image formats and custom paths for input and output directories.

## Requirements

- Python 3.x
- Libraries: os, concurrent, statistics, argparse
- A pre-trained model compatible with YOLOv8.
- MrSID Decoder (for MrSID image format support).

## Installation

Ensure Python 3.x and required libraries are installed. Download or clone this repository to your local machine. Adjust the `PROJ_LIB`, `mrsid_decoder_path`, and `model_path` in the script to match your environment.

## Usage

```sh
python SLICE_DET.py --proj_lib [path] --mrsid_decoder_path [path] --model_path [path] --objects [object names] --model_type yolov8 --model_device [device] --model_confidence_threshold [threshold] --slice_height [height] --slice_width [width] --overlap_height_ratio [ratio] --overlap_width_ratio [ratio] --source_image_dir [directory] --out_dir [output directory] --workers [number of workers] --merge [True/False]
```
## Contributing
Contributions are welcome! Please fork the repository and submit pull requests with any enhancements, bug fixes, or improvements.

## License
Specify the license under which this software is distributed. (This will need to be defined by the original author or organization.)
