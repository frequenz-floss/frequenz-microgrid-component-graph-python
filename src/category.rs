// License: MIT
// Copyright © 2025 Frequenz Energy-as-a-Service GmbH

use frequenz_microgrid_component_graph as cg;
use pyo3::{exceptions, prelude::*};

/// Bindings to the Python classes that map to a [`cg::ComponentCategory`].
///
/// Field order mirrors the `ComponentCategory` enum in
/// `frequenz.client.microgrid.component._category` so that adding,
/// removing, or reshuffling a category here is an obvious visual diff
/// against the upstream client. Categories present only on the cg side
/// (no client class) follow at the end.
///
/// Classes carried as `Bound<PyAny>` are required to exist in the
/// resolved provider module — these are the classes the microgrid
/// client ships today that aren't expected to be renamed or removed.
/// Classes carried as `Option<Bound<PyAny>>` are looked up with
/// `.ok()` so the bindings keep working when the class isn't
/// present: forward-compat aliases the client may adopt later
/// (`Breaker`, `PowerTransformer`), classes paired with such an
/// alias that may themselves disappear after a rename (`Relay`,
/// `VoltageTransformer`), or cg-only categories no current provider
/// exposes (`Plc`, `CapacitorBank`, …).
struct ComponentClasses<'py> {
    // UNSPECIFIED — every problematic-component subclass collapses
    // to `cg::Unspecified`.
    unspecified_component: Bound<'py, PyAny>,
    unrecognized_component: Bound<'py, PyAny>,

    // GRID_CONNECTION_POINT
    grid_connection_point: Bound<'py, PyAny>,

    // METER
    meter: Bound<'py, PyAny>,

    // INVERTER (subtypes first; parent class catches Unspecified*
    // and Unrecognized* subclasses).
    battery_inverter: Bound<'py, PyAny>,
    hybrid_inverter: Bound<'py, PyAny>,
    solar_inverter: Bound<'py, PyAny>,
    inverter: Bound<'py, PyAny>,

    // CONVERTER
    converter: Bound<'py, PyAny>,

    // BATTERY (subtypes first; parent class catches Unspecified*
    // and Unrecognized* subclasses).
    li_ion_battery: Bound<'py, PyAny>,
    na_ion_battery: Bound<'py, PyAny>,
    battery: Bound<'py, PyAny>,

    // EV_CHARGER (subtypes first; parent class catches Unspecified*
    // and Unrecognized* subclasses).
    ac_ev_charger: Bound<'py, PyAny>,
    dc_ev_charger: Bound<'py, PyAny>,
    hybrid_ev_charger: Bound<'py, PyAny>,
    ev_charger: Bound<'py, PyAny>,

    // CRYPTO_MINER
    crypto_miner: Bound<'py, PyAny>,

    // ELECTROLYZER
    electrolyzer: Bound<'py, PyAny>,

    // CHP
    chp: Bound<'py, PyAny>,

    // RELAY → cg::Breaker. The microgrid client today ships a
    // class named `Relay`; the underlying protobuf tag has always
    // been BREAKER, and a future client may rename the class to
    // match. `Option<>` here so a rename that drops `Relay`
    // doesn't break the bindings.
    relay: Option<Bound<'py, PyAny>>,
    // Forward-compat alias: matches if the client renames its
    // class to the protobuf-canonical `Breaker`. One of
    // `relay`/`breaker` will become redundant after such a rename
    // and can be dropped.
    breaker: Option<Bound<'py, PyAny>>,

    // PRECHARGER
    precharger: Bound<'py, PyAny>,

    // POWER_TRANSFORMER → cg::PowerTransformer. The microgrid
    // client today ships a class named `VoltageTransformer`; the
    // protobuf enum was renamed from VOLTAGE_TRANSFORMER to
    // POWER_TRANSFORMER (with VOLTAGE_TRANSFORMER kept only as a
    // deprecated enum alias), but the class hasn't followed yet.
    // `Option<>` here so a rename that drops `VoltageTransformer`
    // doesn't break the bindings.
    voltage_transformer: Option<Bound<'py, PyAny>>,
    // Forward-compat alias: matches if the client renames its
    // class to the protobuf-canonical `PowerTransformer`. One of
    // `voltage_transformer`/`power_transformer` will become
    // redundant after such a rename and can be dropped.
    power_transformer: Option<Bound<'py, PyAny>>,

    // HVAC
    hvac: Bound<'py, PyAny>,

    // WIND_TURBINE
    wind_turbine: Bound<'py, PyAny>,

    // STEAM_BOILER
    steam_boiler: Bound<'py, PyAny>,

    // cg-only categories (no class in the microgrid client today;
    // probed optionally so an alternative provider that exposes
    // them works without a code change).
    plc: Option<Bound<'py, PyAny>>,
    static_transfer_switch: Option<Bound<'py, PyAny>>,
    uninterruptible_power_supply: Option<Bound<'py, PyAny>>,
    capacitor_bank: Option<Bound<'py, PyAny>>,
}

