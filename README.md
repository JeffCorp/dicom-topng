# dicom-topng

## Overview
`dicom-topng` is a Python-based tool designed to convert DICOM (Digital Imaging and Communications in Medicine) files to PNG (Portable Network Graphics) format. It also provides an optional feature to extract metadata from DICOM files and save it to a CSV file. This tool is particularly useful for healthcare professionals, researchers, and developers who work with medical imaging data and need to convert or analyze DICOM files efficiently.

## Features
- **Convert DICOM to PNG**: Convert individual DICOM files or entire directories containing DICOM files to PNG format.
- **Metadata Extraction**: Extract and save patient and study information from DICOM files to a CSV file.
- **Flexible Input Options**: Support for converting both single DICOM files and directories of DICOM files.
- **Customizable Output**: Option to specify the output directory for the converted PNG files and CSV file.

## Installation
To use `dicom-topng`, ensure you have Python installed on your system. You can install the required dependencies using the following command:

```bash
pip install -r requirements.txt
```

## Usage
You can use `dicom-topng` from the command line. The script supports various command-line options to specify input files, directories, and output locations.

### Convert Directory of DICOM Files
To convert all DICOM files in a directory to PNG format:
```bash
python main.py -d <dicom_file_dir> -o <output_file_dir> [--csv]
```
- `-d | --directory`: Path to the directory containing DICOM files.
- `-o | --output`: (Optional) Directory for the output PNG and CSV files.
- `--csv`: (Optional) Flag to write metadata to a CSV file.

### Convert Single or Multiple DICOM Files
To convert one or more DICOM files to PNG format:
```bash
python main.py -f <dicom_file_path1> <dicom_file_path2> ... -o <output_file_dir> [--csv]
```
- `-f | --file`: Path(s) to one or more DICOM files.
- `-o | --output`: (Optional) Directory for the output PNG and CSV files.
- `--csv`: (Optional) Flag to write metadata to a CSV file.

### Examples
Convert all DICOM files in a directory and save the results to a specified output directory:
```bash
python main.py -d dicom_files/ -o output/ --csv
```

Convert multiple DICOM files and save the results to a specified output directory without CSV:
```bash
python main.py -f file1.dcm file2.dcm file3.dcm -o output/
```

## Project Structure
- `main.py`: The main script to execute the conversion and metadata extraction.
- `utils/text_reader.py`: Utility module to read and process DICOM files.

## Contributions
Contributions to the `dicom-topng` project are welcome! If you encounter any issues, have suggestions for new features, or want to contribute code, please create an issue or submit a pull request on the project's GitHub repository.

## Authors
1. Jeffrey Ukutegbe
2. Ayomide Ayodele-Soyebo
3. Adolphus Eze

## License
This project is licensed under the MIT License. See the `LICENSE` file for more details.

## Acknowledgements
Special thanks to all contributors and the open-source community for their support and contributions to this project.
