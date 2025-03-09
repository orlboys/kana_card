import re

def test_password(password):
    patterns = {
        'uppercase': r'[A-Z]',
        'lowercase': r'[a-z]',
        'number': r'[0-9]',
        'special': r'[@$%*?&]'
    }

    results = {}
    for key, pattern in patterns.items():
        results[key] = bool(re.search(pattern, password))

    return results

password = 'Password1@'
print(test_password(password))