impl<'py> ComponentClasses<'py> {
    fn try_new(py: Python<'py>) -> PyResult<Self> {
        let candidates = vec![
            "frequenz.client.microgrid.component".to_string(),
            "frequenz.client.assets.electrical_component".to_string(),
        ];

        let mut last_err: Option<PyErr> = None;
        for path in &candidates {
            match py.import(path) {
                Ok(module) => {
                    return Ok(Self {
                        unspecified_component: module.getattr("UnspecifiedComponent")?,
                        unrecognized_component: module.getattr("UnrecognizedComponent")?,

                        grid_connection_point: module.getattr("GridConnectionPoint")?,

                        meter: module.getattr("Meter")?,

                        battery_inverter: module.getattr("BatteryInverter")?,
                        hybrid_inverter: module.getattr("HybridInverter")?,
                        solar_inverter: module.getattr("SolarInverter")?,
                        inverter: module.getattr("Inverter")?,

                        converter: module.getattr("Converter")?,

                        li_ion_battery: module.getattr("LiIonBattery")?,
                        na_ion_battery: module.getattr("NaIonBattery")?,
                        battery: module.getattr("Battery")?,

                        ac_ev_charger: module.getattr("AcEvCharger")?,
                        dc_ev_charger: module.getattr("DcEvCharger")?,
                        hybrid_ev_charger: module.getattr("HybridEvCharger")?,
                        ev_charger: module.getattr("EvCharger")?,

                        crypto_miner: module.getattr("CryptoMiner")?,

                        electrolyzer: module.getattr("Electrolyzer")?,

                        chp: module.getattr("Chp")?,

                        relay: module.getattr("Relay").ok(),
                        breaker: module.getattr("Breaker").ok(),

                        precharger: module.getattr("Precharger")?,

                        voltage_transformer: module.getattr("VoltageTransformer").ok(),
                        power_transformer: module.getattr("PowerTransformer").ok(),

                        hvac: module.getattr("Hvac")?,

                        wind_turbine: module.getattr("WindTurbine")?,

                        steam_boiler: module.getattr("SteamBoiler")?,

                        plc: module.getattr("Plc").ok(),
                        static_transfer_switch: module.getattr("StaticTransferSwitch").ok(),
                        uninterruptible_power_supply: module
                            .getattr("UninterruptiblePowerSupply")
                            .ok(),
                        capacitor_bank: module.getattr("CapacitorBank").ok(),
                    });
                }
                Err(e) => last_err = Some(e),
            }
        }
        Err(pyo3::exceptions::PyImportError::new_err(format!(
            "Could not import a component provider. Tried: {candidates:?}. \
            Install one: pip install frequenz-component-graph[microgrid] or [assets]. \
            Last error: {last_err:?}"
        )))
    }
}

