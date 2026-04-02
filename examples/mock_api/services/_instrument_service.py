from datetime import datetime, timedelta, timezone
from typing import TypedDict

from fastapi import HTTPException
from schemas.instruments import (
    Instrument,
    InstrumentCreate,
    InstrumentState,
    InstrumentType,
)


class InstrumentData(TypedDict):
    """Type definition for instrument initialization data"""

    name: str
    type: InstrumentType
    manufacturer: str
    model: str
    year: int


_INSTRUMENTS: dict = {}
_INSTRUMENT_COUNTER = 0


class InstrumentService:
    """Service for managing instruments"""

    def __init__(self):
        self._initialize_fixtures()

    def _initialize_fixtures(self):
        """Initialize with sample instruments"""

        global _INSTRUMENT_COUNTER, _INSTRUMENTS

        sample_instruments: list[InstrumentData] = [
            {
                "name": "Precision Balance A",
                "type": InstrumentType.BALANCE,
                "manufacturer": "Ohaus",
                "model": "PA413C",
                "year": 2022,
            },
            {
                "name": "Centrifuge Z3",
                "type": InstrumentType.CENTRIFUGE,
                "manufacturer": "Hermle",
                "model": "Z 36 HK",
                "year": 2021,
            },
            {
                "name": "Spectrometer UV-Vis",
                "type": InstrumentType.SPECTROMETER,
                "manufacturer": "PerkinElmer",
                "model": "Lambda 25",
                "year": 2020,
            },
        ]

        for inst_data in sample_instruments:
            _INSTRUMENT_COUNTER += 1
            _INSTRUMENTS[_INSTRUMENT_COUNTER] = Instrument(
                id=_INSTRUMENT_COUNTER,
                **inst_data,
                state=InstrumentState.IDLE,
                last_calibration=datetime.now(timezone.utc) - timedelta(days=30),
                next_maintenance=datetime.now(timezone.utc) + timedelta(days=60),
                measurement_count=0,
                specifications={},
            )

    def register_instrument(self, payload: InstrumentCreate) -> Instrument:
        """Register a new instrument

        Args:
            payload: Instrument creation data

        Returns:
            Created instrument
        """

        global _INSTRUMENT_COUNTER

        _INSTRUMENT_COUNTER += 1

        instrument = Instrument(
            id=_INSTRUMENT_COUNTER,
            **payload.model_dump(),
            state=InstrumentState.IDLE,
            last_calibration=None,
            next_maintenance=datetime.now(timezone.utc) + timedelta(days=90),
            measurement_count=0,
        )
        _INSTRUMENTS[_INSTRUMENT_COUNTER] = instrument

        return instrument

    def get_available_instruments(self, limit: int = 100, offset: int = 0) -> list[Instrument]:
        """Get all registered instruments

        Returns:
            List of instruments
        """

        instruments = list(_INSTRUMENTS.values())
        return instruments[offset : offset + limit]

    def get_instrument_status(self, instrument_id: int) -> Instrument:
        """Get detailed status of an instrument

        Args:
            instrument_id: Instrument ID

        Returns:
            Instrument details

        Raises:
            HTTPException: If instrument not found
        """

        instrument = _INSTRUMENTS.get(instrument_id)

        if instrument is None:
            raise HTTPException(
                status_code=404,
                detail=f"Instrument with id {instrument_id} not found",
            )

        return instrument

    def retire_instrument(self, instrument_id: int) -> int:
        """Retire/delete an instrument

        Args:
            instrument_id: Instrument ID

        Returns:
            Retired instrument ID

        Raises:
            HTTPException: If instrument not found
        """

        self.get_instrument_status(instrument_id)

        del _INSTRUMENTS[instrument_id]
        return instrument_id

    def calibrate_instrument(self, instrument_id: int) -> Instrument:
        """Calibrate an instrument

        Args:
            instrument_id: Instrument ID

        Returns:
            Updated instrument with calibration timestamp

        Raises:
            HTTPException: If instrument not found
        """

        instrument = self.get_instrument_status(instrument_id)
        instrument.state = InstrumentState.CALIBRATING
        _INSTRUMENTS[instrument_id] = instrument

        instrument.state = InstrumentState.IDLE
        instrument.last_calibration = datetime.now(timezone.utc)
        instrument.next_maintenance = datetime.now(timezone.utc) + timedelta(days=90)
        _INSTRUMENTS[instrument_id] = instrument

        return instrument
