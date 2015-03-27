from functools import partial
from lxml import etree
from kivy import Logger

from kivy.animation import Animation
from kivy.properties import StringProperty, BooleanProperty
from kivy.clock import Clock

from tools import execution_step, without_schedule_seconds


class Simulator(object):
    TO_WAIT = 1
    PROPERTY_CLASSES_TO_ATTRIBUTES = {
        StringProperty: lambda x: x if x else str(x),
        BooleanProperty: lambda x: str(x).lower(),
    }
    START_DELAY = 2
    EXECUTE_STEP_DELAY = .5

    def __init__(self, app):
        self.app = app
        self.collected_widgets = None
        self.tree = None
        self.execution_queue = []

    def _get_prop_values(self, widget):
        result = {}
        for prop_name, property_object in widget.properties().items():
            if prop_name.startswith("__") or property_object.__class__ in self.PROPERTY_CLASSES_TO_ATTRIBUTES:
                result[prop_name.replace("__", "")] = self.PROPERTY_CLASSES_TO_ATTRIBUTES[
                    property_object.__class__](
                    getattr(widget, prop_name)
                )
        return result

    def build_deep(self, widget):
        props = self._get_prop_values(widget)
        try:
            element = etree.Element(widget.__class__.__name__, __element_id=str(len(self.collected_widgets)), **props)
        except TypeError, ex:
            print "Error while creating  element. %s, %s" % (props, ex)
            raise ex
        self.collected_widgets.append(widget)
        for child in widget.children:
            element.append(self.build_deep(child))
        return element

    def rebuild_tree(self):
        self.collected_widgets = []
        self.tree = self.build_deep(self.app.root)

    def xml_tree(self):
        return etree.tostring(self.tree, pretty_print=True)

    def trigger_event(self, event, selector):
        nodes = self.tree.xpath(selector)
        assert nodes, "Attempt to trigger %s for %s, but no nodes were found" % (event, selector)
        for node in nodes:
            widget = self.node_to_widget(node)
            widget.dispatch(event)
            self._mark_event(widget)

    @execution_step
    def press(self, selector, release=False):
        Logger.info("Simulation: Press %s" % selector)
        self.rebuild_tree()

        self.trigger_event('on_press', selector)
        if release:
            self.trigger_event('on_release', selector)

    def tap(self, selector):
        self.press(selector, release=True)

    @execution_step
    def wait(self, seconds):
        Logger.info("Simulation: wait %s seconds..." % seconds)
        return seconds

    def start(self, callback, params):
        callback(self, **params)
        Clock.schedule_once(self.execute, self.START_DELAY)
        if not self.app.built:
            self.app.run()


    def stop(self, _):
        self.app.stop()

    def _execute_step(self, index, _):
        if index >= len(self.execution_queue):
            Clock.schedule_once(self.stop, .1)
            return

        function, args, kwargs = self.execution_queue[index]

        function(self, *args, **kwargs)

        if function.__name__ == 'wait':
            delay = kwargs.get('seconds', args[0])
        else:
            delay = self.EXECUTE_STEP_DELAY
        Clock.schedule_once(partial(self._execute_step, index + 1), delay)

    def clean_queue(self):
        Logger.info("Simulation: drop execution queue")
        for function, args, kwargs in self.execution_queue:
            Clock.unschedule(function)
        self.execution_queue = []

    def execute(self, *args):
        Clock.schedule_once(partial(self._execute_step, 0))

    def node_to_widget(self, node):
        if isinstance(node, list) and len(node) == 1:
            node = node[0]
        widget = self.collected_widgets[int(node.get('__element_id'))]
        return widget

    # ASSERTIONS
    def assert_exists(self, selector, to_mark=True):
        self.rebuild_tree()
        nodes = self.tree.xpath(selector)
        assert nodes, ("%s not found in widgets tree" % selector)
        if len(nodes) > 1:
            raise RuntimeError("Multiple nodes found for selector %s" % selector)
        widget = self.node_to_widget(nodes)
        if to_mark:
            self._mark_assertion(widget)
        return widget

    @execution_step
    def assert_count(self, selector, count):
        self.rebuild_tree()
        nodes = self.tree.xpath(selector)
        for node in nodes:
            self._mark_assertion(self.node_to_widget(node))
        assert len(nodes) == count, "%s selects %s nodes, not %s" % (selector, len(nodes), count)

    @execution_step
    def assert_not_exists(self, selector):
        self.rebuild_tree()
        assert not self.tree.xpath(selector), \
            ("%s found in widgets tree, but shouldn't be there" % selector)

    @execution_step
    def assert_disabled(self, selector):
        Logger.info("Simulation: assert %s is disabled" % selector)
        self.assert_attr(selector, "disabled", True)

    @execution_step
    def assert_enabled(self, selector):
        Logger.info("Simulation: assert %s is enabled" % selector)
        self.assert_attr(selector, "disabled", False)

    def _get_attr_with_period(self, obj, attrs):
        attrs = attrs.split(".")
        res = obj
        for attr in attrs:
            res = getattr(res, attr)
        return res

    @execution_step
    def assert_attr(self, selector, attr, value):
        node_attr_value = self._get_attr_with_period(self.assert_exists(selector), attr)
        assert node_attr_value == value, "%s.%s is not %s but %s" % (selector, attr, value, node_attr_value)

    def assert_text(self, selector, value):
        Logger.info("Simulation: assert %s has text %s" % (selector, value))
        self.assert_attr(selector, 'text', value)

    def _mark_assertion(self, widget):
        from kivy.graphics import Color, Rectangle

        with widget.canvas.after:
            color = Color(0, 1, 0, .8)
            rect_pos = (widget.x + widget.width / 2, widget.y + widget.height / 2)
            rectangle = Rectangle(pos=rect_pos, size=(0, 0))
            Animation(a=0, duration=self.EXECUTE_STEP_DELAY / 2, t='in_out_cubic').start(color)
            Animation(size=widget.size,
                      pos=widget.pos,
                      duration=self.EXECUTE_STEP_DELAY / 2,
                      t='in_out_cubic').start(rectangle)

    def _mark_event(self, widget):
        from kivy.graphics import Ellipse, Color

        with widget.canvas.after:
            color = Color(1, 0, 1, .8)
            d = min(widget.size)
            circle_pos = (widget.x + widget.width / 2, widget.y + widget.height / 2)
            circle = Ellipse(pos=circle_pos, size=(0, 0))
            Animation(a=0, duration=self.EXECUTE_STEP_DELAY / 2, t='in_out_cubic').start(color)

            point_pos = (widget.x + widget.width/2 - d / 2, widget.y) if widget.width > widget.height\
                else (widget.x, widget.y + widget.height/2 - d / 2)

            Animation(size=(d, d),
                      pos=point_pos,
                      duration=self.EXECUTE_STEP_DELAY / 2,
                      t='in_out_cubic').start(circle)
