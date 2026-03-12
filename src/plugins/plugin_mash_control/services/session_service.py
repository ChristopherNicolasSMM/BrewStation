class SessionService:

    def __init__(self):
        self.sessions = {}

    def create_session(self, session_id, session):
        self.sessions[session_id] = session

    def get_session(self, session_id):
        return self.sessions.get(session_id)

    def list_sessions(self):
        return list(self.sessions.values())