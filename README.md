<picture>  
<source media="(prefers-color-scheme: dark)" srcset="https://i.imgur.com/8qsV6MH.png">  
<source media="(prefers-color-scheme: light)" srcset="https://i.imgur.com/4cpzGnB.png">  
<img src="https://i.imgur.com/8qsV6MH.png" width="200">  
</picture>  

*Part of the tico ecosystem* — https://www.ticoverse.com

**blueMSX** is an emulator for the MSX family of home computers (MSX, MSX2, MSX2+ and turbo R) and the related ColecoVision, Spectravideo SVI-318/328 and Sega SC-3000.

This fork adapts blueMSX to work with the tico frontend and provides a standalone build for the Nintendo Switch, adding a small set of practical features while keeping the original experience familiar.

----------

## Summary

This fork focuses on making blueMSX more usable in practice without changing its core purpose.

It adds:

-   Custom overlay matching tico design, including time, date, user avatar, and game title
-   Explicit control over display (integer scaling and aspect ratios)
-   Runtime-selectable rendering filters  
-   Built-in save and load state support
-   Integrated RetroAchievements with custom alerts
-   MSX cartridges out of the box on the free C-BIOS; an on-screen keyboard on Select, and the pad as keyboard keys when a game wants them
-   Multi-disk games through .m3u playlists, with Change Disc in the quick menu

----------

## Credits

This fork is built on top of the libretro port of blueMSX, by Daniel Vik and the blueMSX team.
All core emulation work belongs to the blueMSX authors and contributors.

- **blueMSX website** — http://www.bluemsx.com
- **libretro blueMSX** — https://github.com/libretro/blueMSX-libretro

----------

## A Note

A lot of work in this scene disappears over time — not because it lacked value, but because it was never shared.

If you are building something, consider releasing it. Even small contributions can help others move forward.