
from lib.API import ApiV1
import time 
import sys

def autostart():
    api = ApiV1(sys.argv[1], verbose=True)

    # auth first
    api.auth("admin", "admin")

    # system init
    monit = api.sys_monit_values()
    if not monit['Enable_Current_Laser_Diode_M'] :
        api.sys_action_run('master', 'diode_switch', True, wait_complete=True)
        time.sleep(1)

    monit = api.sys_monit_values()
    if monit['EDFA_Master_PhdOut'] < 3.0 :
        api.sys_action_run('master', 'powering_edfa', 100, wait_complete=True)
        time.sleep(1)
        
    monit = api.sys_monit_values()
    if not monit['Switch_Loop_Freq_Lock_M'] :
        api.sys_action_run('master', 'master_diode_autolock', True, wait_complete=True)

    #api.sys_action_run('master', 'ppln_autoscan', wait_complete=True)

    # set initial seq state
    api.seq_run(
        [
            {
                "duration": 100e-3,
                "active": True,
                "values": {               
                    "slave1_lock_frequency": {
                        "type": "RAMP_DDS",
                        "to": -210e6
                    },
                    "do_trigger_0": False,
                    "do_trigger_1": False,
                    "do_trigger_2": False,
                }
            }
        ],
        triggered=False, 
        loop_count=1, 
        wait_complete=True
    )

    # run experience
    api.seq_run(
        [
            {
                "duration": 500e-3,
                "active": True,
                "values": {
                    "slave1_lock_frequency": {"type": "RAMP_DDS","from": "down","to": "top"},
                    "do_trigger_0": True,
                    "do_trigger_1": False
                }
            },
            {
                "duration": 500e-3,
                "active": True,
                "values": {
                    "slave1_lock_frequency": { "type": "RAMP_DDS", "from": "top", "to": "down"},
                    "do_trigger_0": False,
                    "do_trigger_1": True
                }
            }
        ],
        aliases={
            "top": -100e6,
            "down": -210e6
        },
        triggered=False, 
        loop_count=10, 
        wait_complete=True)

def capabilities():
    api = ApiV1(sys.argv[1], verbose=True)

    # auth first
    api.auth("admin", "admin")

    monits = api.sys_monit_roles()
    actions = api.sys_actions_roles()
    sequencer = api.seq_roles()

    print()
    print("Monit:")
    for value in monits :
        print('|--', value['id'])
        print('|   |-- name:', value['name'])
        print('|   |-- desc:', value['desc'])
        print('|   |-- unit:', value['unit'])

    print()
    print("Actions:")
    for group in actions :
        print('|--', group['id'])
        print('|   |-- name:', group['name'])
        print('|   |-- desc:', group['desc'])
        print('|   |-- actions:')
        for action in group['actions'] :
            print('|   |   |--', action['id'])
            print('|   |   |   |-- name:', action['name'])
            print('|   |   |   |-- desc:', action['desc'])
            print('|   |   |   |-- type:', action['type'])

    print()
    print("Sequencer:")
    for value in sequencer :
        print('|--', value['id'])
        print('|   |-- name:', value['name'])
        print('|   |-- desc:', value['desc'])
        print('|   |-- type:', value['type'])
        print('|   |-- unit:', value['unit'])
        print('|   |-- default:', value['default'])
        print('|   |-- rules:')
        for rule in value['rules'] :
            print('|   |   |--', rule)


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("usage:", sys.argv[0], "{HOST} [capabilities|autostart]")
        sys.exit(1)

    if sys.argv[2] == 'capabilities':
        capabilities()
    elif sys.argv[2] == 'autostart':
        autostart()
    else:
        print("wrong command.")
