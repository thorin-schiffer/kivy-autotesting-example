import pytest
from tools import simulate

from simulator_fixture import simulator

@pytest.mark.parametrize("params", [{}])
@simulate
def test_example(simulator):

    # widgets are selected with xpath
    simulator.assert_count("//RootWidget//Button", 3)

    # deep tree goes reversed through the tree
    simulator.assert_text("//RootWidget//Button[1]", "Third")
    simulator.assert_text("//RootWidget//Button[2]", "Second")
    simulator.assert_text("//RootWidget//Button[3]", "First")

    simulator.assert_text("//RootWidget//StatusLabel", "Status")

    simulator.tap("//RootWidget//Button[3]")
    simulator.assert_text("//RootWidget//StatusLabel", "First pressed")

    simulator.tap("//RootWidget//Button[2]")
    simulator.assert_text("//RootWidget//StatusLabel", "Second pressed")

    simulator.assert_disabled("//RootWidget//Button[1]")
