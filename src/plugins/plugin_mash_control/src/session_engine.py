class MashSessionEngine:

    def __init__(self):
        self.state = "created"

    def start(self):
        self.state = "running"

    def pause(self):
        self.state = "paused"

    def resume(self):
        self.state = "running"

    def complete(self):
        self.state = "completed"

    def fail_safe(self):
        self.state = "fail_safe"