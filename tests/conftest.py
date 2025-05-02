import pytest

from src.optimization_level import OptimizationLevel
from tests.schematics_builder import choose_simulators


@pytest.fixture(scope="module")
def simulators(request):
    processing: str
    optimization_level: OptimizationLevel
    processing, optimization_level = request.param

    simulators = choose_simulators(processing, optimization_level)

    return simulators
