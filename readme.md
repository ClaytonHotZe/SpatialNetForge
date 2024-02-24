# SpatialNetForge: Image Slicing and Object Detection

SpatialNetForge is a Python tool designed for image slicing and object detection using pre-trained models. It facilitates the processing of large geospatial images by slicing them into smaller, manageable pieces, applying object detection algorithms, and optionally merging the results.

## Features

- **Customizable Image Slicing:** Define slice dimensions and overlap ratios to optimize processing.
- **Object Detection:** Leverages YOLOv8 for detecting objects with adjustable confidence thresholds.
- **Multiprocessing Support:** Enhances processing efficiency by utilizing multiple cores.
- **Flexible Input and Output:** Supports a range of image formats and custom paths for input and output directories.

## Requirements

- Python 3.10
- A pre-trained model compatible with YOLOv8.
- MrSID Decoder (for MrSID image format support).

## Installation

Ensure Python 3.10 is installed on your system. Clone or download this repository to your local machine.

Install the required Python packages by running the following command in your terminal:

```sh
pip install -r requirements.txt
```
The requirements.txt file includes the following packages:

- ultralytics==8.1.6
- torch==2.1.2
- sahi==0.11.15
- geopandas==0.14.0
- pandas==1.5.3
- pillow==9.5.0

For CUDA support, ensure you install the CUDA version of PyTorch that matches your system's CUDA installation. This can significantly improve performance for GPU-accelerated computing. Visit the PyTorch official website for specific installation instructions related to different CUDA versions.

After installing the required packages, adjust the PROJ_LIB, mrsid_decoder_path, and model_path in the script to match your environment and proceed with the usage instructions.

## Usage

```sh
python SLICE_DET.py --proj_lib [path] --mrsid_decoder_path [path] --model_path [path] --objects [object names] --model_type yolov8 --model_device [device] --model_confidence_threshold [threshold] --slice_height [height] --slice_width [width] --overlap_height_ratio [ratio] --overlap_width_ratio [ratio] --source_image_dir [directory] --out_dir [output directory] --workers [number of workers] --merge [True/False]
```
## Contributing
Contributions are welcome! Please fork the repository and submit pull requests with any enhancements, bug fixes, or improvements.

## Future Improvements
- Better Error Handling
- Fencing around CUDA
- Smarter Model Handling for Relevant GSD based Models
- Training Scripts
- Geo Files to Annotated Data
- Training Data Out
- Other Types of YOLOV8 Model Handling

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.


