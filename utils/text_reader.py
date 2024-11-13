import pydicom
from pydicom.dataset import Dataset
from typing import Dict, Any, Union
import json
from datetime import datetime, date, time
import os

class DicomTextReader:
    def __init__(self, filepath: str):
        """
        Initialize DicomTextReader with a DICOM file path
        
        Args:
            filepath (str): Path to the DICOM file
        """
        self.filepath = filepath
        self.dataset = pydicom.dcmread(filepath)
    
    def _convert_value(self, value: Any) -> Any:
        """
        Convert DICOM value to a JSON-serializable format
        
        Args:
            value: DICOM data element value
        
        Returns:
            Converted value that can be serialized to JSON
        """
        if isinstance(value, (datetime, date, time)):
            return str(value)
        elif isinstance(value, bytes):
            return value.decode('ascii', errors='ignore')
        elif isinstance(value, pydicom.sequence.Sequence):
            return [self._convert_dataset_to_dict(item) for item in value]
        elif isinstance(value, pydicom.dataset.Dataset):
            return self._convert_dataset_to_dict(value)
        elif isinstance(value, (int, float, str, bool)):
            return value
        else:
            return str(value)
    
    def _convert_dataset_to_dict(self, dataset: Dataset) -> Dict[str, Any]:
        """
        Convert a DICOM dataset to a dictionary
        
        Args:
            dataset: DICOM dataset
        
        Returns:
            Dictionary containing DICOM metadata
        """
        data_dict = {}
        for elem in dataset:
            if elem.VR != 'SQ':  # Skip sequence elements
                try:
                    # Get human-readable tag name
                    tag_name = elem.name.replace(' ', '_')
                    # Convert value to serializable format
                    value = self._convert_value(elem.value)
                    data_dict[tag_name] = {
                        'value': value,
                        'VR': elem.VR,  # Value Representation
                        'tag': f'({elem.tag.group:04x},{elem.tag.element:04x})'
                    }
                except Exception as e:
                    print(f"Error processing tag {elem.tag}: {str(e)}")
        return data_dict
    
    def get_all_metadata(self) -> Dict[str, Any]:
        """
        Get all metadata from the DICOM file
        
        Returns:
            Dictionary containing all DICOM metadata
        """
        return self._convert_dataset_to_dict(self.dataset)
    
    def get_patient_info(self) -> Dict[str, Any]:
        """
        Get patient-specific information
        
        Returns:
            Dictionary containing patient information
        """
        patient_tags = [
            'PatientName', 'PatientID', 'PatientBirthDate',
            'PatientSex', 'PatientAge', 'PatientWeight'
        ]
        
        return {tag: self.dataset.get(tag, '') for tag in patient_tags}
    
    def get_study_info(self) -> Dict[str, Any]:
        """
        Get study-specific information including laterality and view position
        
        Returns:
            Dictionary containing study information
        """
        study_tags = [
            'StudyDate', 'StudyTime', 'StudyDescription',
            'StudyID', 'AccessionNumber', 'ReferringPhysicianName',
            'Laterality', 'ViewPosition'
        ]
        
        response = {tag: self.dataset.get(tag, '') for tag in study_tags}
        
        if (self.dataset.get('AcquisitionDeviceProcessingDescription')):
          data = self.dataset.get('AcquisitionDeviceProcessingDescription')
          
          if (data.find('MLO') != -1):
            response['ViewPosition'] = 'MLO'
          elif (data.find('CC') != -1):
            response['ViewPosition'] = 'CC'
            
          if (data.find('R ') != -1):
            response['Laterality'] = 'R'
          elif (data.find('L ') != -1):
            response['Laterality'] = 'L'
        
        return response
    
    def save_to_json(self, output_path: str = None) -> str:
        """
        Save DICOM metadata to JSON file
        
        Args:
            output_path (str): Path to save JSON file (optional)
        
        Returns:
            str: Path to the saved JSON file
        """
        if output_path is None:
            base_path = os.path.splitext(self.filepath)[0]
            output_path = f"{base_path}_metadata.json"
        
        metadata = self.get_all_metadata()
        with open(output_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        return output_path
    
    def print_summary(self):
        """Print a summary of key DICOM information"""
        print("\n=== DICOM File Summary ===")
        print(f"Filename: {os.path.basename(self.filepath)}")
        
        # Patient Information
        print("\nPatient Information:")
        patient_info = self.get_patient_info()
        for key, value in patient_info.items():
            print(f"{key}: {value}")
        
        # Study Information
        print("\nStudy Information:")
        study_info = self.get_study_info()
        for key, value in study_info.items():
            print(f"{key}: {value}")
        
        # Image Information
        print("\nImage Information:")
        print(f"Modality: {getattr(self.dataset, 'Modality', 'N/A')}")
        print(f"Image Size: {getattr(self.dataset, 'Rows', 'N/A')}x{getattr(self.dataset, 'Columns', 'N/A')}")
        print(f"Bits Allocated: {getattr(self.dataset, 'BitsAllocated', 'N/A')}")
        print(f"Number of frames: {getattr(self.dataset, 'NumberOfFrames', 1)}")

def main():
    """Example usage of DicomTextReader"""
    # Example usage
    dicom_path = "path/to/your/dicom/file.dcm"
    reader = DicomTextReader(dicom_path)
    
    # Print summary
    reader.print_summary()
    
    # Save complete metadata to JSON
    json_path = reader.save_to_json()
    print(f"\nComplete metadata saved to: {json_path}")
    
    # Get specific information
    patient_info = reader.get_patient_info()
    study_info = reader.get_study_info()
    
    # Print specific information
    print("\nPatient Information:")
    print(json.dumps(patient_info, indent=2))
    
    print("\nStudy Information:")
    print(json.dumps(study_info, indent=2))

if __name__ == "__main__":
    main()