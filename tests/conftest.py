import pytest

from nand.optimization_level import OptimizationLevel
from tests.simulators_factory import BuildProcess, SimulatorsFactory

# TODO : is all of this necessary ?


@pytest.fixture(scope="module")
def simulators_factory():
    """Fixture to create a memoized SimulatorsFactory instance."""
    return SimulatorsFactory()


@pytest.fixture(scope="module")
def simulators(request, simulators_factory):
    """Fixture to provide simulators for different build processes and
    optimization levels."""
    processing: BuildProcess
    optimization_level: OptimizationLevel
    processing, optimization_level, encoder_type, project = request.param

    simulators = simulators_factory.get_simulators(
        processing, optimization_level, encoder_type, project
    )

    return simulators
