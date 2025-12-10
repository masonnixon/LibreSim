"""Sim class - Simulation orchestrator.

Based on H.R. Sells' OSK implementation (updated 210129).
Manages the execution of simulation blocks through stages.
"""

from .state import State


class Sim:
    """Simulation orchestrator.

    Manages the execution of simulation blocks organized into stages.
    Each stage can have a different time step.

    Example usage:
        # Create blocks
        source = StepSource()
        system = SecondOrderSystem()
        scope = Scope()

        # Connect blocks (application-specific)
        system.input_block = source
        scope.input_block = system

        # Create stage with all blocks
        stage = [source, system, scope]

        # Create and run simulation
        sim = Sim(
            dts=[0.01],           # Time steps for each stage
            tmax=10.0,            # Maximum simulation time
            vStage=[stage]        # Vector of stages
        )
        sim.run()
    """

    stop0 = 0        # Previous stop flag
    stop = 0         # Current stop flag (set by blocks to terminate)
    dts = []         # Time steps for each stage
    dt = 0           # Current time step
    tmax = 0         # Maximum simulation time
    vObj = []        # (unused, kept for compatibility)
    vStage = []      # Vector of stages (each stage is a list of blocks)
    clock = None     # Clock State object

    def __init__(self, dts, tmax, vStage):
        """Initialize the simulation.

        Args:
            dts: List of time steps, one per stage
            tmax: Maximum simulation time
            vStage: List of stages, each stage is a list of Block objects
        """
        Sim.tmax = tmax
        Sim.vStage = vStage
        Sim.dts = dts
        Sim.clock = State()
        Sim.stop = 0
        Sim.stop0 = 0

    @classmethod
    def sample(cls, sdt, t_event):
        """Class method for sampling - delegates to clock."""
        if cls.clock:
            cls.clock.sample(sdt, t_event)

    def run(self):
        """Execute the simulation.

        Iterates through stages, executing blocks in order:
        1. Initialize all blocks in stage
        2. For each time step:
           a. Sample (check timing)
           b. Update all blocks (compute derivatives)
           c. Report outputs (if ready)
           d. Propagate states
           e. Update clock
        3. Final report

        Returns:
            Dictionary with simulation results
        """
        results = {
            'times': [],
            'outputs': {}
        }

        Sim.clock.set()
        Sim.stop = Sim.stop0 = 0

        # Reset init counters
        for stage in Sim.vStage:
            for obj in stage:
                obj.initCount = 0

        State.ticklast = 0
        n = 0

        # Process each stage
        for ii in range(len(Sim.vStage)):
            n = ii
            stage = Sim.vStage[ii]
            dt = Sim.dts[ii] if ii < len(Sim.dts) else Sim.dts[-1]

            Sim.clock.reset(dt)
            State.tickfirst = 1
            State.ready = 1

            # Initialize all blocks in stage
            for obj in stage:
                obj.init()
                obj.initCount += 1

            # Main simulation loop
            while True:
                Sim.clock.sample(State.EVENT, Sim.tmax)

                # Update all blocks
                for obj in stage:
                    obj.update()

                # Report if ready (complete integration step)
                if State.ready:
                    # Record time
                    results['times'].append(State.t)

                    # Report and collect outputs
                    for obj in stage:
                        obj.rpt()

                        # Collect outputs from blocks that have them
                        block_id = id(obj)
                        if block_id not in results['outputs']:
                            results['outputs'][block_id] = []
                        results['outputs'][block_id].append(obj.getOutput())

                    State.tickfirst = 0

                    # Check stop conditions
                    if Sim.stop != Sim.stop0:
                        Sim.stop0 = Sim.stop
                        break

                    if State.t + State.EPS >= Sim.tmax:
                        Sim.stop = -1
                        break

                # Propagate all states
                for obj in stage:
                    obj.propagateStates()

                # Advance clock
                Sim.clock.updateclock()

            # Check if simulation should terminate
            if Sim.stop < 0:
                break

        # Final report
        State.ticklast = 1
        stage = Sim.vStage[n]
        for obj in stage:
            obj.rpt()

        return results

    @classmethod
    def terminate(cls, code=1):
        """Request simulation termination.

        Args:
            code: Stop code (positive to stop, negative for error)
        """
        cls.stop = code
