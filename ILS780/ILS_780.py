from .lib.API            import ApiV1 as API
from .lib.configuration  import SLAVE1, SLAVE2, SLAVE3
from .lib.lasers         import MasterDiode, SlaveDiode
from .lib.sequence      import Sequence, SequencerStep

MHz = 1e6

class ILS780():

    def __init__(self, host='10.0.3.88', verbose=False):
        self.api = API(host, verbose=verbose)
        self.api.auth("admin", "admin")

        self.master = MasterDiode(self.api)
        self.slave1 = SlaveDiode(self.api, SLAVE1)
        self.slave2 = SlaveDiode(self.api, SLAVE2)
        self.slave3 = SlaveDiode(self.api, SLAVE3)

        self.sequence = Sequence()
        self.sequence.clear()
    
    def use_external_100MHz(self, state):
        """
        Activate the front end 100MHz reference in place of the system quartz.
        """
        self.api.sys_action_run(
            "presets", "rf_100Mhz_ref_switch", state, 
            wait_complete=True)
    
    def set_aom_external_switch(self, state:bool):
        """
        Activate the external control of the AOM switches 
        in place of the internal sequencer.
        """
        self.api.sys_action_run(
            "presets", "rf_aom_external_switch", state, 
            wait_complete=True)

    @property
    def sequence_status(self) -> str:
        return self.api.seq_feedback()

    def run_sequence(self, 
                     is_triggered=False, 
                     loop_count=1, 
                     wait_complete=True,
                     aliases:dict={},
                     ): 
        if not len(self.sequence):
            raise ValueError("The sequence list is empty")

        self.api.seq_run(
            sequence = self.sequence,
            aliases = aliases,
            triggered = is_triggered,
            loop_count= loop_count,
            wait_complete= wait_complete
        )
