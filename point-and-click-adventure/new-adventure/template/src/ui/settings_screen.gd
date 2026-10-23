class_name SettingsScreen
extends MenuScreen
## The settings page: a slider for each volume, and a line
## for each choice that moves to its next value with a click. Every change
## applies at once (see the Settings autoload).

const VOLUMES := [
	[&"voice_volume", "Voice"],
	[&"music_volume", "Music"],
	[&"ambience_volume", "Ambience"],
	[&"effects_volume", "Effects"],
]
## Each choice: its setting, its name, and its values with their labels.
const CHOICES := [
	[&"subtitles", "Subtitles", [[true, "On"], [false, "Off"]]],
	[&"subtitle_size", "Subtitle size", [[0.85, "Small"], [1.0, "Normal"], [1.25, "Large"], [1.5, "Larger"]]],
	[&"text_speed", "Text speed", [[0.75, "Slow"], [1.0, "Normal"], [1.5, "Fast"]]],
	[&"reduce_flashing", "Reduce flashing", [[false, "Off"], [true, "On"]]],
	[&"reduce_camera_motion", "Reduce camera motion", [[false, "Off"], [true, "On"]]],
	[&"fullscreen", "Fullscreen", [[false, "Off"], [true, "On"]]],
	[&"render_1080p", "Render at 1080p", [[false, "Off"], [true, "On"]]],
]

var _values := {}
var _sliders := {}


func _build(content: VBoxContainer) -> void:
	var grid := GridContainer.new()
	grid.name = "Settings"
	grid.columns = 2
	grid.add_theme_constant_override(&"h_separation", 80)
	grid.add_theme_constant_override(&"v_separation", 14)
	grid.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	grid.mouse_filter = Control.MOUSE_FILTER_IGNORE
	content.add_child(grid)
	for volume: Array in VOLUMES:
		grid.add_child(text_line(volume[1], 32, Color.WHITE))
		var slider := HSlider.new()
		slider.name = String(volume[0]).to_pascal_case()
		slider.min_value = 0.0
		slider.max_value = 1.0
		slider.step = 0.05
		slider.custom_minimum_size = Vector2(420, 40)
		slider.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		slider.value = Settings.get(volume[0])
		slider.value_changed.connect(func(value: float) -> void: Settings.set(volume[0], value))
		_sliders[volume[0]] = slider
		grid.add_child(slider)
	for choice: Array in CHOICES:
		grid.add_child(text_line(choice[1], 32, Color.WHITE))
		var value := text_button(_label_of(choice), 32, cycle.bind(choice[0]))
		value.name = String(choice[0]).to_pascal_case()
		_values[choice[0]] = value
		grid.add_child(value)


## Moves the setting `key` on to its next value, as a click on it does.
func cycle(key: StringName) -> void:
	var choice := _choice(key)
	var options: Array = choice[2]
	Settings.set(key, options[(_index_of(options, Settings.get(key)) + 1) % options.size()][0])
	(_values[key] as Label).text = _label_of(choice)


## The slider for the volume setting `key`, for tests.
func slider(key: StringName) -> HSlider:
	return _sliders.get(key)


## The line showing the choice `key`, for tests.
func value_line(key: StringName) -> Label:
	return _values.get(key)


func _choice(key: StringName) -> Array:
	for choice: Array in CHOICES:
		if choice[0] == key:
			return choice
	return []


func _label_of(choice: Array) -> String:
	var options: Array = choice[2]
	return options[maxi(_index_of(options, Settings.get(choice[0])), 0)][1]


## Which option `value` is: the equal one, or for numbers the nearest.
static func _index_of(options: Array, value: Variant) -> int:
	var best := -1
	for i in options.size():
		if typeof(options[i][0]) == TYPE_BOOL:
			if options[i][0] == value:
				return i
		elif best < 0 or absf(float(options[i][0]) - float(value)) < absf(float(options[best][0]) - float(value)):
			best = i
	return best
