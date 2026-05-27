#pragma once
#include <Arduino.h>

// Suppress duplicate detections for the same MAC within a rolling window.
// Shared across wifi_scan, wifi_promisc, and ble_scan.

#define SEEN_CACHE_SIZE   64
#define SEEN_CACHE_TTL_MS 30000  // 30 s cooldown before re-emitting same MAC

struct _SeenEntry {
    char mac[18];
    unsigned long ts;
};

static _SeenEntry _seen_cache[SEEN_CACHE_SIZE];
static int _seen_next = 0;

// Returns true  → suppress (already emitted within TTL).
// Returns false → emit and record.
static bool seen_cache_suppress(const char* mac) {
    unsigned long now = millis();

    for (int i = 0; i < SEEN_CACHE_SIZE; i++) {
        if (_seen_cache[i].mac[0] && strcasecmp(_seen_cache[i].mac, mac) == 0) {
            if (now - _seen_cache[i].ts < SEEN_CACHE_TTL_MS) return true;
            _seen_cache[i].ts = now;
            return false;
        }
    }

    // New entry — ring buffer
    strncpy(_seen_cache[_seen_next].mac, mac, 17);
    _seen_cache[_seen_next].mac[17] = '\0';
    _seen_cache[_seen_next].ts      = now;
    _seen_next = (_seen_next + 1) % SEEN_CACHE_SIZE;
    return false;
}
