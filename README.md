# Protect Snapshots

Exposes recent UniFi Protect person and face detection thumbnails as Home Assistant `image` entities, so they can be shown on dashboards (the thumbnails need HA auth, which plain picture cards can't do — `image` entities get signed URLs automatically).

## What it creates

Four `image` entities per configured camera feed:

- Latest person detection
- Previous person detection
- Latest face detection
- Previous face detection

The integration watches the camera's smart detection event entity from the official UniFi Protect integration. When a person or face is detected, it fetches the zoomed detection thumbnail via the Protect API and rotates it into the slots.

## Requirements

- The official [UniFi Protect](https://www.home-assistant.io/integrations/unifiprotect/) integration, set up and working.

## Install

1. In HACS, add `https://github.com/dabido3/protect-snapshots` as a custom **Integration** repository.
2. Install **Protect Snapshots** and restart Home Assistant.
3. Go to Settings → Devices & Services → Add Integration → Protect Snapshots.
4. Pick your UniFi Protect instance, then pick the camera's smart detection event entity (e.g. `event.g6_instant_smart_detection`).

## Dashboard

Add four `picture-entity` cards (or one `grid`/`horizontal-stack` of them) pointing at the image entities, under your camera card.
