kivy-autotesting-example
========================

Simple example of implementing selenium-like testing for kivy

Implemented using kivy's Clock mechanism. 

HowTo:

* install all dependencies
* start using ./test.sh

Assertions marked with green rectangle, taps marked with purple circle. Every test must be decorated with `@simulate`,
get simulator as only argument. Also if you don't want to parametrize the test,
 you still also need to decorate it with `@pytest.mark.parametrize("params", [{}])`.
