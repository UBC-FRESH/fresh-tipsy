"""Age interpolation and scenario extraction for growth tables."""

from __future__ import annotations

from fresh_tipsy.curves.errors import InterpolationError, ScenarioError
from fresh_tipsy.curves.models import CurveQuery, InterpolatedRow
from fresh_tipsy.tables.parsers import RunBlock, TableRow, TIPSYTable

_TOLERANCE = 1e-9
_SCENARIOS = {"UNTREATED", "PCT", "CT", "PCT+CT"}


def _to_float(raw: str) -> float | None:
    """Parse a table value while preserving blanks.

    Parameters
    ----------
    raw : str
        Raw field.

    Returns
    -------
    float or None
        Parsed value, or ``None`` when blank.

    Raises
    ------
    InterpolationError
        When the field is not numeric.
    """
    text = raw.strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError as exc:
        message = f"table value is not numeric: {raw!r}"
        raise InterpolationError(message) from exc


def _series(block: RunBlock) -> tuple[tuple[float, TableRow], ...]:
    """Return a block's rows keyed by age, keeping the last duplicate.

    Parameters
    ----------
    block : RunBlock
        Run block.

    Returns
    -------
    tuple of (float, TableRow)
        Sorted age/row pairs.

    Raises
    ------
    InterpolationError
        When the block has no numeric age.
    """
    rows: dict[float, TableRow] = {}
    for row in block.rows:
        if row.age is not None:
            rows[row.age] = row
    if not rows:
        message = f"run block has no numeric age: {block.marker.raw}"
        raise InterpolationError(message)
    return tuple(sorted(rows.items()))


def select_block(table: TIPSYTable, query: CurveQuery) -> tuple[int, RunBlock]:
    """Select the run block for a scenario query.

    Parameters
    ----------
    table : TIPSYTable
        Parsed source table.
    query : CurveQuery
        Query with optional scenario and density filters.

    Returns
    -------
    tuple of (int, RunBlock)
        Block index and block.

    Raises
    ------
    ScenarioError
        When no block matches the scenario or density filters.
    """
    scenario = query.scenario.upper() if query.scenario is not None else None
    if scenario is not None and scenario not in _SCENARIOS:
        message = f"unsupported scenario: {query.scenario}"
        raise ScenarioError(message)
    candidates: list[tuple[int, RunBlock]] = []
    for index, block in enumerate(table.blocks):
        marker = block.marker
        if query.initial_density is not None and marker.initial_density != query.initial_density:
            continue
        if query.pct_density is not None and marker.pct_density != query.pct_density:
            continue
        if query.ct_density is not None and marker.ct_density != query.ct_density:
            continue
        if scenario is None:
            candidates.append((index, block))
        elif scenario == "UNTREATED":
            if block.treatment is None:
                candidates.append((index, block))
        elif block.treatment is not None and block.treatment.upper() == scenario:
            candidates.append((index, block))
    if scenario is None:
        untreated = [(index, block) for index, block in candidates if block.treatment is None]
        if untreated:
            candidates = untreated
    if not candidates:
        available = ", ".join(
            f"{block.treatment or 'untreated'}:"
            f"{block.marker.initial_density}/{block.marker.pct_density}/"
            f"{block.marker.ct_density}"
            for block in table.blocks
        )
        message = f"no matching scenario; available blocks: {available}"
        raise ScenarioError(message)
    return candidates[0]


def interpolate_block(block: RunBlock, block_index: int, age: float) -> InterpolatedRow:
    """Interpolate one run block at an age.

    Parameters
    ----------
    block : RunBlock
        Run block.
    block_index : int
        Source block index.
    age : float
        Requested age.

    Returns
    -------
    InterpolatedRow
        Interpolated values and bracketing ages.

    Raises
    ------
    InterpolationError
        When the age is outside the block's age range.
    """
    series = _series(block)
    first_age = series[0][0]
    last_age = series[-1][0]
    if age < first_age - _TOLERANCE or age > last_age + _TOLERANCE:
        message = f"age {age} is outside the source range {first_age}-{last_age}"
        raise InterpolationError(message)
    for exact_age, row in series:
        if abs(age - exact_age) <= _TOLERANCE:
            exact_values = tuple(_to_float(value) for value in row.fields[1:])
            return InterpolatedRow(
                age=age,
                values=exact_values,
                lower_age=exact_age,
                upper_age=exact_age,
                fraction=0.0,
                scenario=block.treatment or "untreated",
                block_index=block_index,
                initial_density=block.marker.initial_density,
                pct_density=block.marker.pct_density,
                ct_density=block.marker.ct_density,
            )
    lower_age, lower_row = series[0]
    upper_age, upper_row = series[-1]
    for current_age, current_row in series:
        if current_age < age:
            lower_age, lower_row = current_age, current_row
        else:
            upper_age, upper_row = current_age, current_row
            break
    fraction = (age - lower_age) / (upper_age - lower_age)
    values: list[float | None] = []
    for lower_raw, upper_raw in zip(lower_row.fields[1:], upper_row.fields[1:], strict=True):
        lower = _to_float(lower_raw)
        upper = _to_float(upper_raw)
        if lower is None or upper is None:
            values.append(None)
        else:
            values.append(lower + ((upper - lower) * fraction))
    return InterpolatedRow(
        age=age,
        values=tuple(values),
        lower_age=lower_age,
        upper_age=upper_age,
        fraction=fraction,
        scenario=block.treatment or "untreated",
        block_index=block_index,
        initial_density=block.marker.initial_density,
        pct_density=block.marker.pct_density,
        ct_density=block.marker.ct_density,
    )


def interpolate_table(table: TIPSYTable, query: CurveQuery) -> InterpolatedRow:
    """Select a scenario and interpolate a table at the query age.

    Parameters
    ----------
    table : TIPSYTable
        Parsed source table.
    query : CurveQuery
        Query with a required age.

    Returns
    -------
    InterpolatedRow
        Interpolated row.

    Raises
    ------
    InterpolationError
        When the query has no age or the age is outside the source range.
    ScenarioError
        When no scenario matches.
    """
    if query.age is None:
        message = "age is required for interpolation"
        raise InterpolationError(message)
    block_index, block = select_block(table, query)
    return interpolate_block(block, block_index, query.age)
