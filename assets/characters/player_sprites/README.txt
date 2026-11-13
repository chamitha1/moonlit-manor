MOONLIT MANOR - PLAYER SPRITES (complete set). Replaces the earlier player_walk and player_idle zips.
Copy everything into res://assets/characters/player/

MAIN SPRITE (AnimatedSprite2D, 32x32 frames, Offset 0,-16)
  walk_down/up/right/left.png   4 frames (128x32). Sheet import: Horizontal 4, Vertical 1. 8 FPS, Loop on.
  idle_down/up/right/left.png   8 frames (256x32): stand, stand, breathe, breathe, stand, BLINK, breathe, breathe.
                                Sheet import: Horizontal 8, Vertical 1. 4 FPS, Loop on. (Up view has no blink.)

FISHING SPRITE (second AnimatedSprite2D "FishingSprite", 64x48 frames, Offset 0,-24, hidden by default)
  fishing/fish_windup_right/left.png  1 frame   -> CHARGING
  fishing/fish_cast_right/left.png    1 frame   -> cast
  fishing/fish_wait_right/left.png    2 frames (128x48), 2 FPS loop -> WAITING / BITE
  fishing/fish_reel_right/left.png    2 frames (128x48), 6 FPS loop -> REELING
  fishing/fish_catch.png              1 frame   -> catch celebration
Feet and head line up with the main sprite, so swapping sprites does not make him jump.
The rod has no line: draw it with a Line2D from the rod tip to the bobber.

preview_*.gif / preview_fishing.png  check the motion and poses.
build_player.py                      the conversion script.
