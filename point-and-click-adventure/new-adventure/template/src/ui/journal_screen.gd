class_name JournalScreen
extends MenuScreen
## The journal (game-design.md §9): The hero's scrapbook. On
## the left, "Who am I?", a page for each memory seen, and the cutscenes that
## can be watched again. On the right, the page: a memory's still and its line,
## or what the hero has learned about themselves.

## A cutscene was picked to watch again; the page has closed.
signal rewatch(id: StringName)

const ENTRIES := preload("res://content/journal/entries.gd")
const LINES := "res://content/dialogue/journal.dialogue"

var _page: VBoxContainer


func _build(content: VBoxContainer) -> void:
	var row := HBoxContainer.new()
	row.name = "Spread"
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	row.add_theme_constant_override(&"separation", 90)
	row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	content.add_child(row)
	var list := VBoxContainer.new()
	list.name = "Contents"
	list.custom_minimum_size.x = 420
	list.add_theme_constant_override(&"separation", 10)
	list.mouse_filter = Control.MOUSE_FILTER_IGNORE
	row.add_child(list)
	list.add_child(text_button("Who am I?", 34, show_self))
	var memories := Journal.memories()
	if not memories.is_empty():
		list.add_child(_heading("Memories"))
		for id in memories:
			list.add_child(text_button(ENTRIES.MEMORIES[id]["title"], 30, show_memory.bind(id)))
	var watchable := Journal.rewatchable()
	if not watchable.is_empty():
		list.add_child(_heading("Watch again"))
		for id in watchable:
			list.add_child(text_button(ENTRIES.REWATCH[id]["title"], 30, watch.bind(id)))
	_page = VBoxContainer.new()
	_page.name = "Page"
	_page.custom_minimum_size = Vector2(760, 520)
	_page.add_theme_constant_override(&"separation", 18)
	_page.mouse_filter = Control.MOUSE_FILTER_IGNORE
	row.add_child(_page)
	show_self()


## The "Who am I?" page.
func show_self() -> void:
	_clear()
	_page.add_child(text_line("Name: %s" % ENTRIES.hero_name(), 40, Color.WHITE))
	if GameState.facts.is_empty():
		_page.add_child(text_line("Nothing I know of yet.", 30))
	for id in GameState.facts:
		var line := text_line(ENTRIES.FACTS.get(id, String(id)), 30)
		line.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		line.custom_minimum_size.x = 760
		_page.add_child(line)


## The page of the memory `id`: its still and its line.
func show_memory(id: StringName) -> void:
	_clear()
	var entry: Dictionary = ENTRIES.MEMORIES[id]
	_page.add_child(text_line(entry["title"], 40, Color.WHITE))
	var picture := TextureRect.new()
	picture.name = "Still"
	picture.custom_minimum_size = Vector2(640, 360)
	picture.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	picture.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	picture.texture = Journal.still(id)
	picture.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_page.add_child(picture)
	var line := text_line("", 28)
	line.name = "Line"
	line.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	line.custom_minimum_size.x = 760
	_page.add_child(line)
	var said: DialogueLine = await DialogueManager.get_next_dialogue_line(load(LINES), String(entry["cue"]))
	if said and is_instance_valid(line):
		line.text = said.text


## Closes the journal and plays the cutscene `id` again.
func watch(id: StringName) -> void:
	rewatch.emit(id)
	close()


## The page showing now (tests).
func page() -> VBoxContainer:
	return _page


func _clear() -> void:
	for child in _page.get_children():
		_page.remove_child(child)
		child.queue_free()


func _heading(text: String) -> Label:
	var heading := text_line(text, 24, Color(0.55, 0.57, 0.63))
	heading.horizontal_alignment = HORIZONTAL_ALIGNMENT_LEFT
	return heading
