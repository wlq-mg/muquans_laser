
from dataclasses import dataclass
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator
plt.style.use('dark_background')
from .configuration import SLAVE1, SLAVE2, SLAVE3
def grid_style(ax):
    ax.xaxis.set_minor_locator(AutoMinorLocator(10))
    ax.yaxis.set_minor_locator(AutoMinorLocator(5))
    ax.grid(which='major', color='#AEB6BF', linestyle='-', alpha=0.3)
    ax.grid(which='minor', color='#D6DBDF', linestyle=':', alpha=0.2)
    ax.tick_params(which='minor',axis="y",direction="in")
    ax.tick_params(which='minor',axis="x",direction="in", )
    ax.tick_params(which='major',axis="y",direction="in", width=1, length=2)
    ax.tick_params(which='major',axis="x",direction="in", width=1, length=3)
    return ax

class SequencerValue:
    @dataclass
    class Value:
        value: float | bool | str

    @dataclass
    class RampDDS:
        from_ : float
        to_ :float

        @property
        def value(self):
            return {"type": "RAMP_DDS", "from": self.from_, "to": self.to_}
    
    @dataclass
    class RampAO:
        from_: float
        to_: float
        samples: int

        @property
        def value(self):
            return {
                "type": "RAMP_AO", 
                "from": self.from_, 
                "to": self.to_, 
                "samples": self.samples}

        @staticmethod
        def check_rule(param):
            return 0. <= param <= 100.


class SequencerStep:
    """Represents a single step in a sequence."""

    def __init__(self, duration: float, active: bool = True, name: str = None):
        self.name = name
        self.duration = duration
        self.active = active
        self.values = {}

    def add_value(self, id: str, value: SequencerValue):
        """Ensures that only valid sequence values are assigned."""
        
        # For simplicity exceptionally allow these types
        if isinstance(value, (float, int, bool)):
            self.values[id] = value
            return
        
        if not hasattr(value, "value"):
            raise TypeError("You must use a SequencerValue typed object !")
        self.values[id] = value.value

    def add_ramp(self, id:str, from_, to_, samples:int=20):
        if 'frequency' in id:
            self._add_frequency_ramp(id, from_, to_)
        elif 'power' in id:
            self._add_ao_ramp(id, from_, to_, samples)
        else:
            raise NotImplementedError(
                f"The parameter {id} has no ramp method. Be explicit !"
                )

    def _add_frequency_ramp(self, id:str, from_, to_):
        if not 'frequency' in id:
            raise ValueError(f"{id} is not a valid frequency parameter")
        self.values[id] = SequencerValue.RampDDS(from_, to_).value

    def _add_ao_ramp(self, id:str, from_, to_, samples:int):
        if not 'power' in id:
            raise ValueError(f"{id} is not a valid analog parameter")
        self.values[id] = SequencerValue.RampAO(from_, to_, samples).value

    def as_dict(self):
        """Returns the step as a dictionary (for API use)."""
        return {
            "duration": self.duration, 
            "active": self.active, 
            "values": self.values}


