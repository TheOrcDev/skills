extends Node
## The top bar and the pages it opens. The bar comes down
## when the cursor pushes against the top edge while the player is free to act.
## A page pauses the game until it closes; loading a slot happens after its page
## has closed. The start screen is here too: main.gd shows it at
## launch, and the bar's Main menu brings it up over the paused game.

## New Game was chosen on the start screen and the old game, if any, has gone;
## main.gd starts the game from the opening.
signal new_game_requested

## The open page, or null.
var screen: MenuScreen
## The start screen while it is up, or null.
var title: TitleScreen
var bar: TopBar
var hotspots: HotspotReveal
## Off in scripted QA runs, so a stray cursor at the top of the window cannot
## bring the bar into a recording.
var enabled := true


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	bar = TopBar.new()
	bar.name = "TopBar"
	bar.chosen.connect(choose)
	add_child(bar)
	hotspots = HotspotReveal.new()
	hotspots.name = "HotspotReveal"
	add_child(hotspots)


func _process(_delta: float) -> void:
	# Headless runs have no cursor; tests call bar.follow() themselves, and a
	# scripted run that switched the bar off may still open it by hand.
	if enabled and DisplayServer.get_name() != "headless":
		bar.follow(get_viewport().get_mouse_position(), can_open())


## Whether the bar may come down: a room is showing and nothing else has the
## player's attention. Not inside a playable memory, which a save could not
## resume.
func can_open() -> bool:
	return enabled and screen == null and title == null and Rooms.current != null and Interaction.locked == 0 \
		and not Interaction.coin.is_open and not Interaction.inventory.is_open and not Flashback.in_memory


## Runs the bar's entry `id`.
func choose(id: StringName) -> void:
	bar.hide_now()
	match id:
		&"journal":
			var page := JournalScreen.new()
			page.title = "Journal"
			page.rewatch.connect(func(id: StringName) -> void: Journal.rewatch.call_deferred(id))
			open_page(page)
		&"save":
			# The thumbnail is the game as it was, so it waits for a frame without the bar.
			await get_tree().process_frame
			await get_tree().process_frame
			var page := SlotsScreen.new()
			page.title = "Save"
			page.saving = true
			page.picture = Saves.screen_image()
			open_page(page)
		&"load":
			var page := SlotsScreen.new()
			page.title = "Load"
			page.saving = false
			page.picked.connect(func(slot: int) -> void: Saves.load_slot.call_deferred(slot))
			open_page(page)
		&"settings":
			var page := SettingsScreen.new()
			page.title = "Settings"
			open_page(page)
		&"hotspots":
			hotspots.reveal()
		&"menu":
			# Save Game's thumbnail is the game as it was, so it waits for a
			# frame without the bar.
			await get_tree().process_frame
			await get_tree().process_frame
			show_title(true, Saves.screen_image())
		&"quit":
			confirm("Leave the game?", "Quit", func() -> void: get_tree().quit())


## Shows the start screen: at launch, or with `in_game` over the paused game,
## whose look before the screen opened is `picture`.
func show_title(in_game := false, picture: Image = null) -> void:
	if title:
		return
	if screen:
		screen.close()
	title = TitleScreen.new()
	title.name = "TitleScreen"
	title.in_game = in_game
	title.picture = picture
	title.chosen.connect(choose_on_title)
	title.tree_exited.connect(func() -> void:
		title = null
		if screen == null:
			get_tree().paused = false)
	get_tree().paused = in_game
	Cursors.show_for(null)
	add_child(title)


## Runs the start screen's entry `id`.
func choose_on_title(id: StringName) -> void:
	if title == null:
		return
	var page_title := title
	match id:
		&"resume":
			title.close()
		&"continue":
			var slot := Saves.latest_slot()
			if slot >= 0:
				title.leave(_load.bind(slot))
		&"new_game":
			if title.in_game or Saves.latest_slot() >= 0:
				confirm("Start a new game?", "Begin", func() -> void:
					if page_title == title:
						title.leave(_new_game),
					"Your saved games stay. The autosave will be replaced." if not title.in_game else "Your saved games stay. Anything since the last save is lost.")
			else:
				title.leave(_new_game)
		&"load":
			var page := SlotsScreen.new()
			page.title = "Load"
			page.saving = false
			page.picked.connect(func(slot: int) -> void:
				if page_title == title:
					title.leave(_load.bind(slot)))
			open_page(page)
		&"save":
			var page := SlotsScreen.new()
			page.title = "Save"
			page.saving = true
			page.picture = title.picture
			open_page(page)
		&"settings":
			var page := SettingsScreen.new()
			page.title = "Settings"
			open_page(page)
		&"quit":
			if title.in_game:
				confirm("Leave the game?", "Quit", func() -> void: get_tree().quit())
			else:
				get_tree().quit()


## A page that asks `question`, with `yes` running `action` and Stay closing it,
## and `note` under the question.
func confirm(question: String, yes: String, action: Callable, note := "") -> void:
	var page := MenuScreen.new()
	page.title = question
	page.ready.connect(func() -> void:
		var content := page.get_node(^"Content")
		if not note.is_empty():
			content.add_child(MenuScreen.text_line(note, 30))
			var gap := Control.new()
			gap.custom_minimum_size = Vector2(0, 40)
			content.add_child(gap)
		var row := HBoxContainer.new()
		row.name = "Answers"
		row.alignment = BoxContainer.ALIGNMENT_CENTER
		row.add_theme_constant_override(&"separation", 120)
		row.add_child(MenuScreen.text_button(yes, 40, func() -> void:
			page.close()
			action.call()))
		row.add_child(MenuScreen.text_button("Stay", 40, page.close))
		content.add_child(row))
	open_page(page)


## Ends the game in progress, if any, and asks main.gd for a new one, while the
## start screen is black.
func _new_game() -> void:
	await _end_game()
	GameState.reset()
	new_game_requested.emit()


## Loads `slot` in place of the game in progress, if any, while the start
## screen is black.
func _load(slot: int) -> void:
	await _end_game()
	Saves.autosave = true
	Saves.load_slot(slot)


## Takes down the game in progress: its close-up, its room and the hero. The
## start screen only opens from the bar, when nothing else is going on.
func _end_game() -> void:
	get_tree().paused = false
	Saves.autosave = false
	if Closeups.current:
		await Closeups.close()
	Rooms.clear()


## Shows `page` over the paused game.
func open_page(page: MenuScreen) -> void:
	if screen:
		screen.close()
	screen = page
	get_tree().paused = true
	Cursors.show_for(null)
	page.closed.connect(func() -> void:
		if screen == page:
			screen = null
			get_tree().paused = title != null and title.in_game)
	add_child(page)
