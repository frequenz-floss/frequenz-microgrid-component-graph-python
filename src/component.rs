// License: MIT
// Copyright © 2025 Frequenz Energy-as-a-Service GmbH

use frequenz_microgrid_component_graph as cg;

use pyo3::{
    exceptions::{PyAttributeError, PyValueError},
    prelude::*,
    types::PyAny,
};

use crate::{category::category_from_python_component, utils::extract_int};

/// A wrapper for the Python object representing a component.
pub(crate) struct Component {
    pub(crate) component_id: u64,
    pub(crate) category: cg::ComponentCategory,
    pub(crate) operational_mode: cg::OperationalMode,
    pub(crate) object: Py<PyAny>,
}

impl cg::Node for Component {
    fn component_id(&self) -> u64 {
        self.component_id
    }

    fn category(&self) -> cg::ComponentCategory {
        self.category
    }

    fn operational_mode(&self) -> cg::OperationalMode {
        self.operational_mode
    }
}

/// Reads a component's operational mode.
///
/// The Python side splits the mode into two flags, `provides_telemetry()`
/// and `accepts_control()`, each of which raises `ValueError` when the mode
/// is unspecified. Both flags together name one `OperationalMode`.
///
/// A mode is only named when both flags are known. One flag alone does
/// not name a mode: `provides_telemetry() == false` fits both `Inactive`
/// and `ControlOnly`. So a half-known mode is reported as `Unspecified`,
/// which the graph treats as providing telemetry -- a component that says
/// it has no telemetry but not whether it takes control keeps measuring.
/// The API sends the two flags together or not at all, so this is a
/// hand-built component, and reporting a mode it did not state would be
/// a guess.
fn operational_mode_from_python_component(
    object: &Bound<'_, PyAny>,
) -> PyResult<cg::OperationalMode> {
    let (Some(telemetry), Some(control)) = (
        specified_flag(object, "provides_telemetry")?,
        specified_flag(object, "accepts_control")?,
    ) else {
        return Ok(cg::OperationalMode::Unspecified);
    };

    Ok(match (telemetry, control) {
        (true, true) => cg::OperationalMode::ControlAndTelemetry,
        (true, false) => cg::OperationalMode::TelemetryOnly,
        (false, true) => cg::OperationalMode::ControlOnly,
        (false, false) => cg::OperationalMode::Inactive,
    })
}

/// Calls a no-argument boolean method and reads its answer, if it has one.
///
/// Two ways a component can have no answer, both giving `None`:
///
/// * The method is missing. Not every supported component type carries
///   one: the methods arrived in `frequenz-client-microgrid` 0.18.4, and
///   the assets client has no equivalent. Like the category lookup, the
///   bindings keep working with a component that does not provide them.
/// * The method is there and raises `ValueError`, which is how a
///   component says its mode is unspecified.
///
/// Any other error is passed on. The method is looked up and called in
/// two steps on purpose, so that only a missing method is read as
/// unspecified: an `AttributeError` raised from inside the method body is
/// the caller's own bug, and reporting that as an unspecified mode would
/// hide it and leave the component measuring.
fn specified_flag(object: &Bound<'_, PyAny>, name: &str) -> PyResult<Option<bool>> {
    let method = match object.getattr(name) {
        Ok(method) => method,
        Err(err) if err.is_instance_of::<PyAttributeError>(object.py()) => return Ok(None),
        Err(err) => return Err(err),
    };

    match method.call0() {
        Ok(value) => value.extract().map(Some),
        Err(err) if err.is_instance_of::<PyValueError>(object.py()) => Ok(None),
        Err(err) => Err(err),
    }
}

impl Component {
    pub(crate) fn try_new(py: Python<'_>, object: Bound<'_, PyAny>) -> PyResult<Self> {
        let component_id = extract_int(py, object.getattr("id")?)?;
        let category = category_from_python_component(py, &object)?;
        let operational_mode = operational_mode_from_python_component(&object)?;

        Ok(Component {
            component_id,
            category,
            operational_mode,
            object: object.into(),
        })
    }
}
