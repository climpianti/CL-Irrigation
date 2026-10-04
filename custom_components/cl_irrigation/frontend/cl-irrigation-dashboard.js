const DOMAIN = "cl_irrigation";
const STRATEGY = "cl-irrigation";


function clControlHomePath(hass) {
  const panels = hass?.panels || {};
  for (const [path, panel] of Object.entries(panels)) {
    if (panel?.component_name !== "lovelace") continue;
    const title = String(panel?.title || "").trim().toLowerCase();
    if (path === "cl-control" || title === "cl control") {
      return `/${String(path).replace(/^\/+|\/+$/g, "")}/home`;
    }
  }
  return "";
}

function brandSection(hass) {
  const homePath = clControlHomePath(hass);
  const card = {
    type: "markdown",
    content:
      '<table role="presentation" width="100%"><tr>' +
      '<td width="70" valign="middle"><img src="/cl_irrigation/brand/logo.png" width="54"></td>' +
      '<td valign="middle"><span style="font-size:20px"><b>CL Irrigation</b></span><br>' +
      '<span style="font-size:13px">Irrigazione intelligente</span></td>' +
      "</tr></table>",
    grid_options: { columns: "full", rows: 2 },
  };
  if (homePath) {
    card.tap_action = { action: "navigate", navigation_path: homePath };
    card.hold_action = { action: "none" };
  }
  return {
    type: "grid",
    column_span: 4,
    cards: [card],
  };
}

function entityName(hass, entityId, fallback) {
  const state = entityId ? hass.states[entityId] : undefined;
  return state?.attributes?.friendly_name || fallback;
}

function stripDevicePrefix(name, controllerName) {
  if (!name) return name;
  const prefix = `${controllerName} `;
  return name.startsWith(prefix) ? name.slice(prefix.length) : name;
}

function tile(entity, name, icon, extra = {}) {
  if (!entity) return null;
  return { type: "tile", entity, name, icon, ...extra };
}

function buttonCard(entity, name, icon, confirmation) {
  if (!entity) return null;
  const tap_action = {
    action: "perform-action",
    perform_action: "button.press",
    target: { entity_id: entity },
  };
  if (confirmation) tap_action.confirmation = { text: confirmation };
  return {
    type: "button",
    entity,
    name,
    icon,
    show_state: false,
    tap_action,
  };
}

function compact(items) {
  return items.filter(Boolean);
}

function heading(text, icon, style = "title") {
  return { type: "heading", heading: text, heading_style: style, icon };
}

function entityRow(entity, name, icon) {
  if (!entity) return null;
  return { entity, name, ...(icon ? { icon } : {}) };
}

function entitiesCard(title, rows, icon) {
  return {
    type: "entities",
    title,
    show_header_toggle: false,
    state_color: true,
    ...(icon ? { icon } : {}),
    entities: compact(rows),
  };
}

async function discoverControllers(hass) {
  const [entities, devices] = await Promise.all([
    hass.callWS({ type: "config/entity_registry/list" }),
    hass.callWS({ type: "config/device_registry/list" }),
  ]);

  const groups = new Map();
  for (const entity of entities) {
    if (entity.platform !== DOMAIN || !entity.config_entry_id) continue;
    if (!groups.has(entity.config_entry_id)) groups.set(entity.config_entry_id, []);
    groups.get(entity.config_entry_id).push(entity);
  }

  return [...groups.entries()].map(([entryId, entryEntities]) => {
    const map = {};
    const prefix = `${entryId}_`;
    for (const entity of entryEntities) {
      const unique = entity.unique_id || "";
      const key = unique.startsWith(prefix) ? unique.slice(prefix.length) : unique;
      map[key] = entity.entity_id;
    }
    const device = devices.find(
      (d) => Array.isArray(d.config_entries) && d.config_entries.includes(entryId)
    );
    const name = device?.name_by_user || device?.name || "CL Irrigation";
    return { entryId, name, entities: map };
  });
}

function zoneIndexes(entities) {
  return Object.keys(entities)
    .map((key) => key.match(/^zone_(\d+)_enabled$/))
    .filter(Boolean)
    .map((match) => Number(match[1]))
    .sort((a, b) => a - b);
}

