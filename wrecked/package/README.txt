WRECKED FALLOUT 2
by breakVanilla (https://breakvanilla.com, https://github.com/breakvanilla, youtube.com/@BreakVanilla)

Explosions in Fallout 2 break things. Grenades, rockets and dynamite blow holes in walls, knock down scenery and break through roofs. Debris flies in each wall's own material: stone, wood, metal, glass or cloth. Whatever a blast leaves hanging in the air comes down. Craters, scorch marks and rubble stay on the ground, and the damage is kept in your saves.

Two extra keys, with the mouse cursor on the map:
- X: an orbital beam comes down at the cursor and follows it for two seconds, burning through roofs and setting off blasts.
- G: a meteor falls on the cursor and hits harder and wider than any explosion.
Both are the game's own explosions: they throw people back and hurt everyone near, you too.

WHAT YOU NEED

- Your own copy of Fallout 2 from GOG, Steam or Epic Games.
- Windows 10 or 11 (64-bit), or macOS 11 or later on an Apple Silicon or Intel Mac.

The mod is a new program for the game, built on Fallout 2 Community Edition, and uses your own game files. It needs the game folder of the Windows version, the one with master.dat in it. In Steam: right-click Fallout 2, Manage, Browse local files. GOG installs to C:\GOG Games\Fallout 2 or, with GOG Galaxy, to C:\Program Files (x86)\GOG Galaxy\Games\Fallout 2.

On a Mac, copy that folder from a PC, or unpack the GOG installer for Windows with innoextract (brew install innoextract, then innoextract -I app <installer>.exe).

INSTALL

Windows:
1. If the game folder is in Program Files, copy it elsewhere first, for example to C:\Games\Fallout 2, or the game can't save there.
2. Copy "Wrecked Fallout 2.exe" and the wrecked-fallout-2 folder into the game folder, next to master.dat.
3. Double-click "Wrecked Fallout 2.exe".
4. Windows can show "Windows protected your PC". If it does, click "More info", then "Run anyway".

Mac:
1. Copy "Wrecked Fallout 2.app" and the wrecked-fallout-2 folder into the game folder, next to master.dat.
2. Double-click "Wrecked Fallout 2.app".
3. The first time, macOS says it can't check the app, because the app isn't signed by an Apple developer. If it does, click "Done". Open System Settings, then Privacy & Security, and scroll down. Click "Open Anyway" next to Wrecked Fallout 2, then confirm.
4. If the game folder is in Downloads, Documents or Desktop, click "Allow" when macOS asks.
5. If the game still can't find its files, open Terminal, run this with your own path, and start the game again:
   xattr -dr com.apple.quarantine "/path/to/Fallout 2/Wrecked Fallout 2.app"

SETTINGS

Open wrecked-fallout-2/wrecked.ini in a text editor to turn each part on or off: walls, scenery, craters, screen shake and flash, the beam and the meteor. Each setting is explained in the file. Restart the game after a change.

SAVES

Your saves work with and without the mod. The damage is kept in an extra file, DESTRUCT.DAT, in each save folder; the original game ignores it.

REMOVE THE MOD

Delete the files you copied. The mod doesn't change the game's own files.

PROBLEMS

Report them at https://github.com/breakvanilla/fallout-2-wrecked/issues, with your system and what you did before it went wrong.

LICENCES AND SOURCE

Wrecked Fallout 2 is a modified version of Fallout 2 Community Edition (fallout2-ce) by Alexander Batalov, https://github.com/alexbatalov/fallout2-ce, used under its Sustainable Use License in LICENSE-fallout2-ce.md. The source of the mod is at https://github.com/breakvanilla/fallout-2-wrecked. The program also uses SDL2 and zlib (zlib licence), fpattern (MIT) and, on Windows, the MinGW-w64 runtime; their licences are in wrecked-fallout-2/LICENSES.

The mod has no files from the original game. Fallout 2 is a trademark of Bethesda Softworks. This is a free fan mod, not made or endorsed by Bethesda.
