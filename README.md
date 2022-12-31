# hutch
The coolest LAN Hutch you can make

# Getting started

1. Move the hutch_gamestate_integration.cfg to your csgo cfg directory. Probably something like "C:\Program Files (x86)\Steam\steamapps\common\Counter-Strike Global Offensive\csgo\cfg"

2. Run hutchserver.py: 'python hutchserver.py'

3. Run CSGO. you should see game state data in the output of hutchserver.py. Play the game and test getting flashed.

Hutchserver will scan for WLED devices on your network and may ask you to select one if more than one are found. When connected successfully your LEDs should flash green three times, and then go into a colorloop idle animation.

Once CSGO is sending data, getting flashbanged in the game should make your LEDs flash white then fade. Other game state has other effects.