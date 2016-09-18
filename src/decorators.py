from utils import post_message


def require_registration(func):
    def func_wrapper(slack_user, *args, **kwargs):
        if not slack_user.tea_type:
            return post_message('You need to register first.')
        else:
            return func(slack_user, *args, **kwargs)
    return func_wrapper
