class MashStep:

    def __init__(self, temperature, duration):
        self.temperature = temperature
        self.duration = duration


class MashRecipe:

    def __init__(self, name, steps):
        self.name = name
        self.steps = steps