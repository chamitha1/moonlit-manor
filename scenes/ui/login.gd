extends Control
@onready var username: LineEdit = $Background/CenterContainer/PanelContainer/VBoxContainer/Username
@onready var error_label: Label = $Background/CenterContainer/PanelContainer/VBoxContainer/ErrorLabel
@onready var password: LineEdit = $Background/CenterContainer/PanelContainer/VBoxContainer/Password


# Called when the node enters the scene tree for the first time.
func _ready() -> void:
	pass # Replace with function body.


## Called every frame. 'delta' is the elapsed time since the previous frame.
#func _process(delta: float) -> void:
	#pass


func _on_login_button_pressed() -> void:
	if username.text.strip_edges().length() < 3:
		error_label.text = "username need at least 3 letters"
		return
	get_tree().change_scene_to_file("res://scenes/ui/shop_ui.tscn")
	
	


func _on_registration_button_pressed() -> void:
	error_label.text = "Coming soon"
