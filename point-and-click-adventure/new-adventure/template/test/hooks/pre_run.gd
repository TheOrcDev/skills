extends GutHookScript
## Runs before the tests: settings start from their defaults, in a file of their
## own, so a player's settings never change how the tests behave.


func run() -> void:
	Settings.path = "user://test-settings.cfg"
	Settings.reset()
