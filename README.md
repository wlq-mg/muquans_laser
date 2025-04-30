This is library to control the Integrated Laser System (ILS780-2401) for the QDNG experiment.

It provides:
- configuration dataclasses for each slave (AOMS / limits...)
- access all the monitroring values for each diode/EDFA.
- control all the experimental parameters: enabling diodes, locking, set the power/frequency ...
- program an experimental sequence: Since the API doesn't offer any AO_RAMPS, I tried to devide ramps into smaller chunks (all keeping it in parralel for multiple channels).
