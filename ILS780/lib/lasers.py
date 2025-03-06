
# For type checking
from .configuration import SlaveConfig, AOM
from .API import ApiV1 as API
from .API import ApiError

def short_name(laser_name:str):
    """ Converts laser_name (eg. 'slave2' to 'S2' or 'master' to 'M') """
    name = laser_name[0].capitalize()
    return name + laser_name[-1] if laser_name[-1].isnumeric() else name

class _BaseAPI:

    def __init__(self, api:API, laser:SlaveConfig):
        self.api = api
        
        if not issubclass(laser, SlaveConfig):
            raise TypeError(f"Invalid slave configuration.")
        
        self.config = laser
        self.laser: str = laser.name
    
    def _get_value(self, value:str):
        data = self.api.sys_monit_values()
        if not value in data.keys():
            raise ApiError(f"{value} is not a valid monitoring.")
        return data[value]
    
    def _run_action(self, action:str, value=None):
        self.api.sys_action_run(self.laser, action, value, wait_complete=True)

class Diode(_BaseAPI):

    @property
    def is_enabled(self) -> bool:
        """ Status of the laser diode. 
        Laser diode emits or not."""
        laser = short_name(self.laser)
        value = f"Enable_Current_Laser_Diode_{laser}"
        return self._get_value(value)

    @property
    def current(self) -> float:
        """ Current feeding the laser diode. (mV)"""
        laser = short_name(self.laser)
        value = f"Mon_Current_Laser_Diode_{laser}"
        return self._get_value(value)

    @property
    def temperature(self) -> float:
        """ Temperature of the laser diode. (°C)"""
        laser = short_name(self.laser)
        value = f"Mon_Temp_NTC_Laser_Diode_{laser}"
        return self._get_value(value)

    # Actions
    def autolock(self, state:bool):
        """ 
        S1: Lock at -10MHz with respect to the resonance of the f=2->F'=3 transition of the 87Rb for the cool/rep outputs.
        S2: Lock at -10MHz with respect to the resonance of the f=2->F'=3 transition of the 87Rb.
        S3: Lock on the resonance of the F=1->F'=2 transition of the 87Rb for the cool/rep outputs
        """
        self._run_action(f'{self.laser}_diode_autolock', state)
    
    def ppln_autoscan(self):
        """ Automatically optimize the phase matching temperature. """
        self._run_action('ppln_autoscan')

    def diode_switch(self, state:bool):
        """ Change the current of the laser and start to emit ligth at native diode power."""
        self._run_action('diode_switch', state)

class MasterDiode(Diode):
    
    def __init__(self, api: API):
        self.api = api
        self.laser = "master"

    def autolock(self, state:bool):
        """ 
        Lock automatically laser frequency on the crossover F'=3 x F'=4 of the 85Rb 
        using the temperature parameters offset.
        """
        self._run_action(f'diode_autolock', state)

    @property
    def is_locked(self) -> bool:
        """ Status of the laser diode frequency lock."""
        laser = short_name(self.laser)
        value = f"Switch_Loop_Freq_Lock_{laser}"
        res = self.api.get(f"/system/monitoring/values/{value}")
        return bool(res['val'])

    @property
    def interlock_status(self) -> bool:
        """ 
        Status of  interlock. 
        True  : Allow to switch ON the optical amplifier; 
        False : Prevent to switch ON the optical amplifier
        """
        return self._get_value('Interlock_Status')

    @property
    def SAS_absorption(self) -> float:
        """ Image of the atomic absorption level. (V) """
        return self._get_value('master_absp')

    @property
    def lock_error(self) -> float:
        """ Value of the lock-in frequency error signal. (V) """
        return self._get_value('master_integ_error')

class SlaveDiode(Diode):

    @property
    def is_locked(self) -> bool:
        """ Status of the slave diode phase lock."""
        laser = short_name(self.laser)
        value = f"Switch_Loop_Phase_Lock_{laser}"
        res = self.api.get(f"/system/monitoring/values/{value}")
        return bool(res['val'])

    @property
    def pll_error(self) -> float:
        """ Value of the PLL error signal (V)."""
        return self._get_value(f"{self.laser}_pll_error")

    @property
    def lock_frequency(self) -> float:
        """ Lock frequency (MHz)"""
        return self._get_value(f"{self.laser}_lock_frequency")

    def _check_aom(self, aom:AOM):
        """ Looks at the configuration dataclass and check if the AOM matches..."""
        attr = f"{aom.name.upper()}_AOM"
        if hasattr(self.config, attr):
            raise ValueError(f"No AOM named '{aom}' in {self.laser.upper()}.")

    ####### EDFA properties ####################""

    @property
    def protection(self) -> str:
        """ Status of the optical amplifier protection. 
        OK : ready to emit ; KO : a hardware security not allow to emit. """
        return self._get_value(f"{self.laser.capitalize()}_Protection")

    @property
    def is_EDFA_enabled(self) -> bool:
        """ State of the optical amplifier. 
        OK : optical amplifier emits ; KO : optical amplifier does not emit. """
        return self._get_value(f"{self.laser.capitalize()}_Enable")
    
    @property
    def phd_EDFA_in(self):
        """ Image of the optical amplifier input power. (V)"""
        return self._get_value(f"{self.laser.capitalize()}_PhdIn")
    
    @property
    def phd_EDFA_out(self):
        """ Image of the optical amplifier output power. (V)"""
        return self._get_value(f"{self.laser.capitalize()}_PhdOut")

    @property
    def current_EDFA(self):
        """ Current feeding the optical amplifier. (A)"""
        return self._get_value(f"{self.laser.capitalize()}_Current")

    def set_edfa_power(self, power_percent: float):
        """ Erbium-doped optical fiber amplifier power in percent or in ampere. """
        self._run_action('powering_edfa', power_percent)

    def get_aom_switch(self, aom:AOM) -> bool:
        self._check_aom(aom)
        return self._get_value(f"{self.laser}_aom_{aom.name}_switch")

    def set_aom_switch(self, aom:AOM, state:bool=False):
        self._check_aom(aom)
        self._run_action(f'aom_{aom.name}_state', state)

    def get_aom_power(self, aom:AOM):
        """ AOM power in percent (%)"""
        self._check_aom(aom)
        return self._get_value(f"{self.laser}_aom_{aom.name}_power")

    def set_aom_power(self, aom:AOM, power_percent:float=0.): 
        """AOM power (%)"""
        self._check_aom(aom)
        self._run_action(f'aom_{aom.name}_power', power_percent)