function zoneName(hass, controller, index) {
  const enabled = controller.entities[`zone_${index}_enabled`];
  const state = enabled ? hass.states[enabled] : undefined;
  const attrName = state?.attributes?.zone_name;
  if (attrName) return attrName;
  let name = entityName(hass, enabled, `Zona ${index}`);
  name = stripDevicePrefix(name, controller.name);
  return name.replace(/\s+inclusa$/i, "");
}

function centralView(hass, controller, suffix) {
  const e = controller.entities;
  const zones = zoneIndexes(e);

  const overviewSection = {
    type: "grid",
    cards: compact([
      heading("Stato generale", "mdi:sprinkler-variant"),
      tile(e.automatic, "Automatico", "mdi:auto-mode", {
        features: [{ type: "toggle" }],
      }),
      tile(e.allowed, "Consentita", "mdi:check-circle-outline"),
      tile(e.status, "Stato sistema", "mdi:text-box-outline"),
      tile(e.next_start, "Prossimo avvio", "mdi:clock-start"),
      tile(e.current_zone, "Zona attiva", "mdi:sprinkler"),
      tile(e.planned_total_duration, "Durata prevista", "mdi:timer-outline"),
    ]),
  };

  const manualSection = {
    type: "grid",
    cards: compact([
      heading("Comandi", "mdi:gesture-tap-button"),
      buttonCard(e.start, "Avvia ciclo", "mdi:play-circle"),
      buttonCard(
        e.stop,
        "STOP",
        "mdi:stop-circle",
        "Interrompere il ciclo e chiudere tutte le valvole?"
      ),
      tile(e.running, "Ciclo", "mdi:sprinkler-variant"),
      tile(e.remaining_time, "Tempo rimanente", "mdi:timer-sand"),
    ]),
  };

  const scheduleSections = [];
  for (let i = 1; i <= 4; i += 1) {
    scheduleSections.push({
      type: "grid",
      cards: [
        heading(`Programma ${i}`, "mdi:calendar-clock"),
        entitiesCard(
          `Programma ${i}`,
          [
            entityRow(e[`schedule_${i}_enabled`], "Abilitato", "mdi:toggle-switch"),
            entityRow(e[`schedule_${i}_time`], "Orario avvio", "mdi:clock-outline"),
          ],
          "mdi:calendar-clock"
        ),
      ],
    });
  }

  const zoneSections = [];
  for (const i of zones) {
    const enabled = e[`zone_${i}_enabled`];
    const baseDuration = e[`zone_${i}_duration`];
    const calculated = e[`zone_${i}_calculated_duration`];
    const name = zoneName(hass, controller, i);
    const valve = enabled ? hass.states[enabled]?.attributes?.valve_entity : undefined;

    zoneSections.push({
      type: "grid",
      cards: [
        heading(name, "mdi:sprinkler"),
        entitiesCard(
          name,
          [
            entityRow(enabled, "Includi zona", "mdi:toggle-switch"),
            entityRow(baseDuration, "Durata base", "mdi:timer-outline"),
            entityRow(calculated, "Durata calcolata", "mdi:timer-check-outline"),
            valve ? entityRow(valve, "Stato valvola", "mdi:valve") : null,
          ],
          "mdi:sprinkler"
        ),
      ],
    });
  }

  return {
    type: "sections",
    title: controller.name,
    path: suffix ? `${suffix}-centralina` : "centralina",
    icon: "mdi:sprinkler-variant",
    max_columns: 4,
    sections: [
      brandSection(hass),
      overviewSection,
      manualSection,
      ...scheduleSections,
      ...zoneSections,
    ],
  };
}

