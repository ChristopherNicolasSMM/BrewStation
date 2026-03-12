class TemperatureController:

    def __init__(self, pid):
        self.pid = pid

    def control(self, setpoint, current_temp, heater):
        signal = self.pid.compute(setpoint, current_temp)

        if signal > 0:
            heater.on()
        else:
            heater.off()