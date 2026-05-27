#pragma once
#include <Arduino.h>
#include <ArduinoJson.h>

// Emit one detection JSON line to Serial.
// All callers share this so the output format stays identical.
static void emit_detection(
    const char* mac,
    const char* protocol,
    const char* method,
    int rssi,
    const char* ssid,        // may be nullptr
    const char* device_name, // may be nullptr
    int threat_score
) {
    DynamicJsonDocument doc(256);
    doc["mac_address"]       = mac;
    doc["protocol"]          = protocol;
    doc["detection_method"]  = method;
    doc["rssi"]              = rssi;
    doc["device_category"]   = "FLOCK_SAFETY";
    doc["threat_score"]      = threat_score;
    doc["timestamp"]         = millis();
    if (ssid && *ssid)        doc["ssid"]        = ssid;
    if (device_name && *device_name) doc["device_name"] = device_name;

    serializeJson(doc, Serial);
    Serial.println();
}

// Score based on match quality and RSSI strength.
static int calc_threat_score(const char* method, int rssi) {
    int base = 70;
    if (strcmp(method, "ssid_match") == 0 || strcmp(method, "ble_name") == 0)
        base = 100;
    else if (strcmp(method, "mac_prefix") == 0 || strcmp(method, "ble_mac") == 0)
        base = 85;
    // Boost slightly for strong signal — still caps at 100
    if (rssi > -60) base = (base < 100) ? base + 5 : 100;
    return base;
}