class Sequence(list):
    """A special list that accepts SequencerStep objects, storing their as_dict() representation."""


    def add_exponential(self, key:str, duration, from_, to_, samples:int, tau):
        """ An special ramp implemented via many small duration SequencerStep"""
        t = np.linspace(0, duration, samples)
        v = from_ + (to_ - from_)*(1-np.exp(-t/tau))
        for i in range(samples):
            step = SequencerStep(duration=duration/samples, active=True)
            step.add_value(key, SequencerValue.Value(v[i]))
            self += step

    def collect_data(self) -> dict:
        """ Collects all the data stored for each laser: AOMs power and frequency"""
        channels = {}
        time_accum = 0

        classes = {
            "slave1": SLAVE1,
            "slave2": SLAVE2,
            "slave3": SLAVE3,
        }

        # Init data holders
        slaves: list[str] = [f'slave{i+1}' for i in range(3)]
        channels = {}
        channels['change_times'] = []
        for i, slave in enumerate(slaves):
            channels[slave] = {}
            channels[slave]['frequency'] = {'times': [], 'values':[], 'last': 0, 'color':f"C{i}"}
            channels[slave]['aoms'] = {'names': {}}
            cls = classes.get(slave)
            c = 0
            for attr in cls.__dict__.keys():
                if not 'AOM' in attr: continue
                name = cls.__dict__[attr].name
                channels[slave]['aoms']['names'][name] = {'color': f'C{c}', 'times': [] ,'values':[], 'last': 0}
                c+=1
        
        # Retrieve data
        def fetch_data(where:dict, parameter:str, channel:str):
            """ Checks if data exist in a step and appends it to channel buffers.
            If not, the last known value will be used.
            """
            t = np.array([0, duration])
            if parameter in where.keys():
                value = where[parameter]
                if isinstance(value, dict) and 'from' in value:
                    # Will be valid for both RAMP_DDS (2 points) and RAMP_AO types
                    y = np.linspace(value['from'], value['to'], value.get('samples', 2))
                    if 'samples' in value: # Adapt when samples is provided
                        t = np.linspace(0, duration, len(y))
                else:
                    y = np.array([value, value])
            else:
                value = channel['last']
                y = np.array([value, value])
            channel['times'].extend(list(t+time_accum))
            channel['values'].extend(list(y))
            channel['last'] = y[-1]

        time_accum = 0
        steps = self[:]
        for step in steps:
            duration = step["duration"] * 1e3
            for slave in slaves:
                # Frequency data
                fetch_data(
                    step['values'],
                    f"{slave}_lock_frequency", 
                    channels[slave]['frequency'])

                # Aom Data
                for aom in channels[slave]['aoms']['names']:
                    fetch_data(
                        step['values'],
                        f"{slave}_aom_{aom}_power", 
                        channels[slave]['aoms']['names'][aom])                    

            time_accum += duration
            channels['change_times'].append(time_accum)
        
        return channels

    def draw(self, show_seperator=False):
        channels = self.collect_data()

        # Init axes
        fig, axs = plt.subplots(4, 1, figsize=(10, 8), sharex=True, dpi=100)
        axs[-1].set_xlabel("Time (ms)")
        axs[0].set_ylabel("Frequency (MHz)")
        [axs[i+1].set_ylabel(f"S{i+1} AOMs (%)") for i in range(3)]
        [ax.set_ylim(-10,110) for ax in axs[1:]]
        [grid_style(ax) for ax in axs]

        # Plot the data
        if show_seperator:
            for ax in axs:
                [ax.axvline(t, color="gray", ls='--', alpha=0.5, lw=2) for t in channels['change_times']]
    
        for i in range(3):
            slave = f"slave{i+1}"
            ch = channels[slave]['frequency']

            axs[0].plot( ch['times'], ch['values'], color=ch['color'], label=slave)

            for name, aom in channels[slave]['aoms']['names'].items():
                axs[i+1].step(
                    aom['times'], aom['values'], where='post',
                    color = aom['color'], label= name)
        
        [ax.legend() for ax in axs]

        fig.tight_layout()
        fig.subplots_adjust(hspace=0.00)


        plt.show()

    def __add__(self, other: SequencerStep):
        if isinstance(other, SequencerStep) and other.active:
            return Sequence(super().__add__([other.as_dict()]))
        elif isinstance(other, list):
            if all(isinstance(item, SequencerStep) for item in other):
                return Sequence(super().__add__([item.as_dict() for item in other if item.active]))
            else:
                raise TypeError("All items in the list must be SequencerStep objects.")
        else:
            raise TypeError("Can only add a SequencerStep or list of SequencerStep objects.")
    
    def __iadd__(self, other):
        if isinstance(other, SequencerStep) and other.active:
            self.append(other.as_dict())
        elif isinstance(other, list):
            if all(isinstance(item, SequencerStep) for item in other):
                self.extend([item.as_dict() for item in other if item.active])
            else:
                raise TypeError("All items in the list must be SequencerStep objects.")
        else:
            raise TypeError("Can only add a SequencerStep or list of SequencerStep objects.")
        return self

class RampedStep(SequencerStep):
    """ This will be a list of steps."""
    def __init__(self, duration, active = True, name = None, ramps: dict= {}):
        super().__init__(duration, active, name)
        self.ramps =ramps


if __name__ == '__main__': 
    from instruments.muquans_laser.lib.configuration import SLAVE1, SLAVE2, SLAVE3

    sequence = Sequence()

    step = SequencerStep(duration=100e-3, active=True)
    step.add_ramp(SLAVE1.CONTROL_AOM.power, 0, 100, 20)
    step.add_value(SLAVE2.LOCK_FREQUENCY, SequencerValue.RampDDS(50, 70))
    sequence += step

    step = SequencerStep(duration=50e-3, active=True)
    step.add_ramp(SLAVE1.CONTROL_AOM.power, 100, 50, 20)
    sequence += step

    step = SequencerStep(duration=25e-3, active=True)
    step.add_ramp(SLAVE1.CONTROL_AOM.power, 50, 0, 20)
    step.add_value(SLAVE3.COOLING_REPUMPER_AOM.power, SequencerValue.Value(60))
    sequence += step

    sequence += RampedStep(
        duration=50e-3,
        active=True,
        ramps = {
            SLAVE1.CONTROL_AOM.power: (0, 100, 20),
        }
    )


    # Example of adding an exponential ramp
    sequence.add_exponential(SLAVE1.CONTROL_AOM.power, 
                             duration = 60e-3,
                             from_=0,
                             to_=100,
                             samples=100,
                             tau=10e-3
                             )
    
    step = SequencerStep(duration=25e-3, active=True)
    step.add_ramp(SLAVE2.COOLING_REPUMPER_AOM.power, 0, 100, 20)
    sequence += step

    sequence.draw(False)