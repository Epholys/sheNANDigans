from dataclasses import dataclass
from tests.parameters_enums import BuildProcess, EncoderAlgorithm, Project
from nand.circuit_builder import CircuitLibrary


@dataclass(frozen=True)
class CircuitSpecs:
    """Parameters"""

    build_process: BuildProcess
    encoder_algorithm: EncoderAlgorithm
    project: Project


class CircuitsFactory:
    def __init__(self):
        self._circuits: dict[CircuitSpecs, CircuitLibrary] = {}

    def get_circuits(self, specs: CircuitSpecs) -> CircuitLibrary:
        """Build the circuits for the different build processes."""
        # Returns early if the circuits were already built.
        if specs in self._circuits:
            return self._circuits[specs]

        # For every BuildProcess, we need first the reference:
        # - if REFERENCE is requested: trivial.
        # - if ROUND_TRIP is requested: we must have reference first.
        # It's memoized to avoid building it again if ROUND_TRIP is requested
        if (
            CircuitSpecs(
                BuildProcess.REFERENCE,
                specs.encoder_algorithm,
                specs.project,
            )
            not in self._circuits
        ):
            self._circuits[specs] = specs.project.get_builder().build_circuits()

        # Now, if requested, build ROUND_TRIP.
        if specs.build_process == BuildProcess.ROUND_TRIP:
            encoder_type = specs.encoder_algorithm
            reference = self._circuits[
                CircuitSpecs(
                    BuildProcess.REFERENCE, specs.encoder_algorithm, specs.project
                )
            ]
            encoded = encoder_type.get_encoder()().encode(reference)
            round_trip = encoder_type.get_decoder()().decode(encoded)
            self._circuits[specs] = round_trip

        return self._circuits[specs]
