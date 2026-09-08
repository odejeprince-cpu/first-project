def check_length(password):
    if len(password) >= 8:
        return True
    else:
        return False

def check_special_char(password):
    special_characters = "!@#$%^&*(),.?\":{}|<>"
    for char in password:
        if char in special_characters:
            return True
    return False

def check_digit(password):
    for char in password:
        if char.isdigit():
            return True
    return False

def check_lowercase(password):
    for char in password:
        if char.islower():
            return True
    return False

def check_uppercase(password):
    for char in password:
        if char.isupper():
            return True
    return False

def check_password_strength(password):
    score = 0
    feedback = []

    if check_length(password):
        score += 1
    else:
        feedback.append("password should be at least 8 characters")

    if check_uppercase(password):
        score += 1
    else:
        feedback.append("add atleast 1 uppercase letter")

    if check_special_char(password):
        score += 1
    else:
        feedback.append("add atleast 1 special character")

    if check_digit(password):
        score += 1
    else:
        feedback.append("add at least 1 digit")
    
    if check_lowercase(password):
        score += 1
    else:
        feedback.append("add at least 1 lowercase")
    return score, feedback

def get_strength_label(score):
    if score <= 2:
        return "weak password"
    elif score <= 4:
        return "moderate password"
    else:
        return "strong password"