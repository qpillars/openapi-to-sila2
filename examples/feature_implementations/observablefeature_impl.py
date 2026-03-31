from __future__ import annotations

import json
import os
import threading
from typing import TYPE_CHECKING

import requests
from dotenv import load_dotenv
from sila2.server import MetadataDict

from generated.observablefeature import ObservableFeatureBase
from generated.observablefeature.types import MeasurementReading

if TYPE_CHECKING:
    from proxy_server import Server

load_dotenv()


class ObservableFeatureImpl(ObservableFeatureBase):
    def __init__(self, parent_server: Server) -> None:
        super().__init__(parent_server=parent_server)
        self.test_api_url = os.getenv("TEST_API_URL", "http://127.0.0.1:8000").rstrip("/")

        self._emitter_thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()

    def __emit_updates(self) -> None:
        try:
            with requests.get(f"{self.test_api_url}/observable/measurements", stream=True) as r:
                for line in r.iter_lines():
                    if self._stop_event.is_set():
                        break

                    if not line:
                        continue

                    try:
                        data = json.loads(line.decode("utf-8"))
                        measurement_reading = MeasurementReading(
                            InstrumentId=data["instrument_id"],
                            InstrumentName=data["instrument_name"],
                            Value=data["value"],
                            Unit=data["unit"],
                            Timestamp=data["timestamp"],
                            Status=data["status"],
                            Metadata=json.dumps(data.get("metadata", {})),
                        )
                        self.update_StreamMeasurementsObservableMeasurementsGet(measurement_reading)
                        print(f"[Emitter] Emitted: {measurement_reading}")
                    except Exception as e:
                        print(f"[Emitter] Failed to decode or emit: {e}")
                        print(f"[Emitter] Raw data: {data}")

        except Exception as e:
            print(f"[Emitter] Stream error: {e}")

        with self._lock:
            self._emitter_thread = None
            self._stop_event.clear()

    def StreamMeasurementsObservableMeasurementsGet_on_subscription(self, *, metadata: MetadataDict) -> None:
        super().StreamMeasurementsObservableMeasurementsGet_on_subscription(metadata=metadata)

        with self._lock:
            if self._emitter_thread is None or not self._emitter_thread.is_alive():
                self._stop_event.clear()
                self._emitter_thread = threading.Thread(target=self.__emit_updates, daemon=True)
                self._emitter_thread.start()

        return None
