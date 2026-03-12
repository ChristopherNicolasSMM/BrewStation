class DashboardLayout:

    def __init__(self):
        self.elements = []

    def add_equipment(self, name, role):
        self.elements.append({
            "name": name,
            "role": role
        })