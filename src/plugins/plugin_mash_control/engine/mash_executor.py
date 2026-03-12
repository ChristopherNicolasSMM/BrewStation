import time

class MashExecutor:

    def __init__(self, pid):
        self.pid = pid

    def execute_step(self, target_temp, duration, sensor, heater):
        start = time.time()

        while time.time() - start < duration:
            current_temp = sensor.read()
            control = self.pid.compute(target_temp, current_temp)

            if control > 0:
                heater.on()
            else:
                heater.off()

            time.sleep(1)