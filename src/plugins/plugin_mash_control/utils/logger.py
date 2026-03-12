class MashLogger:

    def log(self, session, message):
        session.logs.append(message)