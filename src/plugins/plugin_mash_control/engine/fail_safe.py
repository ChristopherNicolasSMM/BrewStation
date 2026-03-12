class FailSafeSystem:

    def check_temp(self, current, limit):
        if current > limit:
            raise Exception("FAIL SAFE: temperature limit exceeded")