"""CL Irrigation integration."""
from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.components.lovelace.const import LOVELACE_DATA
from homeassistant.components.lovelace.resources import ResourceStorageCollection
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, FRONTEND_FILENAME, FRONTEND_URL, PLATFORMS
from .controller import CLIrrigationController

_LOGGER = logging.getLogger(__name__)
_FRONTEND_VERSION = "0.2.6"


async def _async_register_dashboard_resource(hass: HomeAssistant) -> None:
    """Register the CL Irrigation dashboard strategy as a Lovelace module resource.

    Home Assistant 2026.5+ only discovers Community dashboard strategies after
    their frontend module has been loaded as a Lovelace resource. In storage
    mode we therefore create/update the resource through Home Assistant's
    Lovelace resource collection. YAML resource mode falls back to the global
    extra-JS loader so the strategy can still be used manually.
    """
    resource_url = f"{FRONTEND_URL}?v={_FRONTEND_VERSION}"
    lovelace_data = hass.data.get(LOVELACE_DATA)

    if lovelace_data is None:
        _LOGGER.warning(
            "Lovelace data is not available; loading CL Irrigation dashboard "
            "strategy through the frontend fallback"
        )
        add_extra_js_url(hass, resource_url)
        return

    resources = lovelace_data.resources

    if not isinstance(resources, ResourceStorageCollection):
        add_extra_js_url(hass, resource_url)
        _LOGGER.info(
            "CL Irrigation dashboard strategy loaded through frontend fallback "
            "because Lovelace resources are not in storage mode"
        )
        return

    await resources.async_get_info()

    existing = None
    for item in resources.async_items():
        url = item.get("url", "")
        if url.split("?", 1)[0] == FRONTEND_URL:
            existing = item
            break

    if existing is None:
        await resources.async_create_item(
            {"res_type": "module", "url": resource_url}
        )
        _LOGGER.info("Registered CL Irrigation dashboard resource: %s", resource_url)
        return

    if (
        existing.get("url") != resource_url
        or existing.get("res_type") != "module"
    ):
        await resources.async_update_item(
            existing["id"], {"res_type": "module", "url": resource_url}
        )
        _LOGGER.info("Updated CL Irrigation dashboard resource: %s", resource_url)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up CL Irrigation and register its dashboard frontend module."""
    component_dir = Path(__file__).parent
    frontend_file = component_dir / "frontend" / FRONTEND_FILENAME
    brand_logo = component_dir / "brand" / "logo.png"
    if frontend_file.exists():
        static_paths = [
            StaticPathConfig(FRONTEND_URL, str(frontend_file), cache_headers=False)
        ]
        if brand_logo.exists():
            static_paths.append(
                StaticPathConfig(
                    "/cl_irrigation/brand/logo.png",
                    str(brand_logo),
                    cache_headers=True,
                )
            )
        await hass.http.async_register_static_paths(static_paths)
        await _async_register_dashboard_resource(hass)
    else:
        _LOGGER.error("CL Irrigation dashboard frontend file is missing: %s", frontend_file)

    return True


async def _async_entry_updated(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Apply options-flow changes without a full integration reload."""
    controller: CLIrrigationController = entry.runtime_data
    await controller.async_options_updated()


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a CL Irrigation config entry."""
    controller = CLIrrigationController(hass, entry)
    entry.runtime_data = controller
    entry.async_on_unload(entry.add_update_listener(_async_entry_updated))
    await controller.async_start()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a CL Irrigation config entry."""
    controller: CLIrrigationController = entry.runtime_data
    await controller.async_stop()
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
