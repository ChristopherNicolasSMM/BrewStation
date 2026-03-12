import time

class MashProcessEngine:

    def __init__(self, temp_controller, sensor, heater):
        self.temp_controller = temp_controller
        self.sensor = sensor
        self.heater = heater

    def run_step(self, step):
        start = time.time()

        while (time.time() - start) < step.duration:
            temp = self.sensor.read()

            self.temp_controller.control(
                step.temperature,
                temp,
                self.heater
            )

            time.sleep(1)