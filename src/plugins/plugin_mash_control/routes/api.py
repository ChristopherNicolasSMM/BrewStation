class MashAPI:

    def __init__(self, session_service):
        self.session_service = session_service

    def create_session(self, session_id, session):
        self.session_service.create_session(session_id, session)

    def get_session(self, session_id):
        return self.session_service.get_session(session_id)