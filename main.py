import argparse
import csv
import logging
import os
from logging.handlers import RotatingFileHandler
from typing import List, Optional

import numpy as np
import pydicom
from PIL import Image

from utils.text_reader import DicomTextReader

# Configure logging with RotatingFileHandler
log_handler = RotatingFileHandler(
    "dicom_to_png.log",
    maxBytes=5 * 1024 * 1024,  # 5 MB
    backupCount=5,  # Keep up to 5 backup files
)
log_handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
log_handler.setFormatter(formatter)

# Add handler to the root logger
logging.getLogger().addHandler(log_handler)
logging.getLogger().setLevel(logging.INFO)


def dicom_to_png(
    dicom_path: str,
    output_path: Optional[str] = None,
    window_center: Optional[int] = None,
    window_width: Optional[int] = None,
) -> str:
    """
    Convert a DICOM image to PNG format with optional windowing parameters.

    Parameters:
        dicom_path (str): Path to the input DICOM file or directory
        output_path (str): Path for the output PNG file (optional)
        window_center (int): Center of the window for contrast adjustment \
            (optional)
        window_width (int): Width of the window for contrast adjustment \
            (optional)

    Returns:
        str: Path to the saved PNG file

    Example:
        dicom_to_png('path/to/dicom/file.dcm', 'path/to/output/image.png', 50\
            , 350)
    """
    file_name = os.path.basename(dicom_path)
    try:
        # Read the DICOM file
        dicom = pydicom.dcmread(dicom_path)

        # Extract the pixel array
        try:
            image = dicom.pixel_array.astype(np.float64)
        except AttributeError:
            raise AttributeError("DICOM file does not contain pixel data")

        # Apply windowing if parameters are provided
        if window_center is not None and window_width is not None:
            min_value = window_center - window_width // 2
            max_value = window_center + window_width // 2
            image = np.clip(image, min_value, max_value)

        # Normalize pixel values to 0-255 range
        if image.max() != image.min():
            image = (
                (image - image.min()) / (image.max() - image.min()) * 255
            ).astype(np.uint8)
        else:
            image = np.zeros_like(image, dtype=np.uint8)

        # Convert to PIL Image
        pil_image = Image.fromarray(image)

        # Generate output path if not provided
        if output_path is None:
            output_path = "output/png"
            if not os.path.exists(output_path):
                os.makedirs(output_path, exist_ok=True)
        elif not os.path.exists(
            output_path
        ) and not output_path.lower().endswith(".png"):
            os.makedirs(output_path, exist_ok=True)

        # Save PNG file with the same name as the DICOM file
        if not output_path.lower().endswith(".png"):
            output_path = os.path.join(
                output_path, f"{os.path.splitext(file_name)[0]}.png"
            )

        # Save as PNG
        pil_image.save(output_path, "PNG")
        logging.info(f"Saved PNG file: {output_path}")
        return output_path

    except FileNotFoundError:
        logging.error(f"DICOM file not found: {dicom_path}")
        raise FileNotFoundError(f"DICOM file not found: {dicom_path}")
    except pydicom.errors.InvalidDicomError:
        logging.error(f"Invalid DICOM file: {dicom_path}")
        raise pydicom.errors.InvalidDicomError(
            f"Invalid DICOM file: {dicom_path}"
        )
    except Exception as e:
        logging.error(f"Error converting DICOM to PNG: {str(e)}")
        raise Exception(f"Error converting DICOM to PNG: {str(e)}")


