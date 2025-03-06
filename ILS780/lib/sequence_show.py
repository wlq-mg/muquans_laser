import numpy as np
from .configuration import SLAVE1, SLAVE2, SLAVE3
import matplotlib.pyplot as plt

from matplotlib.ticker import AutoMinorLocator
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

def plot_sequence(sequence, show_seperator=False):
    """ Plots the sequence data"""
    channels = collect_data(sequence)

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

    print("Plotting the sequence...")
    plt.show()

def collect_data(sequence) -> dict:
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
    steps = sequence[:]
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