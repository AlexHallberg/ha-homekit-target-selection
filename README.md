# HomeKit Bridge – target selection (test build)

Home Assistant's built-in **HomeKit Bridge** integration, packaged as a custom component so you can test
[home-assistant/core#180269](https://github.com/home-assistant/core/pull/180269) ("Add target selection to HomeKit Bridge") before it is merged.

Source: [`fabiangigler/home-assistant-core@d0d8b26`](https://github.com/fabiangigler/home-assistant-core/tree/d0d8b26ac6624324719ce385c8830e2ce3d6002f/homeassistant/components/homekit).
All credit goes to the PR author and the HomeKit integration maintainers.

## What it adds

- Include or exclude **entities, devices, areas, floors and labels** on top of the domain selection.
- More specific rules override broader ones; when two rules are equally specific, the exclude wins.
- A **review step** listing exactly which entities will be exposed before you save.
- Existing entity include/exclude selections are carried over when editing a bridge.

## Extra in this repo: `require_targets` (YAML only)

The PR's rules are either/or: an area include exposes *everything* in the area. `require_targets` adds an **and**:
an entity must also match at least one of these targets to be exposed. This makes "one bridge per area, only things
labelled HomeKit" possible:

```yaml
homekit:
  - name: HA Living Room Bridge
    port: 21063
    filter:
      include_targets:
        area_id: living_room
      require_targets:
        label_id: homekit
```

- A label on the **device** counts too, so labelling a Hue bulb's device is enough.
- It applies to every rule, including `include_entities`, so everything you expose carries the label and
  *Settings → Labels → HomeKit* lists all of it.
- Used on its own (no include rules), it exposes everything with the label.
- Adding or removing the label, or moving things between areas, reloads the bridge automatically.
- Not shown in the UI config flow; set it in YAML.

## Install

> ⚠️ This **overrides the built-in `homekit` integration** for all your bridges. Take a backup first.
> Requires Home Assistant 2026.9 or newer.

**HACS:** HACS → ⋮ → *Custom repositories* → add `https://github.com/AlexHallberg/ha-homekit-target-selection` as type *Integration* → download → restart Home Assistant.

**Manual:** copy `custom_components/homekit` into `/config/custom_components/` and restart.

## Remove

Delete it in HACS (or remove `/config/custom_components/homekit`) and restart. The built-in HomeKit Bridge loads again.

## Changes from upstream

- `manifest.json`: added `version` (required for custom components).
- `translations/en.json`: generated from `strings.json` with `[%key:…%]` references resolved.
