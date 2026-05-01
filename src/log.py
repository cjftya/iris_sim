debug_mode = True

class Logger:

    @staticmethod
    def log(msg, value=None):
        if debug_mode:
            if value is None:
                print(f"\n[DEBUG] {msg}\n")
            else:
                print(f"\n[DEBUG] {msg}\n {value}\n")