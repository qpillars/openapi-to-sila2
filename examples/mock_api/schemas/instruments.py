from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class InstrumentType(str, Enum):
    """Laboratory instrument types"""

    MICROSCOPE = "microscope"
    CENTRIFUGE = "centrifuge"
    SPECTROMETER = "spectrometer"
    BALANCE = "balance"


class InstrumentState(str, Enum):
    """State of an instrument"""

    IDLE = "idle"
    CALIBRATING = "calibrating"
    RUNNING = "running"
    MAINTENANCE = "maintenance"
    ERROR = "error"


class InstrumentBase(BaseModel):
    """Base instrument model"""

    name: str = Field(..., min_length=1, max_length=100, description="Name of the instrument")
    type: InstrumentType = Field(..., description="Type of laboratory instrument")
    manufacturer: str = Field(..., min_length=1, max_length=100, description="Instrument manufacturer")
    model: str = Field(..., min_length=1, max_length=100, description="Instrument model number")
    year: int = Field(..., ge=1900, le=2100, description="Year of manufacture")


class Instrument(InstrumentBase):
    """Full instrument model with runtime state"""

    id: int = Field(..., description="Unique instrument identifier")
    state: InstrumentState = Field(default=InstrumentState.IDLE, description="Current state of the instrument")
    last_calibration: datetime | None = Field(None, description="Timestamp of last calibration")
    next_maintenance: datetime | None = Field(None, description="Scheduled maintenance date")
    measurement_count: int = Field(default=0, description="Total number of measurements recorded")
    specifications: dict = Field(default_factory=dict, description="Technical specifications")

    class Config:
        from_attributes = True


class InstrumentCreate(InstrumentBase):
    """Model for creating new instruments"""

    specifications: dict | None = Field(None, description="Optional technical specifications")
