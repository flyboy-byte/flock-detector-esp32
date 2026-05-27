#pragma once

// ----------------------------------------------------------------------------
// BLE detection signatures
//
// Sources:
//   references/flock-you/src/main.cpp, GainSec Bluetooth surveillance research
//
// Name patterns matched case-insensitively as substrings.
// MAC prefix matching reuses the lists in wifi_signatures.h.
// ----------------------------------------------------------------------------

static const char* BLE_NAME_PATTERNS[] = {
    "FS Ext Battery",
    "Flock",
    "Penguin",
    "Pigvision",
};
static const int BLE_NAME_PATTERN_COUNT =
    sizeof(BLE_NAME_PATTERNS) / sizeof(BLE_NAME_PATTERNS[0]);
