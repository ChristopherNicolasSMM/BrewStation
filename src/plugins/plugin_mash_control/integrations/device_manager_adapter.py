class DeviceManagerAdapter:

    def __init__(self, manager=None):
        self.manager = manager

    def get_sensor(self, device_id):
        if self.manager:
            return self.manager.get_sensor(device_id)
        raise Exception("device_manager not available")

    def get_actuator(self, device_id):
        if self.manager:
            return self.manager.get_actuator(device_id)
        raise Exception("device_manager not available")