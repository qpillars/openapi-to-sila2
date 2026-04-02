from datetime import datetime

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Login request model"""

    username: str = "admin"


class LoginResponse(BaseModel):
    """Login response model"""

    access_token: str
    token_type: str = "bearer"


class MeasurementReading(BaseModel):
    """Real-time measurement reading for streaming"""

    instrument_id: int = Field(..., description="Source instrument ID")
    instrument_name: str = Field(..., description="Source instrument name")
    value: float = Field(..., description="Current measurement value")
    unit: str = Field(..., description="Unit of measurement")
    timestamp: datetime = Field(..., description="Reading timestamp")
    status: str = Field(default="ok", description="Measurement status (ok, warning, error)")
    metadata: dict | None = Field(None, description="Optional additional data")


class StreamEvent(BaseModel):
    """Generic stream event container"""

    event_type: str = Field(..., description="Type of event (measurement, status, etc.)")
    data: dict = Field(..., description="Event data")
    timestamp: datetime = Field(..., description="Event timestamp")
