class_name ItemDef
extends Resource
## An inventory item (docs/technical-plan.md §5.5). Items live at
## res://content/items/<id>/<id>.tres.

@export var id: StringName
@export var display_name := ""
@export var icon: Texture2D
## Where its look line lives: a .dialogue file in content/dialogue and a cue.
@export var look_file: StringName
@export var look_cue: StringName
## Other item id -> the id of the item the two combine into.
@export var combinations := {}
