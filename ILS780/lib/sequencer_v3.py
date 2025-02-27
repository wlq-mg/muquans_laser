import numpy as np
import matplotlib.pyplot as plt


class SequencerStep:
    """Represents a single step in a sequence."""

    def __init__(self, duration: float, active: bool = True, name: str = None):
        self.name = name
        self.duration = duration
        self.active = active
        self.values = {}

    def add_value(self, id: str, value):
        self.values[id] = value

    def as_dict(self):
        """Returns the step as a dictionary (for API use)."""
        return {
            "duration": self.duration,
            "active": self.active, 
            "values": self.values
        }


class RampStrategy:
    """Base class for ramp strategies."""

    def generate(self, duration, from_, to_, samples, **kwargs):
        raise NotImplementedError("Must be implemented by subclasses")


class ExponentialRamp(RampStrategy):
    """Exponential ramp strategy."""

    def generate(self, duration, from_, to_, samples, tau):
        t = np.linspace(0, duration, samples)
        return from_ + (to_ - from_) * (1 - np.exp(-t / tau))


class LinearRamp(RampStrategy):
    """Linear ramp strategy."""

    def generate(self, duration, from_, to_, samples, **kwargs):
        return np.linspace(from_, to_, samples)


class ConstantRamp(RampStrategy):
    """Constant value strategy."""

    def generate(self, duration, from_, to_, samples, **kwargs):
        # Only need the first step since the value is constant
        return [from_]


class Sequence(list):

    def add_ramp(self, duration, samples, ramps: dict):
        """ 
        Adds multiple ramps in parallel to the sequence.
        
        `ramps`: Dictionary where each key is a parameter and the value is a dict specifying:
          - type: 'exponential', 'linear', or 'constant'
          - from: Starting value
          - to: Ending value
          - tau: Time constant (only for exponential)
        """
        # Register ramp strategies
        ramp_strategies = {
            'exponential': ExponentialRamp(),
            'linear': LinearRamp(),
            'constant': ConstantRamp()
        }

        # Determine ramp types and generate values
        ramp_values = {}
        constant_values = {}
        
        for key, config in ramps.items():
            ramp_type = config.get('type', 'constant')
            from_ = config.get('from', 0)
            to_ = config.get('to', from_)
            tau = config.get('tau', 1)

            if ramp_type not in ramp_strategies:
                raise ValueError(f"Unknown ramp type: {ramp_type}")

            ramp_strategy = ramp_strategies[ramp_type]
            values = ramp_strategy.generate(
                duration=duration, 
                from_=from_, 
                to_=to_, 
                samples=samples, 
                tau=tau
            )

            # Check if it's a constant value
            if ramp_type == 'constant':
                constant_values[key] = values[0]
            else:
                ramp_values[key] = values

        # If there are constant values, add them as the first step
        if constant_values:
            step = SequencerStep(duration=duration, active=True)
            for key, value in constant_values.items():
                step.add_value(key, value)
            self.append(step.as_dict())

        # Create sequencer steps for all ramps in parallel
        for i in range(samples):
            step = SequencerStep(duration=duration/samples, active=True)
            for key, values in ramp_values.items():
                step.add_value(key, values[i])
            # Only append if there's at least one ramp value
            if step.values:
                self.append(step.as_dict())

def plot_sequence(sequence):
    """Plots the sequence using plt.step with where='pre'."""
    time = 0
    times = []
    values = {}

    # Collect times and values for each parameter
    for step in sequence:
        duration = step['duration']
        times.append(time)
        for key, value in step['values'].items():
            if key not in values:
                values[key] = []
            values[key].append(value)
        time += duration

    # Add final time for step plotting
    times.append(time)

    # Ensure all value lists are the same length as times
    for key in values.keys():
        # Repeat the last value to match the length of times
        while len(values[key]) < len(times):
            values[key].append(values[key][-1])

    # Plot each parameter
    plt.figure(figsize=(10, 6))
    for key, vals in values.items():
        plt.step(times, vals, where='pre', label=key)

    plt.xlabel("Time (s)")
    plt.ylabel("Value")
    plt.title("Sequence Plot")
    plt.legend()
    plt.grid(True)
    plt.show()

# Fix: Recreate the sequence to ensure clean state
sequence = Sequence()

# Add a standard step
step = SequencerStep(duration=50e-3, active=True)
step.add_value("slave1_lock_frequency", -210e6)
step.add_value("slave3_repump_power", 100)
step.add_value("do_trigger_0", False)
sequence.append(step.as_dict())


