
import numpy as np


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
            "values": self.values}

class Sequence(list):

    def add_exponential(self, key:str, duration, from_, to_, samples:int, tau):
        """ An special ramp implemented via many small duration SequencerStep"""
        t = np.linspace(0, duration, samples)
        v = from_ + (to_ - from_)*(1-np.exp(-t/tau))
        for i in range(samples):
            step = SequencerStep(duration=duration/samples, active=True)
            step.add_value(key, v[i])
            self += step

if __name__ == '__main__':

    sequence: list[dict] = Sequence()

    step = SequencerStep(duration=500e-3, active=True)
    step.add_value("slave1_lock_frequency", -210e6)
    step.add_value("slave3_repump_power", 100)
    step.add_value("do_trigger_0", False)
    sequence.append(step.as_dict())


    sequence.add_exponential("slave3_repump_power", 100e-3, 100, 0, 300, 50e-3)

