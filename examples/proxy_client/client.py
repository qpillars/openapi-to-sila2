from __future__ import annotations

from sila2.client import SilaClient
from sila2.framework import FullyQualifiedFeatureIdentifier

# This import registers all the generated features, errors, types, etc.
# The files are generated during the build process by the sila2-codegen tool
from generated import (
    authenticationfeature,
    instrumentsfeature,
    observablefeature,
)


class Client(SilaClient):
    AuthenticationFeature: authenticationfeature.AuthenticationFeatureClient
    InstrumentsFeature: instrumentsfeature.InstrumentsFeatureClient
    ObservableFeature: observablefeature.ObservableFeatureClient

    _expected_features: set[FullyQualifiedFeatureIdentifier] = {
        FullyQualifiedFeatureIdentifier("org.silastandard/core/SiLAService/v1"),
        FullyQualifiedFeatureIdentifier("org.silastandard/generator/AuthenticationFeature/v1"),
        FullyQualifiedFeatureIdentifier("org.silastandard/generator/InstrumentsFeature/v1"),
        FullyQualifiedFeatureIdentifier("org.silastandard/generator/ObservableFeature/v1"),
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._register_defined_execution_error_class(
            authenticationfeature.AuthenticationFeatureFeature.defined_execution_errors["AuthenticationError"],
            authenticationfeature.AuthenticationError,
        )

        self._register_defined_execution_error_class(
            instrumentsfeature.InstrumentsFeatureFeature.defined_execution_errors["InstrumentsError"],
            instrumentsfeature.InstrumentsError,
        )

        self._register_defined_execution_error_class(
            observablefeature.ObservableFeatureFeature.defined_execution_errors["ObservableError"],
            observablefeature.ObservableError,
        )
