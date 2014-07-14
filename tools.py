from functools import partial

from kivy.properties import Clock


def to_task(s):
    s.press("//MenuButtonTitled[@name='LOGO']")
    s.assert_on_screen('activity')
    s.press('//StartNowButton')
    s.assert_on_screen('tasks')
    s.tap("//TestIntro//TestCarouselForwardButton")
    s.assert_on_screen("test", manager_selector="//TasksScreen/ScreenManager")
    s.tap("//BlinkImageButton[@name='task_icon']")


def without_schedule_seconds(function):
    def inner(*args, **kwargs):
        function(*args[:-1], **kwargs)

    return inner


def wait(seconds):
    def real_decorator(function):
        def wrapper(*args, **kwargs):
            Clock.schedule_once(partial(without_schedule_seconds(function), *args, **kwargs), seconds)

        return wrapper

    return real_decorator


def simulate(function):
    def simulate_inner(simulator, params):
        simulator.start(function, params or {})

    simulate_inner.settings = getattr(function, "settings", {})
    return simulate_inner


def execution_step(function):
    def execution_step_inner(self, *args, **kwargs):
        self.execution_queue.append((function, args, kwargs))

    return execution_step_inner


def override_settings(**settings):
    def real_override_settings(function):
        def inner_override_settings(*args, **kwargs):
            function(*args, **kwargs)

        inner_override_settings.settings = settings
        return inner_override_settings

    return real_override_settings
