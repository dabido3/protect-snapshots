"""Protect Snapshots integration: expose recent person/face detection thumbnails as image entities."""
from __future__ import annotations

import asyncio
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event

from .const import (
    CONF_EVENT_ENTITY_ID,
    CONF_PROTECT_ENTRY_ID,
    DOMAIN,
    SLOT_FACE_1,
    SLOT_FACE_2,
    SLOT_PERSON_1,
    SLOT_PERSON_2,
    SLOTS,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["image"]

_FETCH_RETRIES = 3
_FETCH_RETRY_DELAY = 5


async def _fetch_thumbnail(protect_data, event_id: str) -> bytes | None:
    """Fetch a thumbnail for a Protect event, retrying while it renders."""
    for attempt in range(_FETCH_RETRIES):
        try:
            thumbnail = await protect_data.api.get_event_thumbnail(event_id)
        except Exception as err:  # noqa: BLE001
            _LOGGER.debug("Thumbnail fetch failed (attempt %s): %s", attempt + 1, err)
            thumbnail = None
        if thumbnail:
            return thumbnail
        if attempt < _FETCH_RETRIES - 1:
            await asyncio.sleep(_FETCH_RETRY_DELAY)
    _LOGGER.warning("Could not fetch thumbnail for event %s", event_id)
    return None


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Protect Snapshots from a config entry."""
    from homeassistant.components.unifiprotect.data import async_get_data_for_entry_id

    protect_entry_id: str = entry.data[CONF_PROTECT_ENTRY_ID]
    event_entity_id: str = entry.data[CONF_EVENT_ENTITY_ID]

    protect_data = async_get_data_for_entry_id(hass, protect_entry_id)
    if protect_data is None:
        _LOGGER.error("UniFi Protect entry %s not loaded", protect_entry_id)
        return False

    state: dict = {
        "protect_data": protect_data,
        "event_entity_id": event_entity_id,
        "slots": {slot: None for slot in SLOTS},
        "entities": {},
    }
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = state

    @callback
    def _schedule_thumbnail(event_type: str, event_id: str) -> None:
        hass.async_create_task(_handle_detection(event_type, event_id))

    async def _handle_detection(event_type: str, event_id: str) -> None:
        thumbnail = await _fetch_thumbnail(state["protect_data"], event_id)
        if not thumbnail:
            return
        if event_type == "person":
            state["slots"][SLOT_PERSON_2] = state["slots"][SLOT_PERSON_1]
            state["slots"][SLOT_PERSON_1] = thumbnail
        elif event_type == "face":
            state["slots"][SLOT_FACE_2] = state["slots"][SLOT_FACE_1]
            state["slots"][SLOT_FACE_1] = thumbnail
        else:
            return
        for entity in state["entities"].values():
            entity.async_write_ha_state()

    @callback
    def _event_listener(event: Event) -> None:
        new_state = event.data.get("new_state")
        if new_state is None:
            return
        attrs = new_state.attributes
        event_id = attrs.get("event_id")
        if not event_id:
            return
        detected: str | None = None
        event_type = str(attrs.get("event_type") or "").lower()
        if event_type in ("person", "face"):
            detected = event_type
        else:
            smart_types = [
                str(t).lower() for t in (attrs.get("smart_detect_types") or [])
            ]
            if "face" in smart_types:
                detected = "face"
            elif "person" in smart_types:
                detected = "person"
        if detected:
            _schedule_thumbnail(detected, event_id)

    async_track_state_change_event(hass, [event_entity_id], _event_listener)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return unload_ok
