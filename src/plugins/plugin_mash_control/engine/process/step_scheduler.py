class StepScheduler:

    def __init__(self, engine):
        self.engine = engine

    def run_recipe(self, recipe):
        for step in recipe.steps:
            self.engine.run_step(step)