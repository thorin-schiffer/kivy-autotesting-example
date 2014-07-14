#!/bin/sh
export KIVY_UNITTEST="true"
py.test -v --tb=short
