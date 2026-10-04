"""Config flow for Protect Snapshots."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers import entity_registry as er

from .const import CONF_EVENT_ENTITY_ID, CONF_PROTECT_ENTRY_ID, DOMAIN


class ProtectSnapshotsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Protect Snapshots."""

    VERSION = 1

    def __init__(self) -> None:
        self._protect_entry_id: str | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial step: pick the UniFi Protect config entry."""
        entries = self.hass.config_entries.async_entries("unifiprotect")
        if not entries:
            return self.async_abort(reason="no_protect")

        if user_input is not None:
            self._protect_entry_id = user_input[CONF_PROTECT_ENTRY_ID]
            return await self.async_step_select()

        if len(entries) == 1:
            self._protect_entry_id = entries[0].entry_id
            return await self.async_step_select()

        schema = vol.Schema(
            {
                vol.Required(CONF_PROTECT_ENTRY_ID): vol.In(
                    {e.entry_id: e.title for e in entries}
                )
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema)

    async def async_step_select(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Pick the smart detection event entity to watch."""
        assert self._protect_entry_id is not None
        registry = er.async_get(self.hass)
        candidates = {
            e.entity_id: (e.original_name or e.name or e.entity_id)
            for e in registry.entities.values()
            if e.platform == "unifiprotect"
            and e.domain == "event"
            and e.config_entry_id == self._protect_entry_id
            and "smart_detection" in (e.entity_id or "")
        }
        if not candidates:
            return self.async_abort(reason="no_smart_detection_events")

        if user_input is not None:
            event_entity_id = user_input[CONF_EVENT_ENTITY_ID]
            await self.async_set_unique_id(
                f"{DOMAIN}_{self._protect_entry_id}_{event_entity_id}"
            )
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=f"Protect Snapshots ({candidates[event_entity_id]})",
                data={
                    CONF_PROTECT_ENTRY_ID: self._protect_entry_id,
                    CONF_EVENT_ENTITY_ID: event_entity_id,
                },
            )

        schema = vol.Schema(
            {vol.Required(CONF_EVENT_ENTITY_ID): vol.In(candidates)}
        )
        return self.async_show_form(step_id="select", data_schema=schema)
