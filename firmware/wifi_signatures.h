#pragma once

// ----------------------------------------------------------------------------
// WiFi detection signatures
//
// Sources:
//   deflock.me crowdsourced database, references/flock-you/src/main.cpp
//
// MAC prefixes: first 3 octets, lowercase "xx:xx:xx" format.
// SSID patterns: matched case-insensitively as substrings.
// ----------------------------------------------------------------------------

static const char* FS_WIFI_MAC_PREFIXES[] = {
    "70:c9:4e", "3c:91:80", "d8:f3:bc", "80:30:49",
    "14:5a:fc", "74:4c:a1", "08:3a:88", "9c:2f:9d",
};
static const int FS_WIFI_MAC_PREFIX_COUNT =
    sizeof(FS_WIFI_MAC_PREFIXES) / sizeof(FS_WIFI_MAC_PREFIXES[0]);

static const char* FS_EXT_MAC_PREFIXES[] = {
    "58:8e:81", "ec:1b:bd", "90:35:ea", "04:0d:84",
    "f0:82:c0", "1c:34:f1", "38:5b:44", "94:34:69", "b4:e3:f9",
    // "cc:cc:cc" excluded — not a real OUI
};
static const int FS_EXT_MAC_PREFIX_COUNT =
    sizeof(FS_EXT_MAC_PREFIXES) / sizeof(FS_EXT_MAC_PREFIXES[0]);

static const char* PENGUIN_MAC_PREFIXES[] = {
    "cc:09:24", "ed:c7:63", "e8:ce:56", "ea:0c:ea", "d8:8f:14",
    "f9:d9:c0", "f1:32:f9", "f6:a0:76", "e4:1c:9e", "e7:f2:43",
    "e2:71:33", "da:91:a9", "e1:0e:15", "c8:ae:87", "f4:ed:b2",
    "d8:bf:b5", "ee:8f:3c", "d7:2b:21", "ea:5a:98",
};
static const int PENGUIN_MAC_PREFIX_COUNT =
    sizeof(PENGUIN_MAC_PREFIXES) / sizeof(PENGUIN_MAC_PREFIXES[0]);

// Collapsed from flock-you's redundant flock/Flock/FLOCK — one case-insensitive match covers all.
static const char* SSID_PATTERNS[] = {
    "flock",
    "FS Ext Battery",
    "Penguin",
    "Pigvision",
};
static const int SSID_PATTERN_COUNT =
    sizeof(SSID_PATTERNS) / sizeof(SSID_PATTERNS[0]);

// 5 GHz channels (from sniffer reference — not in flock-you)
static const uint8_t WIFI_CHANNELS_5GHZ[] = {
    36, 40, 44, 48, 149, 153, 157, 161, 165
};
static const int WIFI_CHANNELS_5GHZ_COUNT =
    sizeof(WIFI_CHANNELS_5GHZ) / sizeof(WIFI_CHANNELS_5GHZ[0]);
