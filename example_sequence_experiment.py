from ILS780 import *

if __name__ == '__main__':
    laser = ILS780()

    sequence = laser.sequence

    samples = 100

    step = SequencerStep(1)
    step.add_value(SLAVE3.REPUMPER_AOM.power, 100)
    step.add_value(SLAVE3.REPUMPER_AOM.switch, True)

    sequence += step

    step = SequencerStep(5)
    step.add_value(SLAVE3.REPUMPER_AOM.power, Models.Linear(100,0, samples))
    step.add_value(SLAVE3.REPUMPER_AOM.switch, True)

    sequence += step

    
    step = SequencerStep(10)
    step.add_value(SLAVE3.REPUMPER_AOM.power, Models.Linear(0,100, samples))
    step.add_value(SLAVE3.REPUMPER_AOM.switch, True)

    sequence += step

    laser.run_sequence(False, 1, True)

