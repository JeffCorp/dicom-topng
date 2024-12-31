import json
import logging
import os
import subprocess
from datetime import date, datetime, time
from typing import Any, Dict, Optional

import pydicom
from pydicom.dataset import Dataset


class DicomTextReader:
    def __init__(self, filepath: str, modfiy: bool = False):
        """
        Initialize DicomTextReader with a DICOM file path

        Args:
            filepath (str): Path to the DICOM file
        """
        self.filepath = filepath
        self.dataset = pydicom.dcmread(filepath)
        if modfiy:
            self.get_study_info(modfiy=True)

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
            return value.decode("ascii", errors="ignore")
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
            if elem.VR != "SQ":  # Skip sequence elements
                try:
                    # Get human-readable tag name
                    tag_name = elem.name.replace(" ", "_")
                    # Convert value to serializable format
                    value = self._convert_value(elem.value)
                    data_dict[tag_name] = {
                        "value": value,
                        "VR": elem.VR,  # Value Representation
                        "tag": f"({elem.tag.group:04x},\
                            {elem.tag.element:04x})",
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
            "PatientName",
            "PatientID",
            "PatientBirthDate",
            "PatientSex",
            "PatientAge",
            "PatientWeight",
        ]

        return {tag: self.dataset.get(tag, "") for tag in patient_tags}

    def write_info(
        self, laterality: Optional[str] = None, view: Optional[str] = None
    ):
        """
        Write the information of the DICOM file
        """
        dcm = self.dataset
        # Check if the DICOM file has the necessary tags
        # View position
        try:
            view_str = dcm.ViewPosition
            if view_str == "":
                view_str = view
        except AttributeError:
            view_str = dcm.ViewPosition
        # Laterality
        try:
            side_str = dcm.ImageLaterality
        except AttributeError:
            side_str = laterality
        series_str = dcm.SOPClassUID
        # Call `dcmodify` to write the information to the DICOM file
        # First check if dcmodify is installed
        try:
            result = subprocess.run(
                ["dcmodify", "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            if result.returncode != 0:
                raise OSError(
                    """dcmodify is not installed. Please install it first.
                        You can install it by running:
                        apt-get install dcmtk
                        or download it from:
                        https://dicom.offis.de/en/dcmtk/dcmtk-tools/
                        or on Windows with Chocolatey: `choco install dcmtk`
                    """
                )
        except FileNotFoundError:
            raise OSError(
                """dcmodify is not installed. Please install it first.
                    You can install it by running:
                    apt-get install dcmtk
                    or download it from:
                    https://dicom.offis.de/en/dcmtk/dcmtk-tools/
                    or on Windows with Chocolatey: `choco install dcmtk`
                """
            )
        # Ex: dcmodify -i "(0020,0062)=L" -i "(0008,103e)=Mammogram" file.dcm
        command = f'dcmodify -i "(0020,0062)={side_str}" -i "(0008,103e)=\
            {series_str}" {self.filepath}'
        process = subprocess.Popen(
            command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            print(f"Error executing command: {command}")
            print(f"Error message: {stdout.decode('utf-8')}")
            logging.error(f"Error executing command: {command}")
            logging.error(f"Error message: {stderr.decode('utf-8')}")

    def get_study_info(self, modfiy: bool = False) -> Dict[str, Any]:
        """
        Get study-specific information including laterality and view position

        Returns:
            Dictionary containing study information
        """
        study_tags = [
            "StudyDate",
            "StudyTime",
            "StudyDescription",
            "StudyID",
            "AccessionNumber",
            "ReferringPhysicianName",
            "Laterality",
            "ViewPosition",
        ]

        response = {tag: self.dataset.get(tag, "") for tag in study_tags}

        # Additional processing for view position and laterality
        acquisition_desc = self.dataset.get(
            "AcquisitionDeviceProcessingDescription"
        )
        if acquisition_desc:
            if "MLO" in acquisition_desc:
                response["ViewPosition"] = "MLO"
            elif "CC" in acquisition_desc:
                response["ViewPosition"] = "CC"

            if "R " in acquisition_desc:
                response["Laterality"] = "R"
            elif "L " in acquisition_desc:
                response["Laterality"] = "L"

        if modfiy:
            self.write_info(response["Laterality"], response["ViewPosition"])

        return response

    def save_to_json(self, output_path: Optional[str] = None) -> str:
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
        with open(output_path, "w") as f:
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
        print(
            f"Image Size: {getattr(self.dataset, 'Rows', 'N/A')}x{getattr(
                self.dataset, 'Columns', 'N/A')}"
        )
        print(
            f"Bits Allocated: {getattr(self.dataset, 'BitsAllocated', 'N/A')}"
        )
        print(
            f"Number of frames: {getattr(self.dataset,
                                         'NumberOfFrames', 1)}"
        )


def main():
    """Example usage of DicomTextReader"""
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
