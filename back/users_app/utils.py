import random
import string


def generate_activation_code():
    return ''.join(random.choice(string.digits) for _ in range(4))


def has_company_access(user, company):
    return bool(user.role == 'manager' and user.company == company or user.role == 'admin')
