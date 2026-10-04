"""Image platform for Protect Snapshots."""
from __future__ import annotations

from homeassistant.components.image import Image
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_EVENT_ENTITY_ID, DOMAIN, SLOTS

SLOT_NAMES = {
    "person_1": "Latest person detection",
    "person_2": "Previous person detection",
    "face_1": "Latest face detection",
    "face_2": "Previous face detection",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the image entities."""
    state = hass.data[DOMAIN][entry.entry_id]
    event_entity_id: str = entry.data[CONF_EVENT_ENTITY_ID]
    camera_slug = event_entity_id.replace("event.", "").replace("_smart_detection", "")

    entities = [
        ProtectSnapshotImage(entry.entry_id, slot, camera_slug) for slot in SLOTS
    ]
    for entity in entities:
        state["entities"][entity.unique_id] = entity
    async_add_entities(entities)


class ProtectSnapshotImage(Image):
    """Image entity serving the latest cached Protect detection thumbnail."""

    _attr_has_entity_name = True

    def __init__(self, entry_id: str, slot: str, camera_slug: str) -> None:
        # content_type/content are required by Image.__init__; actual bytes
        # come from async_image() below.
        super().__init__("image/jpeg", b"")
        self._entry_id = entry_id
        self._slot = slot
        self._attr_unique_id = f"{DOMAIN}_{camera_slug}_{slot}"
        self._attr_name = SLOT_NAMES[slot]
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, camera_slug)},
            name=f"Protect Snapshots ({camera_slug.replace('_', ' ').title()})",
            manufacturer="UniFi Protect",
        )
        self._attr_entity_picture = None

    async def async_image(self) -> bytes | None:
        """Return the cached thumbnail bytes."""
        state = self.hass.data[DOMAIN][self._entry_id]
        return state["slots"].get(self._slot)
