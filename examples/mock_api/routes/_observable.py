import json
import random
import time
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from schemas.types import MeasurementReading
from services._instrument_service import InstrumentService

router = APIRouter(prefix="/observable", tags=["Observable"])


def get_instrument_service() -> InstrumentService:
    """Dependency for instrument service"""

    return InstrumentService()


def event_stream(
    service: InstrumentService = Depends(get_instrument_service),
):
    """Generate global streaming events from all instruments

    Args:
        service: Instrument service instance

    Yields:
        JSON-encoded measurement readings
    """

    try:
        index = 0
        while True:
            instruments = service.get_available_instruments()

            if instruments:
                instrument = random.choice(instruments)

                if instrument.type.value == "balance":
                    value = round(random.uniform(0.1, 500.0), 2)
                    unit = "g"
                elif instrument.type.value == "centrifuge":
                    value = round(random.uniform(100, 15000), 0)
                    unit = "rpm"
                elif instrument.type.value == "spectrometer":
                    value = round(random.uniform(0.0, 3.0), 3)
                    unit = "AU"
                else:
                    value = round(random.uniform(0.1, 100.0), 1)
                    unit = "μm"

                reading = MeasurementReading(
                    instrument_id=instrument.id,
                    instrument_name=instrument.name,
                    value=value,
                    unit=unit,
                    timestamp=datetime.now(timezone.utc),
                    status="ok",
                    metadata={"index": index},
                )

                yield json.dumps(reading.model_dump(mode="json")) + "\n"
            else:
                placeholder = {
                    "status": "no_instruments",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

                yield json.dumps(placeholder) + "\n"

            index += 1
            time.sleep(1)

    except Exception as e:
        error_data = {
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        yield json.dumps(error_data) + "\n"


@router.get("/measurements")
def stream_measurements(
    service: InstrumentService = Depends(get_instrument_service),
):
    """Stream real-time measurements from all instruments

    Server-Sent Events stream of latest measurements across all instruments.

    Args:
        service: Instrument service instance

    Returns:
        StreamingResponse with JSON-encoded measurements
    """

    return StreamingResponse(
        event_stream(service),
        media_type="application/x-ndjson",
    )