function statusView(hass, controller, suffix) {
  const e = controller.entities;
  const zones = zoneIndexes(e);

  const systemRows = compact([
    entityRow(e.status, "Stato sistema", "mdi:text-box-outline"),
    entityRow(e.allowed, "Irrigazione consentita", "mdi:check-circle-outline"),
    entityRow(e.running, "Ciclo in esecuzione", "mdi:sprinkler-variant"),
    entityRow(e.current_zone, "Zona attiva", "mdi:sprinkler"),
    entityRow(e.remaining_time, "Tempo rimanente", "mdi:timer-sand"),
    entityRow(e.next_start, "Prossimo avvio", "mdi:clock-start"),
    entityRow(e.last_cycle, "Ultimo ciclo", "mdi:history"),
    entityRow(e.planned_total_duration, "Durata totale prevista", "mdi:timer-outline"),
  ]);

  const sections = [
    brandSection(hass),
    {
      type: "grid",
      cards: [
        heading("Stato sistema", "mdi:information-outline"),
        { type: "entities", show_header_toggle: false, state_color: true, entities: systemRows },
      ],
    },
    {
      type: "grid",
      cards: compact([
        heading("Meteo", "mdi:weather-partly-rainy"),
        tile(e.rain_tomorrow, "Pioggia domani", "mdi:weather-rainy"),
        tile(e.temperature_tomorrow, "Temperatura domani", "mdi:thermometer"),
        buttonCard(e.refresh_weather, "Aggiorna meteo", "mdi:weather-cloudy-clock"),
      ]),
    },
  ];

  for (const i of zones) {
    const enabled = e[`zone_${i}_enabled`];
    const valve = enabled ? hass.states[enabled]?.attributes?.valve_entity : undefined;
    const name = zoneName(hass, controller, i);
    sections.push({
      type: "grid",
      cards: [
        heading(name, "mdi:water-percent"),
        entitiesCard(
          name,
          [
            entityRow(e[`zone_${i}_humidity`], "Umidità terreno", "mdi:water-percent"),
            entityRow(e[`zone_${i}_factor`], "Fattore durata", "mdi:tune"),
            entityRow(e[`zone_${i}_calculated_duration`], "Durata calcolata", "mdi:timer-check-outline"),
            valve ? entityRow(valve, "Valvola", "mdi:valve") : null,
          ],
          "mdi:water-percent"
        ),
      ],
    });
  }

  return {
    type: "sections",
    title: "Stato",
    path: suffix ? `${suffix}-stato` : "stato",
    icon: "mdi:information-outline",
    max_columns: 4,
    sections,
  };
}

function settingsView(hass, controller, suffix) {
  const e = controller.entities;
  const zones = zoneIndexes(e);

  const thresholdCards = compact([
    tile(e.rain_threshold, "Soglia pioggia", "mdi:weather-rainy", {
      features: [{ type: "numeric-input", style: "buttons" }],
    }),
    tile(e.humidity_block, "Blocco umidità", "mdi:water-off", {
      features: [{ type: "numeric-input", style: "buttons" }],
    }),
    tile(e.humidity_dry, "Terreno secco", "mdi:water-minus", {
      features: [{ type: "numeric-input", style: "buttons" }],
    }),
    tile(e.humidity_very_dry, "Molto secco", "mdi:water-alert", {
      features: [{ type: "numeric-input", style: "buttons" }],
    }),
  ]);

  const factorCards = compact([
    tile(e.factor_normal, "Fattore normale", "mdi:tune", {
      features: [{ type: "numeric-input", style: "buttons" }],
    }),
    tile(e.factor_dry, "Fattore secco", "mdi:tune", {
      features: [{ type: "numeric-input", style: "buttons" }],
    }),
    tile(e.factor_very_dry, "Fattore molto secco", "mdi:tune", {
      features: [{ type: "numeric-input", style: "buttons" }],
    }),
  ]);

  const pumpCards = compact([
    tile(e.pump_on_delay, "Ritardo accensione pompa", "mdi:pump", {
      features: [{ type: "numeric-input", style: "buttons" }],
    }),
    tile(e.pump_off_delay, "Ritardo spegnimento pompa", "mdi:pump-off", {
      features: [{ type: "numeric-input", style: "buttons" }],
    }),
    tile(e.manual_respects_conditions, "Manuale protetto", "mdi:shield-check-outline", {
      features: [{ type: "toggle" }],
    }),
  ]);

  const durationCards = [];
  for (const i of zones) {
    durationCards.push(
      tile(e[`zone_${i}_duration`], zoneName(hass, controller, i), "mdi:timer-outline", {
        features: [{ type: "numeric-input", style: "buttons" }],
      })
    );
  }

  return {
    type: "sections",
    title: "Impostazioni",
    path: suffix ? `${suffix}-impostazioni` : "impostazioni",
    icon: "mdi:cog-outline",
    max_columns: 4,
    sections: [
      brandSection(hass),
      {
        type: "grid",
        cards: [
          heading("Meteo e soglie umidità", "mdi:water-thermometer-outline"),
          ...thresholdCards,
        ],
      },
      {
        type: "grid",
        cards: [heading("Fattori durata", "mdi:tune-variant"), ...factorCards],
      },
      {
        type: "grid",
        cards: [heading("Pompa e avvio manuale", "mdi:pump"), ...pumpCards],
      },
      {
        type: "grid",
        cards: [heading("Durate base zone", "mdi:timer-outline"), ...compact(durationCards)],
      },
    ],
  };
}