def batch_convert_dicom_to_png(
    input_directory: str, output_directory: Optional[str] = None
) -> tuple[List[str], List[str]]:
    """
    Convert all DICOM files in a directory to PNG format.

    Parameters:
        input_directory (str): Directory containing DICOM files
        output_directory (str): Directory for output PNG files (optional)

    Returns:
        tuple: List of paths to the converted PNG files and DICOM files

    Example:
        batch_convert_dicom_to_png('path/to/dicom/directory', \
            'path/to/output/directory')
    """
    if output_directory is None:
        folder = os.path.basename(input_directory)
        output_directory = os.path.join("output", folder)

    os.makedirs(f"{output_directory}/png", exist_ok=True)
    converted_files = []
    dicom_files = []

    logging.info(
        f"Starting conversion for files in directory: {input_directory}"
    )

    for file in os.listdir(input_directory):
        if file.lower().endswith((".dcm", ".dicom")):
            input_path = os.path.join(input_directory, file)
            output_path = os.path.join(
                output_directory, "png", f"{os.path.splitext(file)[0]}.png"
            )
            try:
                converted_files.append(dicom_to_png(input_path, output_path))
                dicom_files.append(input_path)
                logging.info(f"Successfully converted: {file}")
            except Exception as e:
                logging.error(f"Failed to convert {file}: {str(e)}")

    logging.info(
        f"Conversion completed. Converted files: {len(converted_files)}"
    )

    return (converted_files, dicom_files)


def write_to_csv(
    png_files: List[str],
    dicom_path: str,
    files: bool = False,
    save_path: Optional[str] = None,
) -> None:
    """
    Write patient and study information to a CSV file.

    Parameters:
        png_files (List[str]): List of paths to the converted PNG files
        dicom_path (str): Path to the DICOM file or directory
        files (bool): Flag to specify if the input was a list of files \
            (optional)
        save_path (str): Path to save the CSV file (optional)

    Example:
        write_to_csv(['path/to/image1.png', 'path/to/image2.png'], \
            'path/to/dicom/')
    """
    if len(png_files) == 0:
        logging.warning("No PNG files found for writing to CSV")
        return

    if dicom_path.endswith("/") or dicom_path.endswith("\\"):
        dicom_path = dicom_path.removesuffix("/")
        dicom_path = dicom_path.removesuffix("\\")

    if files:
        if save_path:
            csv_file_path = f"{save_path}/patient_info.csv"
        else:
            csv_file_path = "output/patient_info.csv"
    elif save_path:
        csv_file_path = f"{save_path}/{os.path.basename(dicom_path)}.csv"
    else:
        csv_file_path = f"output/{os.path.basename(dicom_path)}.csv"

    if not os.path.exists("output/") and not save_path:
        os.makedirs("output/", exist_ok=True)

    with open(csv_file_path, mode="w", newline="") as csv_file:
        fieldnames = [
            "patient_id",
            "exam_id",
            "laterality",
            "view",
            "file_path",
            # Additional fields can be uncommented as needed
            # "years_to_cancer",
            # "years_to_last_followup",
            # "split_group"
        ]
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

        writer.writeheader()

        for png in png_files:
            dicom_file = os.path.join(
                dicom_path, os.path.splitext(os.path.basename(png))[0] + ".dcm"
            )
            try:
                text_reader = DicomTextReader(dicom_file)
                patient_info = text_reader.get_patient_info()
                study_info = text_reader.get_study_info()

                writer.writerow(
                    {
                        "patient_id": patient_info.get("PatientID", "N/A"),
                        "exam_id": 0,
                        "laterality": study_info.get("Laterality", "N/A"),
                        "view": study_info.get("ViewPosition", "N/A"),
                        "file_path": png.replace("\\", "/"),
                        # Uncomment and populate additional fields as needed
                        # "years_to_cancer": years_to_cancer,
                        # "years_to_last_followup": years_to_last_followup,
                        # "split_group": split_group
                    }
                )
            except Exception as e:
                logging.error(f"Failed to process {dicom_file}: {str(e)}")
                continue

    logging.info(f"CSV file saved: {csv_file_path}")


def add_metadata_to_files(dicom_files):
    """Add metadata to DICOM files."""
    for file in dicom_files:
        DicomTextReader(file, True)
        logging.info(f"Added metadata to {file}")


