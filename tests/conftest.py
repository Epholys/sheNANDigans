import pytest

from tests.simulators_factory import (
    CircuitsFactory,
    SimulatorSpecs,
    SimulatorsFactory,
)


@pytest.fixture(scope="session")
def simulators_factory():
    """Fixture to create a memoized SimulatorsFactory instance."""
    return SimulatorsFactory()


@pytest.fixture(scope="session")
def circuits_factory():
    """Fixture to create a memoized CircuitsFactory instance."""
    return CircuitsFactory()


@pytest.fixture(scope="session")
def simulators(request, simulators_factory, circuits_factory):
    """Fixture to provide simulators for different cases. Useful because of memoization.

    Cases being build process, optimization level, encode algorithm, ...
    """

    simulators = simulators_factory.get_simulators(
        SimulatorSpecs(*request.param),
        circuits_factory,
    )

    return simulators