function historyView(hass, controller, suffix) {
  const e = controller.entities;
  const zones = zoneIndexes(e);

  const humidityEntities = compact(
    zones.map((i) => {
      const entity = e[`zone_${i}_humidity`];
      if (!entity) return null;
      return { entity, name: zoneName(hass, controller, i) };
    })
  );

  const activityEntities = compact([
    e.running ? { entity: e.running, name: "Ciclo irrigazione" } : null,
    ...zones.map((i) => {
      const enabled = e[`zone_${i}_enabled`];
      const valve = enabled ? hass.states[enabled]?.attributes?.valve_entity : undefined;
      if (!valve) return null;
      return { entity: valve, name: zoneName(hass, controller, i) };
    }),
  ]);

  const sections = [
    brandSection(hass),
    {
      type: "grid",
      cards: compact([
        heading("Riepilogo", "mdi:history"),
        tile(e.last_cycle, "Ultimo ciclo", "mdi:history"),
        tile(e.planned_total_duration, "Durata prevista", "mdi:timer-outline"),
        tile(e.next_start, "Prossimo avvio", "mdi:clock-start"),
      ]),
    },
  ];

  if (humidityEntities.length) {
    sections.push({
      type: "grid",
      cards: [
        heading("Umidità terreno - 7 giorni", "mdi:chart-line"),
        {
          type: "statistics-graph",
          title: "Andamento umidità",
          chart_type: "line",
          days_to_show: 7,
          period: "hour",
          stat_types: ["mean"],
          entities: humidityEntities,
        },
      ],
    });
  }

  if (activityEntities.length) {
    sections.push({
      type: "grid",
      cards: [
        heading("Attività irrigazione - 48 ore", "mdi:timeline-clock-outline"),
        {
          type: "history-graph",
          title: "Cicli e valvole",
          hours_to_show: 48,
          entities: activityEntities,
        },
      ],
    });
  }

  return {
    type: "sections",
    title: "Storico",
    path: suffix ? `${suffix}-storico` : "storico",
    icon: "mdi:chart-timeline-variant",
    max_columns: 4,
    sections,
  };
}

class CLIrrigationDashboardStrategy extends HTMLElement {
  static getCreateSuggestions(_hass) {
    return { title: "CL Irrigation", icon: "mdi:sprinkler-variant" };
  }

  static async generate(config, hass) {
    const controllers = await discoverControllers(hass);
    if (!controllers.length) {
      return {
        title: config.title || "CL Irrigation",
        views: [
          {
            title: "CL Irrigation",
            path: "cl-irrigation",
            cards: [
              {
                type: "markdown",
                content:
                  '<table role="presentation" width="100%"><tr>' +
                  '<td width="70" valign="middle"><img src="/cl_irrigation/brand/logo.png" width="54"></td>' +
                  '<td valign="middle"><span style="font-size:20px"><b>CL Irrigation</b></span><br>' +
                  '<span style="font-size:13px">Configura prima l\'integrazione in Impostazioni → Dispositivi e servizi</span></td>' +
                  "</tr></table>",
              },
            ],
          },
        ],
      };
    }

    const multiple = controllers.length > 1;
    const views = [];
    controllers.forEach((controller, idx) => {
      const suffix = multiple ? `impianto-${idx + 1}` : "";
      views.push(
        centralView(hass, controller, suffix),
        statusView(hass, controller, suffix),
        historyView(hass, controller, suffix),
        settingsView(hass, controller, suffix)
      );
    });
    return { title: config.title || "CL Irrigation", views };
  }
}

if (!customElements.get(`ll-strategy-dashboard-${STRATEGY}`)) {
  customElements.define(
    `ll-strategy-dashboard-${STRATEGY}`,
    CLIrrigationDashboardStrategy
  );
}

window.customStrategies = window.customStrategies || [];
if (
  !window.customStrategies.some(
    (item) => item.type === STRATEGY && item.strategyType === "dashboard"
  )
) {
  window.customStrategies.push({
    type: STRATEGY,
    strategyType: "dashboard",
    name: "CL Irrigation",
    description: "Centralina irrigazione dinamica per CL Irrigation.",
    documentationURL: "https://github.com/climpianti/CL-Irrigation",
  });
}
