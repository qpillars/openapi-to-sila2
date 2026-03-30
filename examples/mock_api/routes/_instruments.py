from typing import List
from fastapi import APIRouter, Depends, status
from schemas.instruments import (
    Instrument,
    InstrumentCreate,
)
from services._instrument_service import InstrumentService
from services._login_service import LoginService

router = APIRouter(prefix="/instruments", tags=["Instruments"])


def get_instrument_service() -> InstrumentService:
    """Dependency for instrument service"""

    return InstrumentService()


def get_login_service() -> LoginService:
    """Dependency for login service"""

    return LoginService()


@router.get("/", response_model=List[Instrument])
def list_instruments(
    service: InstrumentService = Depends(get_instrument_service),
) -> List[Instrument]:
    """Get all registered laboratory instruments
    
    Returns:
        List of available instruments
    """

    return service.get_available_instruments()


@router.get("/{instrument_id}", response_model=Instrument)
def get_instrument_status(
    instrument_id: int,
    service: InstrumentService = Depends(get_instrument_service),
) -> Instrument:
    """Get detailed status of an instrument
    
    Args:
        instrument_id: ID of the instrument
        
    Returns:
        Instrument status with state and metadata
    """

    return service.get_instrument_status(instrument_id)


@router.post("/", response_model=Instrument, status_code=status.HTTP_201_CREATED)
def register_new_instrument(
    payload: InstrumentCreate,
    service: InstrumentService = Depends(get_instrument_service),
    _: dict = Depends(get_login_service().require_role("admin")),
) -> Instrument:
    """Register a new laboratory instrument (admin only)
    
    Args:
        payload: Instrument details
        service: Instrument service instance
        _: Login context
    Returns:
        Created instrument
    """

    return service.register_instrument(payload)


@router.post("/{instrument_id}/calibrate", response_model=Instrument)
def calibrate_instrument(
    instrument_id: int,
    service: InstrumentService = Depends(get_instrument_service),
    _: dict = Depends(get_login_service().require_role("admin")),
) -> Instrument:
    """Calibrate an instrument (admin only)
    
    Updates calibration timestamp and schedules next maintenance.
    
    Args:
        instrument_id: ID of instrument to calibrate
        service: Instrument service instance
        _: Login context
    Returns:
        Updated instrument with new calibration timestamp
    """

    return service.calibrate_instrument(instrument_id)


@router.put("/{instrument_id}/retire", response_model=Instrument)
def retire_instrument(
    instrument_id: int,
    service: InstrumentService = Depends(get_instrument_service),
    _: dict = Depends(get_login_service().require_role("admin")),
) -> Instrument:
    """Retire an instrument from service (admin only)
    
    Args:
        instrument_id: ID of instrument to retire
        service: Instrument service instance
        _: Login context
    Returns:
        Updated instrument with maintenance state
    """
    
    service.retire_instrument(instrument_id)
    return service.get_instrument_status(instrument_id)
