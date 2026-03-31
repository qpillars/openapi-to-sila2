import sys
from pathlib import Path
from uuid import UUID, uuid4

from sila2.server import SilaServer

# Add examples directory to path to enable absolute imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# from feature_implementations.authenticationfeature_impl import AuthenticationFeatureImpl
# from feature_implementations.instrumentsfeature_impl import InstrumentsFeatureImpl
from feature_implementations.observablefeature_impl import ObservableFeatureImpl

# This import registers the generated features base classes
# The files are generated during the build process by the sila2-codegen tool
from generated.authenticationfeature import AuthenticationFeatureFeature
from generated.instrumentsfeature import InstrumentsFeatureFeature
from generated.observablefeature import ObservableFeatureFeature


class Server(SilaServer):
    def __init__(
        self,
        server_uuid: UUID | None = None,
        name: str | None = None,
        description: str | None = None,
    ):
        if name is None:
            name = "QPillars Server"
        if description is None:
            description = "Sample QPillars SiLA2 Proxy"
        super().__init__(
            server_name=name,
            server_description=description,
            server_type="DEMO",
            server_version="1.0",
            server_vendor_url="https://gitlab.com/SiLA2/sila_python",
            server_uuid=server_uuid if server_uuid is not None else uuid4(),
        )

        # self.authenticationfeature = AuthenticationFeatureImpl(self)
        # self.set_feature_implementation(AuthenticationFeatureFeature, self.authenticationfeature)

        # self.instrumentsfeature = InstrumentsFeatureImpl(self)
        # self.set_feature_implementation(InstrumentsFeatureFeature, self.instrumentsfeature)

        self.observablefeature = ObservableFeatureImpl(self)
        self.set_feature_implementation(ObservableFeatureFeature, self.observablefeature)