def delete_backup_files(dicom_files):
    """Delete backup files."""
    logging.info("Deleting backup files")
    for file in dicom_files:
        backup_file = file + ".bak"
        try:
            os.remove(backup_file)
            logging.info(f"Deleted {backup_file}")
        except FileNotFoundError:
            logging.warning(f"Backup file not found: {backup_file}")
    logging.info("Deleted all backup files")


def process_files(files, output):
    """Process each file and convert if valid."""
    all_converted_files = []
    invalid_files = []
    for file_path in files:
        if os.path.isfile(file_path):
            try:
                converted_file = dicom_to_png(
                    file_path, f"{output}/png" if output else None
                )
                all_converted_files.append(converted_file)
                logging.info(f"Converted {file_path} to PNG")
            except Exception as e:
                logging.error(f"Error converting file {file_path}: {e}")
                print(f"Error converting file {file_path}: {e}")
        else:
            invalid_files.append(file_path)
    return all_converted_files, invalid_files


def create_csv(all_converted_files, files, output):
    """Create a CSV file with metadata of converted files."""
    write_to_csv(all_converted_files, os.path.dirname(files[0]), True, output)
    logging.info("CSV file created with metadata of converted files")


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Convert DICOM files to PNG and optionally write metadata \
            to CSV."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "-d", "--directory", type=str, help="Directory containing DICOM files."
    )
    group.add_argument(
        "-f",
        "--file",
        nargs="+",
        type=str,
        help="Path(s) to one or more DICOM files.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Directory for output PNG and CSV files.",
    )
    parser.add_argument(
        "--csv",
        action="store_true",
        help="Flag to write metadata to a CSV file.",
    )
    parser.add_argument(
        "--add-metadata",
        action="store_true",
        help="Flag to extract additional metadata from DICOM files.",
    )
    parser.add_argument(
        "--delete-backup",
        action="store_true",
        help="Flag to delete backup files.",
    )
    return parser.parse_args()


def handle_directory_conversion(
    directory, output, csv_flag, add_metadata, delete_backup
):
    """Handle conversion of DICOM files in a directory."""
    if not os.path.isdir(directory):
        logging.error("Invalid directory path")
        print("Invalid directory path")
        return

    converted_files, dicom_files = batch_convert_dicom_to_png(directory,
                                                              output)
    if csv_flag:
        write_to_csv(converted_files, directory, False, output)
    logging.info(f"Converted all files in directory {directory}")

    if add_metadata:
        add_metadata_to_files(dicom_files)

    if delete_backup:
        delete_backup_files(dicom_files)


def handle_file_conversion(
    files, output, csv_flag, add_metadata, delete_backup
):
    """Handle conversion of individual DICOM files."""
    all_converted_files, invalid_files = process_files(files, output)

    if csv_flag and all_converted_files:
        create_csv(all_converted_files, files, output)

    if add_metadata:
        add_metadata_to_files(files)

    if delete_backup:
        delete_backup_files(files)

    if invalid_files:
        logging.warning(f"Invalid file paths: {', '.join(invalid_files)}")
        print(f"Invalid file paths: {', '.join(invalid_files)}")


def main():
    """
    Main function to handle command-line arguments and execute the script.
    """
    parser = argparse.ArgumentParser(
        description="Convert DICOM files to PNG and optionally write metadata \
            to CSV."
    )
    args = parse_arguments()

    if args.directory:
        handle_directory_conversion(
            args.directory,
            args.output,
            args.csv,
            args.add_metadata,
            args.delete_backup,
        )
    elif args.file:
        handle_file_conversion(
            args.file,
            args.output,
            args.csv,
            args.add_metadata,
            args.delete_backup,
        )
    else:
        print(
            "Usage: python main.py [-d <dicom_file_dir>] [-f \
                <dicom_file_path> ...] -o <output_file_dir> [--csv] \
                    [--add-metadata] [--delete-backup]"
        )
        parser.print_help()


if __name__ == "__main__":
    main()
