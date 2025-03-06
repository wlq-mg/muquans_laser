from ILS780 import *


if __name__ == '__main__':

    sequence = Sequence()

    samples = 100

    step = SequencerStep(50e-3)
    step.add_value(SLAVE1.PUMP_AOM.power, Models.Linear(0,100, 10))
    step.add_value(SLAVE1.CONTROL_AOM.power, 30)
    step.add_value(SLAVE1.LOCK_FREQUENCY, 100)    
    
    sequence += step

    step = SequencerStep(100e-3)
    step.add_value(SLAVE1.PUMP_AOM.power, Models.Linear(100,30, samples))
    step.add_value(SLAVE1.CONTROL_AOM.power, Models.Linear(30,90, samples))
    step.add_value(SLAVE1.LOCK_FREQUENCY, Models.RampDDS(100, 800))    
    
    sequence +=step

    step = SequencerStep(20e-3)
    step.add_value(SLAVE1.PUMP_AOM.power, Models.Linear(30,0, samples))
    step.add_value(SLAVE1.LOCK_FREQUENCY, Models.Exponential(800, 0, tau=0.3, samples=samples))    
    
    sequence += step

    print(f"Number of steps: {len(sequence)}")

    sequence.draw(False)
