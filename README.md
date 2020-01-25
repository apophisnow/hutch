# hutch
The coolest LAN Hutch you can make

# Getting started

1. Move the hutch_gamestate_integration.cfg to your csgo cfg directory. Probably something like "C:\Program Files (x86)\Steam\steamapps\common\Counter-Strike Global Offensive\csgo\cfg"

2. Flash your arduino with main.ino.

3. Connect your led strip, default pin is 6, but is configurable.

4. Make sure hutchserver.py is configured correctly for your arduino com port. Line 13: 'arduino = serial.Serial('COM5', 9600, timeout=.1)'

5. Run hutchserver.py: 'python hutchserver.py'

6. Run CSGO. you should see game state data in the output of hutchserver.py. Play the game and test getting flashed. 