from kivy.app import App
from kivy.uix.boxlayout import BoxLayout


class RootWidget(BoxLayout):
    def go_back(self):
        if self.screen_names.index(self.current) == 0:
            exit()
        else:
            self.current = self.previous()


class AutotestingApp(App):
    def build(self):
        root = RootWidget()
        return root


if __name__ == '__main__':
    app = AutotestingApp()
    app.run()