/// True when `object` is `class` itself or an instance of it.
fn is_class_or_instance(object: &Bound<'_, PyAny>, class: &Bound<'_, PyAny>) -> PyResult<bool> {
    Ok(object.is_instance(class)? || object.is(class))
}

/// Same as [`is_class_or_instance`], but returns `false` when the optional
/// class wasn't resolved by [`ComponentClasses::try_new`].
fn is_class_or_instance_opt(
    object: &Bound<'_, PyAny>,
    class: Option<&Bound<'_, PyAny>>,
) -> PyResult<bool> {
    match class {
        Some(c) => is_class_or_instance(object, c),
        None => Ok(false),
    }
}

pub(crate) fn category_from_python_component(
    py: Python<'_>,
    object: &Bound<'_, PyAny>,
) -> PyResult<cg::ComponentCategory> {
    let cls = ComponentClasses::try_new(py)?;

    // Order mirrors the `ComponentCategory` enum in
    // `frequenz.client.microgrid.component._category`. Within each
    // category, concrete subtype classes are checked before their
    // abstract parent so the cg-side subtype is preserved instead
    // of collapsing to `Unspecified`. cg-only categories follow at
    // the end.

    // UNSPECIFIED
    if is_class_or_instance(object, &cls.unspecified_component)?
        || is_class_or_instance(object, &cls.unrecognized_component)?
    {
        return Ok(cg::ComponentCategory::Unspecified);
    }

    // GRID_CONNECTION_POINT
    if is_class_or_instance(object, &cls.grid_connection_point)? {
        return Ok(cg::ComponentCategory::GridConnectionPoint);
    }

    // METER
    if is_class_or_instance(object, &cls.meter)? {
        return Ok(cg::ComponentCategory::Meter);
    }

    // INVERTER
    if is_class_or_instance(object, &cls.battery_inverter)? {
        return Ok(cg::ComponentCategory::Inverter(cg::InverterType::Battery));
    }
    if is_class_or_instance(object, &cls.hybrid_inverter)? {
        return Ok(cg::ComponentCategory::Inverter(cg::InverterType::Hybrid));
    }
    if is_class_or_instance(object, &cls.solar_inverter)? {
        return Ok(cg::ComponentCategory::Inverter(cg::InverterType::Pv));
    }
    if is_class_or_instance(object, &cls.inverter)? {
        return Ok(cg::ComponentCategory::Inverter(
            cg::InverterType::Unspecified,
        ));
    }

    // CONVERTER
    if is_class_or_instance(object, &cls.converter)? {
        return Ok(cg::ComponentCategory::Converter);
    }

    // BATTERY
    if is_class_or_instance(object, &cls.li_ion_battery)? {
        return Ok(cg::ComponentCategory::Battery(cg::BatteryType::LiIon));
    }
    if is_class_or_instance(object, &cls.na_ion_battery)? {
        return Ok(cg::ComponentCategory::Battery(cg::BatteryType::NaIon));
    }
    if is_class_or_instance(object, &cls.battery)? {
        return Ok(cg::ComponentCategory::Battery(cg::BatteryType::Unspecified));
    }

    // EV_CHARGER
    if is_class_or_instance(object, &cls.ac_ev_charger)? {
        return Ok(cg::ComponentCategory::EvCharger(cg::EvChargerType::Ac));
    }
    if is_class_or_instance(object, &cls.dc_ev_charger)? {
        return Ok(cg::ComponentCategory::EvCharger(cg::EvChargerType::Dc));
    }
    if is_class_or_instance(object, &cls.hybrid_ev_charger)? {
        return Ok(cg::ComponentCategory::EvCharger(cg::EvChargerType::Hybrid));
    }
    if is_class_or_instance(object, &cls.ev_charger)? {
        return Ok(cg::ComponentCategory::EvCharger(
            cg::EvChargerType::Unspecified,
        ));
    }

    // CRYPTO_MINER
    if is_class_or_instance(object, &cls.crypto_miner)? {
        return Ok(cg::ComponentCategory::CryptoMiner);
    }

    // ELECTROLYZER
    if is_class_or_instance(object, &cls.electrolyzer)? {
        return Ok(cg::ComponentCategory::Electrolyzer);
    }

    // CHP
    if is_class_or_instance(object, &cls.chp)? {
        return Ok(cg::ComponentCategory::Chp);
    }

    // RELAY — the client's `Relay` is the protobuf BREAKER tag.
    // `Breaker` is also accepted from alternative providers.
    if is_class_or_instance_opt(object, cls.relay.as_ref())?
        || is_class_or_instance_opt(object, cls.breaker.as_ref())?
    {
        return Ok(cg::ComponentCategory::Breaker);
    }

    // PRECHARGER
    if is_class_or_instance(object, &cls.precharger)? {
        return Ok(cg::ComponentCategory::Precharger);
    }

    // POWER_TRANSFORMER — `VoltageTransformer` is the deprecated
    // client alias for the same protobuf POWER_TRANSFORMER tag.
    if is_class_or_instance_opt(object, cls.voltage_transformer.as_ref())?
        || is_class_or_instance_opt(object, cls.power_transformer.as_ref())?
    {
        return Ok(cg::ComponentCategory::PowerTransformer);
    }

    // HVAC
    if is_class_or_instance(object, &cls.hvac)? {
        return Ok(cg::ComponentCategory::Hvac);
    }

    // WIND_TURBINE
    if is_class_or_instance(object, &cls.wind_turbine)? {
        return Ok(cg::ComponentCategory::WindTurbine);
    }

    // STEAM_BOILER
    if is_class_or_instance(object, &cls.steam_boiler)? {
        return Ok(cg::ComponentCategory::SteamBoiler);
    }

    // cg-only categories — no class in the microgrid client
    // today, but mapped here so an alternative provider that
    // exposes them just works.
    if is_class_or_instance_opt(object, cls.plc.as_ref())? {
        return Ok(cg::ComponentCategory::Plc);
    }
    if is_class_or_instance_opt(object, cls.static_transfer_switch.as_ref())? {
        return Ok(cg::ComponentCategory::StaticTransferSwitch);
    }
    if is_class_or_instance_opt(object, cls.uninterruptible_power_supply.as_ref())? {
        return Ok(cg::ComponentCategory::UninterruptiblePowerSupply);
    }
    if is_class_or_instance_opt(object, cls.capacitor_bank.as_ref())? {
        return Ok(cg::ComponentCategory::CapacitorBank);
    }

    Err(exceptions::PyValueError::new_err(format!(
        "Unsupported component category: {:?}",
        object
    )))
}

pub(crate) fn match_category(
    category_1: cg::ComponentCategory,
    category_2: cg::ComponentCategory,
) -> bool {
    match (category_1, category_2) {
        (cg::ComponentCategory::Inverter(type_1), cg::ComponentCategory::Inverter(type_2)) => {
            match (type_1, type_2) {
                (cg::InverterType::Unspecified, _) | (_, cg::InverterType::Unspecified) => true,
                _ => type_1 == type_2,
            }
        }
        (cg::ComponentCategory::Battery(type_1), cg::ComponentCategory::Battery(type_2)) => {
            match (type_1, type_2) {
                (cg::BatteryType::Unspecified, _) | (_, cg::BatteryType::Unspecified) => true,
                _ => type_1 == type_2,
            }
        }
        (cg::ComponentCategory::EvCharger(type_1), cg::ComponentCategory::EvCharger(type_2)) => {
            match (type_1, type_2) {
                (cg::EvChargerType::Unspecified, _) | (_, cg::EvChargerType::Unspecified) => true,
                _ => type_1 == type_2,
            }
        }
        _ => category_1 == category_2,
    }
}
