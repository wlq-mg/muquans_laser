from dataclasses import dataclass
import numpy as np
import warnings

class Models:
    """ Collection of Ramp models."""

    @dataclass
    class Model:
        """ Base class for all the models."""
        pass # value: property

    @dataclass
    class RampDDS(Model):
        """ Ramp model for the DDSs."""
        from_ : float
        to_ :float
        
        @property
        def value(self):
            return {
                "type": "RAMP_DDS", 
                "from": self.from_, 
                "to": self.to_
                }

    @dataclass
    class RampAO(Model):
        """"Not supported by  the API !"""
        from_ : float
        to_ :float
        samples: int
        
        @property
        def value(self):
            return {
                "type": "RAMP_AO", 
                "from": self.from_, 
                "to": self.to_, 
                "samples": self.samples
                }

    @dataclass
    class Linear(Model):
        """ Ramp model for the AOMs."""
        from_ : float
        to_ :float
        samples: int

        @property
        def value(self):
            return np.linspace(self.from_, self.to_, self.samples, dtype=float)

    @dataclass
    class Exponential(Model):
        """ 
        Smooth transition between two values.
        
        Parameters:
        ----------
        from_: Initial value.
        to_: Final value.
        tau: Time constant (normalized to 1).
        samples: Number of samples. 
        """
        from_: float
        to_: float
        tau: float
        samples: int

        @property
        def value(self):
            # Create a normalized time vector from 0 to 1
            t = np.linspace(0, 1, self.samples)
            # Compute exponential-like interpolation
            y1, y2, tau = self.from_, self.to_, self.tau
            return y1 + (y2 - y1) * (1 - np.exp(-t/tau)) / (1 - np.exp(-(1/tau)))
        
    @dataclass
    class ExponentialNotWorking:
        """ Exponential curve model."""
        from_: float
        to_: float
        duration: float
        tau: float
        samples: int
        tolerance: float = 1e-2

        @property
        def maximum_tau(self):
            """Compute the maximum tau value that ensures convergence."""
            return self.duration / -np.log(self.tolerance / abs(self.to_ - self.from_))

        @property
        def value(self):
            """Compute the exponential curve and ensure it reaches the target value."""
            t = np.linspace(0, self.duration, self.samples)
            v = self.from_ + (self.to_ - self.from_) * (1 - np.exp(-t / self.tau))
            if abs(v[-1] - self.to_) > self.tolerance:
                warnings.warn(
                    f"""\n Exponential curve does not reach target value ({self.to_}) within the given duration ({self.duration}).
                    Consider increasing the duration or decreasing the tau value.""", 
                    RuntimeWarning)
                v[-1] = self.to_
            return v
