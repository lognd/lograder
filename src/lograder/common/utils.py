import random
import string


def random_name(length=25) -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))
