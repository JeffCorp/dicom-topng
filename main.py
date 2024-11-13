import pydicom
import numpy as np
from PIL import Image
import os
from pathlib import Path
import sys
from utils.text_reader import DicomTextReader
import csv

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
    if (sys.argv[1] == "-s"):
      if len(sys.argv) > 2:
        dicom_to_png(sys.argv[2], sys.argv[3])
        
        text_reader = DicomTextReader(sys.argv[2])
        patient_info = text_reader.get_patient_info()
        study_info = text_reader.get_study_info()
        # laterality, view = mammogram_checker.read_text_from_image(sys.argv[3])

        # Create a CSV file with the patient and study information
        csv_file_path = "output/patient_study_info.csv" # Specify your desired output path

        with open(csv_file_path, mode='w', newline='') as csv_file:
          fieldnames = ['patient_id', 'exam_id', 'laterality', 'view', 'file_path', 'years_to_cancer', 'years_to_last_followup', 'split_group']  # Adjust fieldnames as needed
          writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

          writer.writeheader()
          writer.writerow({
              'patient_id': patient_info.get('PatientID', 'N/A'),
              'exam_id': 0,
              'laterality': study_info.get('Laterality', 'N/A'),
              'view': study_info.get('ViewPosition', 'N/A'),
              'file_path': sys.argv[3],
              'years_to_cancer': 0,
              'years_to_last_followup': 10,
              'split_group': 'test'
          })
      else:
          dicom_to_png("data/L1.dcm", "output.png")
    else:
        # Convert all DICOM files in a directory
        if len(sys.argv) > 1:
            converted_files = batch_convert_dicom_to_png(sys.argv[1], sys.argv[2])
            
            # Create a CSV file with the patient and study information
            csv_file_path = "patients_study_info.csv"  # Specify your desired output path
            with open(csv_file_path, mode='w', newline='') as csv_file:
                fieldnames = ['patient_id', 'exam_id', 'laterality', 'view', 'file_path', 'years_to_cancer', 'years_to_last_followup', 'split_group']  # Adjust fieldnames as needed
                writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                
                writer.writeheader()  
                for file in converted_files:
                    # Read patient info from the original DICOM file
                    dicom_file = file.replace('.png', '.dcm') 
                    modified_path = dicom_file.replace(sys.argv[2], sys.argv[1])# Assuming the original DICOM file has the same name
                    
                    try:
                      print(modified_path)
                      text_reader = DicomTextReader(modified_path)
                      patient_info = text_reader.get_patient_info()
                      study_info = text_reader.get_study_info()
                      
                      laterality = study_info.get('Laterality', 'N/A')
                      view = study_info.get('ViewPosition', 'N/A')
                      
                      writer.writerow({
                          'patient_id': patient_info.get('PatientID', 'N/A'),
                          'exam_id': 0,
                          'laterality': laterality,
                          'view': view,
                          'file_path': file,
                          'years_to_cancer': 0,
                          'years_to_last_followup': 10,
                          'split_group': 'test'
                      })
                    except Exception as e:
                      print(f"Failed to process {file}: {str(e)}")
                
        else:
            batch_convert_dicom_to_png("data", "output")