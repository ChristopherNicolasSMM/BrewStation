class MashControlPlugin:

    def __init__(self, app):
        self.app = app
        self.name = "mash_control"

    def start(self):
        print("Mash Control plugin started")

    def stop(self):
        print("Mash Control plugin stopped")