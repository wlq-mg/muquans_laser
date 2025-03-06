from .sequence_models import Models
import numpy as np




class SequencerStep:
    """Represents a single step in a sequence."""

    def __init__(self, duration: float, active: bool = True, name: str = None):
        self.name = name
        self.duration = duration
        self.active = active
        self.values = {}

    def add_value(self, id: str, value):
        """Ensures that only valid sequence values are assigned.
        id: the id of the value to be assigned (ex: SLAVE1.PUMP_AOM.power) 
        value: can be a single value, a list, or a ramp model.
        """
        
        if isinstance(value, Models.RampAO):
            raise NotImplementedError(f"Type RampAO is not yet supported by the API (use Linear)!")

        if isinstance(value, Models.RampDDS) and not 'frequency' in id:
            raise NotImplementedError(f"Type RampDDS is only used for frequency IDs !")

        if isinstance(value, (float, int, bool)):
            self.values[id] = value
        
        elif isinstance(value, (list, np.ndarray)):
            # Arbitrary waveforms (will be unpacked...)
            self.values[id] = value
        elif isinstance(value, Models.Model):
            self.values[id] = value.value
        else:
            raise NotImplementedError(f"Type {type(value)} is not yet supported !")

    def as_dict(self):
        """Returns the step as a dictionary (for API use)."""
        return {"duration": self.duration, "active": self.active, "values": self.values}

    ########## 
    @property
    def iterable_ids(self):
        """Returns the ids of the iterable values."""
        return [k for k, v in self.values.items() if isinstance(v, (list, np.ndarray))]

    @property
    def frequency_ramp_ids(self):
        dds_ids = []
        for k, v in self.values.items():
            if not isinstance(v, dict): continue
            if not "type" in v: continue
            if not "RAMP_DDS" in v["type"]: continue
            dds_ids.append(k)
        return dds_ids

    def check_sampling(self):
        """Checks if all iterable values have the same length."""
        samples = len(self.values[self.iterable_ids[0]])
        if any(len(self.values[k]) != samples for k in self.iterable_ids):
            raise(ValueError("All ramps must have the same length."))
        return samples