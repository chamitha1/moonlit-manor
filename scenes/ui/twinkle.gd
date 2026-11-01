# twinkle.gd
extends TextureRect

func _ready() -> void:
	var tween := create_tween().set_loops()
	tween.tween_property(self, "modulate:a", 0.25, randf_range(0.8, 1.8))
	tween.tween_property(self, "modulate:a", 1.0, randf_range(0.8, 1.8))
