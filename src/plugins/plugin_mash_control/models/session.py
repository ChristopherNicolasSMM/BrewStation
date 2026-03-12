class MashSession:

    STATES = [
        "created",
        "running",
        "paused",
        "completed",
        "aborted",
        "fail_safe"
    ]

    def __init__(self, recipe, plant_id):
        self.recipe = recipe
        self.plant_id = plant_id
        self.state = "created"
        self.current_step = 0
        self.logs = []