import pydicom
import numpy as np
from PIL import Image
import os
from pathlib import Path
import sys

def dicom_to_png(dicom_path, output_path=None, window_center=None, window_width=None):
    """
    Convert a DICOM image to PNG format with optional windowing parameters.
    
    Args:
        dicom_path (str): Path to the input DICOM file
        output_path (str): Path for the output PNG file (optional)
        window_center (int): Center of the window for contrast adjustment (optional)
        window_width (int): Width of the window for contrast adjustment (optional)
    
    Returns:
        str: Path to the saved PNG file
    """
    try:
        # Read the DICOM file
        dicom = pydicom.dcmread(dicom_path)
        
        # Extract the pixel array
        image = dicom.pixel_array
        
        # Apply windowing if parameters are provided
        if window_center is not None and window_width is not None:
            min_value = window_center - window_width // 2
            max_value = window_center + window_width // 2
            image = np.clip(image, min_value, max_value)
        
        # Normalize pixel values to 0-255 range
        if image.max() != image.min():
            image = ((image - image.min()) / (image.max() - image.min()) * 255).astype(np.uint8)
        else:
            image = np.zeros_like(image, dtype=np.uint8)
        
        # Convert to PIL Image
        pil_image = Image.fromarray(image)
        
        # Generate output path if not provided
        if output_path is None:
            input_path = Path(dicom_path)
            output_path = input_path.with_suffix('.png')
        
        # Save as PNG
        pil_image.save(output_path, 'PNG')
        return output_path
        
    except Exception as e:
        raise Exception(f"Error converting DICOM to PNG: {str(e)}")

def batch_convert_dicom_to_png(input_directory, output_directory=None):
    """
    Convert all DICOM files in a directory to PNG format.
    
    Args:
        input_directory (str): Directory containing DICOM files
        output_directory (str): Directory for output PNG files (optional)
    
    Returns:
        list: List of paths to converted PNG files
    """
    if output_directory is None:
        output_directory = os.path.join(input_directory, 'png_output')
    
    os.makedirs(output_directory, exist_ok=True)
    converted_files = []
    
    for file in os.listdir(input_directory):
        if file.endswith(('.dcm', '.dicom', '.DCM', '.DICOM')):
            input_path = os.path.join(input_directory, file)
            output_path = os.path.join(output_directory, f"{os.path.splitext(file)[0]}.png")
            
            try:
                converted_path = dicom_to_png(input_path, output_path)
                converted_files.append(converted_path)
            except Exception as e:
                print(f"Failed to convert {file}: {str(e)}")
    
    return converted_files

# Example usage
if __name__ == "__main__":
    # Convert a single DICOM file
    if len(sys.argv) > 1:
        dicom_to_png(sys.argv[1], sys.argv[2])
    else:
        dicom_to_png("data/L1.dcm", "output.png")
    
    # Convert all DICOM files in a directory
    if len(sys.argv) > 1:
        batch_convert_dicom_to_png(sys.argv[1], sys.argv[2])
    else:
        batch_convert_dicom_to_png("data", "output")