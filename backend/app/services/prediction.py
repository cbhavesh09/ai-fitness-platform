from backend.app.models.user import User


def calculate_calorie_burn(user: User) -> tuple[float, float]:
    """
    Calculate estimated daily calorie burn using the Mifflin-St Jeor
    equation and the user's activity level.

    Returns:
        tuple[float, float]:
            estimated calorie burn and confidence score.
    """

    if user.gender.lower() == "male":
        bmr = (
            10 * user.weight_kg
            + 6.25 * user.height_cm
            - 5 * user.age
            + 5
        )
    else:
        bmr = (
            10 * user.weight_kg
            + 6.25 * user.height_cm
            - 5 * user.age
            - 161
        )

    activity_multipliers = {
        "sedentary": 1.2,
        "light": 1.375,
        "moderate": 1.55,
        "active": 1.725,
        "very_active": 1.9,
    }

    multiplier = activity_multipliers.get(
        user.activity_level.lower(),
        1.2,
    )

    calorie_burn = bmr * multiplier

    confidence = 0.80

    return round(calorie_burn, 2), confidence