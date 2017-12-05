def user_is_anonymous(user):
    try:
        # for django 1.8
        return user.is_anonymous()
    except TypeError:
        return user.is_anonymous
