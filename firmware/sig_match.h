#pragma once
#include "wifi_signatures.h"
#include "ble_signatures.h"

// Returns true if mac ("xx:xx:xx:xx:xx:xx") starts with any prefix in list.
static bool _prefix_match(const char* mac, const char** list, int count) {
    for (int i = 0; i < count; i++) {
        if (strncasecmp(mac, list[i], 8) == 0) return true;
    }
    return false;
}

// Check mac against all known MAC prefix lists.
static bool sig_match_mac(const char* mac) {
    return _prefix_match(mac, FS_WIFI_MAC_PREFIXES, FS_WIFI_MAC_PREFIX_COUNT)
        || _prefix_match(mac, FS_EXT_MAC_PREFIXES,  FS_EXT_MAC_PREFIX_COUNT)
        || _prefix_match(mac, PENGUIN_MAC_PREFIXES,  PENGUIN_MAC_PREFIX_COUNT);
}

// Case-insensitive substring match against SSID_PATTERNS.
static bool sig_match_ssid(const char* ssid) {
    if (!ssid || !*ssid) return false;
    for (int i = 0; i < SSID_PATTERN_COUNT; i++) {
        if (strcasestr(ssid, SSID_PATTERNS[i])) return true;
    }
    return false;
}

// Case-insensitive substring match against BLE_NAME_PATTERNS.
static bool sig_match_ble_name(const char* name) {
    if (!name || !*name) return false;
    for (int i = 0; i < BLE_NAME_PATTERN_COUNT; i++) {
        if (strcasestr(name, BLE_NAME_PATTERNS[i])) return true;
    }
    return false;
}
