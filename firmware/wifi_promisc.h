#pragma once
#ifdef FEATURE_WIFI_PROMISCUOUS

#include <esp_wifi.h>
#include "sig_match.h"
#include "detection_output.h"
#include "seen_cache.h"

// 2.4 GHz channel sequence to hop
static const uint8_t _PROMISC_CHANNELS_24[] = {1,2,3,4,5,6,7,8,9,10,11,12,13};
static const int     _PROMISC_CHANNELS_24_COUNT =
    sizeof(_PROMISC_CHANNELS_24) / sizeof(_PROMISC_CHANNELS_24[0]);

static int           _promisc_ch_idx  = 0;
static unsigned long _promisc_ch_ts   = 0;
static bool          _promisc_running = false;

// ── 802.11 helpers ────────────────────────────────────────────────────────────

static void _mac6_to_str(const uint8_t* b, char* out) {
    snprintf(out, 18, "%02x:%02x:%02x:%02x:%02x:%02x",
             b[0], b[1], b[2], b[3], b[4], b[5]);
}

// Walk IEs and write the SSID IE (id=0) into out[33].
// Returns true if a non-empty SSID was found.
static bool _extract_ssid(const uint8_t* ie, int ie_len, char* out) {
    const uint8_t* end = ie + ie_len;
    while (ie + 2 <= end) {
        uint8_t id  = ie[0];
        uint8_t len = ie[1];
        if (ie + 2 + len > end) break;
        if (id == 0 && len > 0) {
            int copy = (len < 32) ? len : 32;
            memcpy(out, &ie[2], copy);
            out[copy] = '\0';
            return true;
        }
        ie += 2 + len;
    }
    return false;
}

// ── Promiscuous callback ───────────────────────────────────────────────────────

static void IRAM_ATTR _promisc_cb(void* buf, wifi_promiscuous_pkt_type_t type) {
    if (type != WIFI_PKT_MGMT) return;

    auto* pkt    = reinterpret_cast<wifi_promiscuous_pkt_t*>(buf);
    int   rssi   = pkt->rx_ctrl.rssi;
    int   pktlen = pkt->rx_ctrl.sig_len;
    const uint8_t* p = pkt->payload;

    if (pktlen < 24) return;

    uint8_t fc_type    = (p[0] >> 2) & 0x03;
    uint8_t fc_subtype = (p[0] >> 4) & 0x0F;
    if (fc_type != 0) return;  // management only

    // addr2 = transmitter MAC (bytes 10-15)
    char mac_str[18];
    _mac6_to_str(&p[10], mac_str);

    bool mac_hit  = sig_match_mac(mac_str);
    bool ssid_hit = false;
    char ssid[33] = {0};

    // Subtype 4 = probe request (IEs at byte 24, no fixed params)
    // Subtype 5 = probe response, 8 = beacon (IEs at byte 36, 12 B fixed params)
    int ie_offset = -1;
    if (fc_subtype == 4 && pktlen > 24)
        ie_offset = 24;
    else if ((fc_subtype == 5 || fc_subtype == 8) && pktlen > 36)
        ie_offset = 36;

    if (ie_offset > 0) {
        if (_extract_ssid(&p[ie_offset], pktlen - ie_offset, ssid))
            ssid_hit = sig_match_ssid(ssid);
    }

    if (!mac_hit && !ssid_hit) return;
    if (seen_cache_suppress(mac_str)) return;

    const char* method = ssid_hit ? "ssid_match" : "mac_prefix";
    emit_detection(
        mac_str, "wifi", method, rssi,
        ssid[0] ? ssid : nullptr, nullptr,
        calc_threat_score(method, rssi)
    );
}

// ── Public API ────────────────────────────────────────────────────────────────

void wifi_promisc_init() {
    // WiFi must already be in STA or NULL mode
    esp_wifi_set_promiscuous(false);

    wifi_promiscuous_filter_t filter = {.filter_mask = WIFI_PROMIS_FILTER_MASK_MGMT};
    esp_wifi_set_promiscuous_filter(&filter);
    esp_wifi_set_promiscuous_rx_cb(_promisc_cb);
}

void wifi_promisc_pause() {
    if (_promisc_running) esp_wifi_set_promiscuous(false);
}

void wifi_promisc_resume() {
    if (_promisc_running) {
        esp_wifi_set_channel(_PROMISC_CHANNELS_24[_promisc_ch_idx], WIFI_SECOND_CHAN_NONE);
        esp_wifi_set_promiscuous(true);
    }
}

void wifi_promisc_start() {
    _promisc_running = true;
    _promisc_ch_idx  = 0;
    _promisc_ch_ts   = millis();
    esp_wifi_set_channel(_PROMISC_CHANNELS_24[0], WIFI_SECOND_CHAN_NONE);
    esp_wifi_set_promiscuous(true);
}

// Call every loop iteration. Handles channel hopping based on wall clock.
void wifi_promisc_update() {
    if (!_promisc_running) return;

    unsigned long now = millis();
    if (now - _promisc_ch_ts < CHANNEL_HOP_INTERVAL_MS) return;

    _promisc_ch_ts = now;
    _promisc_ch_idx = (_promisc_ch_idx + 1) % _PROMISC_CHANNELS_24_COUNT;
    esp_wifi_set_channel(_PROMISC_CHANNELS_24[_promisc_ch_idx], WIFI_SECOND_CHAN_NONE);

#if BOARD_HAS_5GHZ
    // Interleave 5 GHz channels from wifi_signatures.h
    static int _5g_turn = 0;
    _5g_turn++;
    if (_5g_turn % 3 == 0) {
        static int _5g_idx = 0;
        esp_wifi_set_channel(WIFI_CHANNELS_5GHZ[_5g_idx], WIFI_SECOND_CHAN_NONE);
        _5g_idx = (_5g_idx + 1) % WIFI_CHANNELS_5GHZ_COUNT;
    }
#endif
}

#endif // FEATURE_WIFI_PROMISCUOUS
