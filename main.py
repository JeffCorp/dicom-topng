import argparse
import csv
import logging
import os
from typing import List

import numpy as np
import pydicom
from PIL import Image

from utils.text_reader import DicomTextReader

logging.basicConfig(level=logging.INFO)


def dicom_to_png(
    dicom_path: str,
    output_path: str = None,
    window_center: int = None,
    window_width: int = None,
) -> str:
    """
    Convert a DICOM image to PNG format with optional windowing parameters.

    Parameters:
        dicom_path (str): Path to the input DICOM file or directory
        output_path (str): Path for the output PNG file (optional)
        window_center (int): Center of the window for contrast adjustment (optional)
        window_width (int): Width of the window for contrast adjustment (optional)

    Returns:
        str: Path to the saved PNG file

    Example:
        dicom_to_png('path/to/dicom/file.dcm', 'path/to/output/image.png', 50, 350)
    """
    file_name = os.path.basename(dicom_path)
    try:
        # Read the DICOM file
        dicom = pydicom.dcmread(dicom_path)

        # Extract the pixel array
        try:
            image = dicom.pixel_array.astype(np.float64)
        except AttributeError:
            raise Exception("DICOM file does not contain pixel data")

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
        raise Exception(f"DICOM file not found: {dicom_path}")
    except pydicom.errors.InvalidDicomError:
        raise Exception(f"Invalid DICOM file: {dicom_path}")
    except Exception as e:
        raise Exception(f"Error converting DICOM to PNG: {str(e)}")


def batch_convert_dicom_to_png(
    input_directory: str, output_directory: str = None
) -> List[str]:
    """
    Convert all DICOM files in a directory to PNG format.

    Parameters:
        input_directory (str): Directory containing DICOM files
        output_directory (str): Directory for output PNG files (optional)

    Returns:
        list: List of paths to converted PNG files

    Example:
        batch_convert_dicom_to_png('path/to/dicom/directory', 'path/to/output/directory')
    """
    if output_directory is None:
        folder = os.path.basename(input_directory)
        output_directory = os.path.join("output", folder)

    os.makedirs(f"{output_directory}/png", exist_ok=True)
    converted_files = []

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
                logging.info(f"Successfully converted: {file}")
            except Exception as e:
                logging.error(f"Failed to convert {file}: {str(e)}")

    logging.info(
        f"Conversion completed. Converted files: {len(converted_files)}"
    )

    return converted_files


def write_to_csv(
    png_files: List[str],
    dicom_path: str,
    files: bool = False,
    save_path: str = None,
) -> None:
    """
    Write patient and study information to a CSV file.

    Parameters:
        png_files (List[str]): List of paths to the converted PNG files
        dicom_path (str): Path to the DICOM file or directory
        files (bool): Flag to specify if the input was a list of files (optional)
        save_path (str): Path to save the CSV file (optional)

    Example:
        write_to_csv(['path/to/image1.png', 'path/to/image2.png'], 'path/to/dicom/')
    """
    if len(png_files) == 0:
        logging.warning("No PNG files found for writing to CSV")
        return

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


def main():
    """Main function to handle command-line arguments and execute the script."""
    parser = argparse.ArgumentParser(
        description="Convert DICOM files to PNG and optionally write metadata to CSV."
    )

    # Create mutually exclusive group for file and directory
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
    args = parser.parse_args()

    if args.directory:
        if os.path.isdir(args.directory):
            converted_files = batch_convert_dicom_to_png(
                args.directory, args.output
            )
            if args.csv:
                if args.output:
                    write_to_csv(
                        converted_files, args.directory, False, args.output
                    )
                else:
                    write_to_csv(converted_files, args.directory)
        else:
            print("Invalid directory path")
    elif args.file:
        all_converted_files = []
        invalid_files = []
        for file_path in args.file:
            if os.path.isfile(file_path):
                try:
                    if args.output:
                        converted_file = dicom_to_png(
                            file_path, f"{args.output}/png"
                        )
                    else:
                        converted_file = dicom_to_png(file_path)
                    all_converted_files.append(converted_file)
                except Exception as e:
                    print(f"Error converting file {file_path}: {e}")
            else:
                invalid_files.append(file_path)

        if args.csv and all_converted_files:
            if args.output:
                write_to_csv(
                    all_converted_files,
                    os.path.dirname(args.file[0]),
                    True,
                    args.output,
                )
            else:
                write_to_csv(
                    all_converted_files, os.path.dirname(args.file[0]), True
                )

        if invalid_files:
            print(f"Invalid file paths: {', '.join(invalid_files)}")

    else:
        print(
            "Usage: python main.py [-d <dicom_file_dir>] [-f <dicom_file_path> ...] -o <output_file_dir> [--csv]"
        )
        parser.print_help()


if __name__ == "__main__":
    main()
