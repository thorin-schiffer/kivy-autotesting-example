from kivy import kivy_data_dir
import os

import pytest

from simulation import Simulator


@pytest.fixture
def simulator(request):
    from main import AutotestingApp
    application = AutotestingApp()
    simulator = Simulator(application)

    def fin():

        simulator.clean_queue()

        from kivy.lang import Builder

        files = list(Builder.files)
        for filename in files:
            Builder.unload_file(filename)
        kivy_style_filename = os.path.join(kivy_data_dir, 'style.kv')
        if not kivy_style_filename in Builder.files:
            Builder.load_file(kivy_style_filename, rulesonly=True)

    request.addfinalizer(fin)
    return simulator
