"""Data models for representing lab instrument data."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path
import pandas as pd
from pydantic import BaseModel, Field


class Metadata(BaseModel):
    """Metadata about the instrument run."""

    instrument_type: Optional[str] = None
    instrument_serial: Optional[str] = None
    instrument_model: Optional[str] = None
    software_version: Optional[str] = None
    method_name: Optional[str] = None
    sample_name: Optional[str] = None
    operator: Optional[str] = None
    run_date: Optional[datetime] = None
    runtime_minutes: Optional[float] = None
    injection_volume: Optional[float] = None
    injection_volume_units: Optional[str] = "µL"
    flow_rate: Optional[float] = None
    flow_rate_units: Optional[str] = "mL/min"
    column_name: Optional[str] = None
    column_temperature: Optional[float] = None
    column_temperature_units: Optional[str] = "°C"
    detector_type: Optional[str] = None
    detector_wavelength: Optional[float] = None
    detector_wavelength_units: Optional[str] = "nm"
    raw_metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True


class Peak(BaseModel):
    """Represents a detected peak in chromatogram data."""

    retention_time: float  # minutes
    area: Optional[float] = None
    height: Optional[float] = None
    width: Optional[float] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    area_percent: Optional[float] = None
    compound_name: Optional[str] = None
    peak_number: Optional[int] = None

    class Config:
        arbitrary_types_allowed = True


class Chromatogram(BaseModel):
    """Time-series signal data from the detector."""

    time: List[float]  # retention time in minutes
    signal: List[float]  # detector response
    time_units: str = "minutes"
    signal_units: str = "mAU"  # milliabsorbance units (common for UV detectors)
    channel_name: Optional[str] = None
    wavelength: Optional[float] = None

    class Config:
        arbitrary_types_allowed = True

    def to_dataframe(self) -> pd.DataFrame:
        """Convert chromatogram to pandas DataFrame."""
        return pd.DataFrame({
            "time": self.time,
            "signal": self.signal
        })


class LabData(BaseModel):
    """Main data container for parsed lab instrument data."""

    metadata: Metadata
    chromatogram: Optional[Chromatogram] = None
    peaks: List[Peak] = Field(default_factory=list)
    source_file: Optional[str] = None
    parser_version: str = "0.1.0"

    class Config:
        arbitrary_types_allowed = True

    def to_csv(self, filepath: str, include_metadata: bool = True) -> None:
        """
        Export data to CSV format.

        Args:
            filepath: Output file path
            include_metadata: If True, includes metadata as header comments
        """
        output_path = Path(filepath)

        # Write metadata as comments
        if include_metadata:
            with open(output_path, 'w') as f:
                f.write(f"# Sample: {self.metadata.sample_name}\n")
                f.write(f"# Instrument: {self.metadata.instrument_model}\n")
                f.write(f"# Run Date: {self.metadata.run_date}\n")
                f.write(f"# Method: {self.metadata.method_name}\n")
                f.write("#\n")

        # Write chromatogram data
        if self.chromatogram:
            df = self.chromatogram.to_dataframe()
            df.to_csv(output_path, mode='a', index=False)

        # Write peaks to separate file if present
        if self.peaks:
            peaks_df = pd.DataFrame([p.model_dump() for p in self.peaks])
            peaks_path = output_path.with_stem(output_path.stem + "_peaks")
            peaks_df.to_csv(peaks_path, index=False)

    def to_json(self, filepath: str) -> None:
        """Export data to JSON format."""
        output_path = Path(filepath)
        with open(output_path, 'w') as f:
            f.write(self.model_dump_json(indent=2))

    def to_parquet(self, filepath: str, normalize: bool = False) -> None:
        """
        Export chromatogram data to Parquet format (ML-ready).

        Args:
            filepath: Output file path
            normalize: If True, normalizes signal to 0-1 range
        """
        try:
            import pyarrow.parquet as pq
        except ImportError:
            raise ImportError(
                "pyarrow is required for Parquet export. "
                "Install it with: pip install pyarrow"
            )

        if self.chromatogram is None:
            raise ValueError("No chromatogram data to export")

        df = self.chromatogram.to_dataframe()

        if normalize:
            df['signal'] = (df['signal'] - df['signal'].min()) / \
                          (df['signal'].max() - df['signal'].min())

        # Add metadata as columns
        df['sample_name'] = self.metadata.sample_name
        df['run_date'] = self.metadata.run_date
        df['instrument'] = self.metadata.instrument_model

        df.to_parquet(filepath, index=False)

    def to_animl(self, filepath: str) -> None:
        """
        Export to AnIML (Analytical Information Markup Language) format.

        Note: Basic implementation. Full AnIML spec is complex.
        """
        raise NotImplementedError("AnIML export coming in v0.2.0")

    def __str__(self) -> str:
        """String representation of LabData."""
        return (
            f"LabData("
            f"sample={self.metadata.sample_name}, "
            f"instrument={self.metadata.instrument_model}, "
            f"peaks={len(self.peaks)}, "
            f"points={len(self.chromatogram.time) if self.chromatogram else 0}"
            f")"
        )
