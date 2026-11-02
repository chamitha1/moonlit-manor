extends TextureProgressBar

@export var seconds := 30.0


func _ready() -> void:
	step = 0.01    
	
func _process(delta: float) -> void:
	value = max(value - 100.0 / seconds * delta, 0.0)
	if value < 30.0:
		modulate = Color("#d1567a") 
