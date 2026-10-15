/// @file TicoConfig.h
/// @brief Minimal hardcoded configuration for tico overlay (blueMSX)
#pragma once

#include <algorithm>
#include <cctype>
#include <string>

namespace TicoConfig {
    constexpr const char* TEST_ROM = "sdmc:/tico/roms/msx/rom.rom";

    constexpr const char* FONT_PATH = "romfs:/fonts/font.ttf";

    // Current console slug (msx, msx2, colecovision, spectravideo or sc-3000,
    // from argv[1])
    inline std::string CURRENT_SLUG = "msx";

    /// @brief Set the console being booted
    inline void SetSlug(const std::string& slug) {
        if (!slug.empty())
            CURRENT_SLUG = slug;
    }

    /// Content directories, with a trailing slash. Tico's per-module Paths tab
    /// stores custom roots as tico_{system,saves,states}_path in bluemsx.jsonc;
    /// empty or missing keys fall back to sdmc:/tico/<kind>/. Like tico's own
    /// {saves}/{states}/{system}, the console slug is appended to the root.
    std::string SystemPath();
    std::string SavesPath();
    std::string StatesPath();

    /// Create a directory and any missing parents.
    void MakeDirs(const std::string& path);

    /// @brief RetroAchievements console ID of the console being booted; 0
    /// for the Spectravideo, which has none there
    inline int GetRcConsoleId() {
        if (CURRENT_SLUG == "colecovision")
            return 44; // RC_CONSOLE_COLECOVISION
        if (CURRENT_SLUG == "sc-3000")
            return 33; // RC_CONSOLE_SG1000, which holds the SC-3000's games
        if (CURRENT_SLUG == "spectravideo")
            return 0;
        return 29; // RC_CONSOLE_MSX
    }

    /// @brief The blueMSX machine (a Machine Type value) for a game of the
    /// console being booted, when Machine Type is Auto; "" leaves it to the
    /// core, which picks an MSX by the file's extension.
    inline std::string MachineFor(const std::string& gamePath) {
        if (CURRENT_SLUG == "colecovision")
            return "ColecoVision";
        if (CURRENT_SLUG == "spectravideo")
            return "SVI - Spectravideo SVI-328";
        if (CURRENT_SLUG == "sc-3000") {
            std::string ext = gamePath.substr(gamePath.find_last_of('.') + 1);
            std::transform(ext.begin(), ext.end(), ext.begin(),
                           [](unsigned char c) { return (char)std::tolower(c); });
            // SF-7000 disks and their extensions; cartridges go in an SC-3000
            return ext == "sf" || ext == "sf7" ? "SEGA - SF-7000" : "SEGA - SC-3000";
        }
        return std::string();
    }

    constexpr int WINDOW_WIDTH = 1280;
    constexpr int WINDOW_HEIGHT = 720;
    constexpr float FONT_SIZE = 32.0f;

    /// @brief Use callback/ring-buffer path (supports resampling)
    constexpr bool USE_SDLQUEUEAUDIO = false;
}

/// @brief UI action identifiers for the helpers bar
enum UIActions {
    ACTION_CONFIRM,
    ACTION_BACK,
    ACTION_DETAILS,
    ACTION_MENU,
    ACTION_EDIT,
    ACTION_DELETE
};
