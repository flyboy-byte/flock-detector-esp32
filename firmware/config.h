#pragma once

// ----------------------------------------------------------------------------
// Identity
// ----------------------------------------------------------------------------
#define FW_PROJECT_NAME  "flock-detector-esp32"
#define FW_VERSION       "0.1.0-dev"

// ----------------------------------------------------------------------------
// Board-specific defaults
// PlatformIO injects BOARD_BUZZER_PIN, BOARD_HAS_5GHZ, BOARD_HAS_PSRAM
// via build_flags. Arduino IDE users set them here manually.
// ----------------------------------------------------------------------------
#ifndef BOARD_BUZZER_PIN
    #define BOARD_BUZZER_PIN 25   // Safe default for WROOM/WROVER dev boards
#endif

#ifndef BOARD_HAS_5GHZ
    #define BOARD_HAS_5GHZ 0      // Original ESP32 is 2.4GHz only
#endif

#ifndef BOARD_HAS_PSRAM
    #define BOARD_HAS_PSRAM 0
#endif

// Derive a human-readable board name for the boot message
#if defined(ARDUINO_XIAO_ESP32S3)
    #define FW_TARGET_BOARD "Xiao ESP32 S3"
#elif defined(ARDUINO_ESP32_DEV) && BOARD_HAS_PSRAM
    #define FW_TARGET_BOARD "ESP32-WROVER"
#elif defined(ARDUINO_ESP32_DEV)
    #define FW_TARGET_BOARD "ESP32-WROOM"
#else
    #define FW_TARGET_BOARD "ESP32 (unknown variant)"
#endif

// ----------------------------------------------------------------------------
// Feature flags — comment out to disable at compile time
// ----------------------------------------------------------------------------
#define FEATURE_WIFI_SCAN             // Active WiFi scan (Milestone 4)
#define FEATURE_WIFI_PROMISCUOUS      // Raw 802.11 frame capture (Milestone 6)
#define FEATURE_BLE_SCAN              // BLE advertisement scan (Milestone 7)
// #define FEATURE_BUZZER             // Audio alerts via piezo buzzer

// ----------------------------------------------------------------------------
// WiFi
// ----------------------------------------------------------------------------
#define WIFI_SCAN_INTERVAL_MS    5000   // Time between active scan cycles
#define CHANNEL_HOP_INTERVAL_MS  2500   // Promiscuous mode channel dwell time

// ----------------------------------------------------------------------------
// BLE
// ----------------------------------------------------------------------------
#define BLE_SCAN_DURATION_S  1    // Scan window per loop iteration
#define BLE_SCAN_INTERVAL    100  // ms
#define BLE_SCAN_WINDOW      99   // ms

// ----------------------------------------------------------------------------
// Serial
// ----------------------------------------------------------------------------
#define SERIAL_BAUD 115200
