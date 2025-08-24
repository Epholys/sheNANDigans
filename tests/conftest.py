import pytest

from nand.optimization_level import OptimizationLevel
from tests.simulators_factory import BuildProcess, SimulatorsFactory


@pytest.fixture(scope="module")
def simulators_factory():
    """Fixture to create a memoized SimulatorsFactory instance."""
    return SimulatorsFactory()


@pytest.fixture(scope="module")
def simulators(request, simulators_factory):
    """Fixture to provide simulators for different build processes and optimization levels."""
    processing: BuildProcess
    optimization_level: OptimizationLevel
    processing, optimization_level, encoder_type = request.param

    simulators = simulators_factory.get_simulators(
        processing, optimization_level, encoder_type
    )

    return simulators
