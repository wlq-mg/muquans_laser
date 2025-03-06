
from .sequence_models import Models
from .sequence_show import plot_sequence
from .sequence_step import SequencerStep

class Sequence(list):
    """A special list that accepts SequencerStep objects, 
    storing their as_dict() representation."""

    def add_step(self, step: SequencerStep):
        """ Since the ILS doesn't support RAMPS_AO (for now 6/3/2025),
        we will use this method of unpacking and processing sequence steps.
        I will implement a recursive method to split the ramps into smaller segments.
        """
        
        duration = step.duration
        steps = step.values
        iterable_ids = step.iterable_ids        

        # Normal case (no arrays): append the step as is
        if not iterable_ids:
            self.append(step.as_dict())
            return
        
        samples = step.check_sampling()

        # Split the DDS ramps into smaller segments (if exist)
        for k in step.frequency_ramp_ids:
            ramp = steps[k]
            dy = (ramp["to"] - ramp['from']) / samples
            steps[k] = [
                Models.RampDDS(
                    ramp['from'] + i * dy, 
                    ramp['from'] + (i+1) * dy
                    ).value 
                    for i in range(samples)
                    ]
            iterable_ids += [k]

        # Recursively process smaller time steps
        dt = duration / samples
        for i in range(samples):
            new_step = SequencerStep(dt, active=True)
            new_step.values = steps.copy()
            # Replace lists with values
            new_step.values.update({id: steps[id][i] for id in iterable_ids})
            self.add_step(new_step)
    

    def __add__(self, other):
        """ Defining the + operator for the sequence."""
        new_seq = Sequence(self)  # Create a new instance
        return new_seq.__iadd__(other)  # Delegate to __iadd__

    def __iadd__(self, other):
        """ Defining the += operator for the sequence."""
        if isinstance(other, SequencerStep):
            if other.active: self.add_step(other)
        elif isinstance(other, list) and all(isinstance(item, SequencerStep) for item in other):
            [self.add_step(item) for item in other if item.active]
        else:
            raise TypeError("Can only add a SequencerStep or a list of SequencerStep objects.")
        return self

    def draw(self, show_seperator=False):
        """Draws the sequence in a matplotlib figure."""
        plot_sequence(sequence=self, show_seperator=show_seperator) 