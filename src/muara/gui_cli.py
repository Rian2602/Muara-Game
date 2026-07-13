"""Entry point for Muara GUI mode."""

from muara.gui.app import MuaraApp


def main() -> None:
    app = MuaraApp()
    app.run()


if __name__ == "__main__":
    main()
