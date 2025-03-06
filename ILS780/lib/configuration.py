
from dataclasses import dataclass
import numpy as np

class classproperty(object):
    """ A decorator for class properties. """
    def __init__(self, f):
        self.f = f
    def __get__(self, obj, owner):
        return self.f(owner)

MHz = 1e6

@dataclass
class AOM:
    """ an abstract representation an AOM in the system. """
    slave: str
    name:str
    frequency: float
    power  = property(lambda self: f"{self.slave}_aom_{self.name}_power")
    switch = property(lambda self: f"{self.slave}_aom_{self.name}_switch")

@dataclass
class SlaveConfig:
    """ 
    This is minimalistic base class of how a 
    laser configuration class should look like.
    We will also add the AOMs in the child classes.
    """
    name    : str
    freq_max: float
    freq_min: float
    F_BEAT  : float = -1066.16616*MHz # Default
    C       : int   = 8               # Default

    EDFA_POWER      = classproperty(lambda self: f"{self.name}_edfa_power")
    LOCK_FREQUENCY  = classproperty(lambda self: f"{self.name}_lock_frequency")

    @classmethod
    def det2freq(cls, det:float, aom:AOM) -> float:
        """ 
        Given a light detuning, return the lock 'frequency' after the 'aom'.
        The detuning is defined as the difference between the laser frequency 
        and the atomic transition frequency:
        For slave1&2: Detuning from (F=2 to F'=3)
        For slave 3 : Detuning from (F=1 to F'=2)
        """
        f = np.abs(cls.F_BEAT + det - aom.frequency) / (cls.C*2)
        cls.check_frequency(f, aom, det)
        return float(f)

    @classmethod
    def freq2det(cls, f:float, aom:AOM) -> float:
        """ Given a lock 'frequency', return the light detuning after the 'aom'."""
        if cls.name != 'slave3':
            det = (aom.frequency - cls.F_BEAT) - 2*cls.C*f
        else:
            det = (aom.frequency - cls.F_BEAT) + 2*cls.C*f 
        return float(det)

    @classmethod
    def detuning_range_MHz(cls, aom:AOM) -> tuple:
        return (
            int(cls.freq2det(cls.freq_max, aom)/1e6), 
            int(cls.freq2det(cls.freq_min, aom)/1e6)
            )

    @classmethod
    def check_frequency(cls, f, aom:AOM, det:float):
        if not cls.freq_min <= f <= cls.freq_max:
            raise ValueError(
                f"({cls.name}) {aom.name} beam output cannot reach a detuning of {int(det/1e6)}MHz."
                )

class SLAVE1(SlaveConfig):
    name         = 'slave1'
    freq_max     = 97.78*MHz 
    freq_min     = 68.51*MHz 

    CONTROL_AOM         = AOM(name, "control",          -110*MHz)
    PROBE_DEPUMP_AOM    = AOM(name, "probe_depump",     +130*MHz)
    PUMP_AOM            = AOM(name, "pump",             -115*MHz)
    GENERAL_COOLING_AOM = AOM(name, "general_cooling",  +110*MHz)

class SLAVE2(SlaveConfig):
    name         = 'slave2'
    freq_max     = 92.26*MHz 
    freq_min     = 74.14*MHz 

    COOLING_REPUMPER_AOM = AOM(name, "cooling_repumper", 110*MHz)

class SLAVE3(SlaveConfig):
    name         = 'slave3'
    freq_max     = 89.25*MHz 
    freq_min     = 82.69*MHz 
    F_BEAT = +5501.86435*MHz
    C = 32

    COOLING_REPUMPER_AOM = AOM(name, "cooling_repumper", 110*MHz)
    REPUMPER_AOM         = AOM(name, "repumper",        -110*MHz)
    
if __name__ == '__main__':

    print("|--------------- Slave 1 -------------|")
    for aom in [SLAVE1.CONTROL_AOM, 
                SLAVE1.PROBE_DEPUMP_AOM, 
                SLAVE1.PUMP_AOM, 
                SLAVE1.GENERAL_COOLING_AOM]:
        _min, _max = SLAVE3.detuning_range_MHz(aom)
        print(f"{aom.name:<20}: [{_min} , {_max}] MHz")

    print("|--------------- Slave 2 -------------|")
    aom = SLAVE2.COOLING_REPUMPER_AOM
    _min, _max = SLAVE3.detuning_range_MHz(aom)
    print(f"{aom.name:<20}: [{_min} , {_max}] MHz")

    print("|--------------- Slave 3 -------------|")
    for aom in [SLAVE3.COOLING_REPUMPER_AOM, 
                SLAVE3.REPUMPER_AOM]:
        _min, _max = SLAVE3.detuning_range_MHz(aom)
        print(f"{aom.name:<20}: [{_min} , {_max}] MHz")
