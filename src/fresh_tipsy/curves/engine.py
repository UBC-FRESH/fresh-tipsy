"""Growth table selection over the fresh-tipsy catalog."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from fresh_tipsy.curves.errors import SourceUnavailableError, UnsupportedQueryError
from fresh_tipsy.curves.interpolation import interpolate_table
from fresh_tipsy.curves.models import CurveQuery, Provenance, QueryResult, TableSelection
from fresh_tipsy.tables.catalog import CatalogEntry, CatalogQuery, TableCatalog
from fresh_tipsy.tables.parsers import TIPSYTable, parse_tab_file, parse_taf_file

_PNC_PREFERENCE: tuple[str, ...] = ("N", "C", "P")


@dataclass(frozen=True)
class CurveEngine:
    """Select source tables for growth queries.

    Parameters
    ----------
    catalog : TableCatalog
        Table catalog.
    source_root : Path or None, optional
        TIPSY database directory used to load table rows.
    """

    catalog: TableCatalog
    source_root: Path | None = None

    @classmethod
    def from_manifest(cls, path: Path, source_root: Path | None = None) -> CurveEngine:
        """Load an engine from a manifest file.

        Parameters
        ----------
        path : Path
            Manifest JSON path.
        source_root : Path or None, optional
            TIPSY database directory.

        Returns
        -------
        CurveEngine
            Engine backed by the loaded catalog.
        """
        return cls(TableCatalog.from_manifest(path), source_root=source_root)

    def query(self, query: CurveQuery) -> QueryResult:
        """Select a table and interpolate the query age.

        Parameters
        ----------
        query : CurveQuery
            Growth query.

        Returns
        -------
        QueryResult
            Selected table and interpolated row.

        Raises
        ------
        UnsupportedQueryError
            When no table or scenario can answer the query.
        InterpolationError
            When the age is missing or outside the source range.
        SourceUnavailableError
            When the source table cannot be loaded.
        """
        selection = self.select_table(query)
        table = self.load_table(selection)
        row = interpolate_table(table, query)
        return QueryResult(selection=selection, row=row)

    def load_table(self, selection: TableSelection) -> TIPSYTable:
        """Load the parsed source table for a selection.

        Parameters
        ----------
        selection : TableSelection
            Selected table.

        Returns
        -------
        TIPSYTable
            Parsed source table.

        Raises
        ------
        SourceUnavailableError
            When the source root is missing, the path escapes it, or the file
            cannot be read.
        """
        if self.source_root is None:
            message = "source_root is required to load table rows"
            raise SourceUnavailableError(message)
        root = self.source_root.resolve()
        path = (root / selection.provenance.relative_path).resolve()
        if not path.is_relative_to(root):
            message = f"source path escapes the source root: {selection.provenance.relative_path}"
            raise SourceUnavailableError(message)
        try:
            if selection.provenance.format == "tab":
                return parse_tab_file(path)
            return parse_taf_file(path)
        except OSError as exc:
            message = f"source table cannot be read: {path}"
            raise SourceUnavailableError(message) from exc

    def select_table(self, query: CurveQuery) -> TableSelection:
        """Select the source table for a query.

        Parameters
        ----------
        query : CurveQuery
            Growth query.

        Returns
        -------
        TableSelection
            Selected table and provenance.

        Raises
        ------
        UnsupportedQueryError
            When no table covers the species, site, PNC, stock height, source
            version, or format.
        """
        species = query.species_code.upper()
        candidates = list(self.catalog.search(CatalogQuery(species_code=species)))
        if not candidates:
            message = f"unknown species: {species}"
            raise UnsupportedQueryError(message)
        site_candidates = [
            entry for entry in candidates if entry.site_from <= query.site_index <= entry.site_to
        ]
        if not site_candidates:
            ranges = ", ".join(f"{entry.site_from}-{entry.site_to}" for entry in candidates)
            message = (
                f"site index {query.site_index} is outside the available range "
                f"for {species}: {ranges}"
            )
            raise UnsupportedQueryError(message)
        candidates = site_candidates
        notes: list[str] = []
        if query.pnc is not None:
            candidates = [entry for entry in candidates if entry.pnc == query.pnc.upper()]
            if not candidates:
                message = f"no {species} table for PNC {query.pnc.upper()}"
                raise UnsupportedQueryError(message)
        else:
            for preferred in _PNC_PREFERENCE:
                subset = [entry for entry in candidates if entry.pnc == preferred]
                if subset:
                    candidates = subset
                    notes.append(f"default PNC {preferred}")
                    break
        if query.source_version is not None:
            candidates = [
                entry for entry in candidates if entry.source_version == query.source_version
            ]
            if not candidates:
                message = f"no table for source version {query.source_version}"
                raise UnsupportedQueryError(message)
        else:
            versions = sorted({entry.source_version for entry in candidates})
            if len(versions) > 1:
                latest = versions[-1]
                candidates = [entry for entry in candidates if entry.source_version == latest]
                notes.append(f"default source version {latest}")
        candidates = [entry for entry in candidates if entry.format == query.format]
        if not candidates:
            message = f"no {query.format} table for {species}"
            raise UnsupportedQueryError(message)
        candidates = self._filter_stock_height(candidates, query, notes)
        candidates.sort(key=lambda entry: (entry.site_to - entry.site_from, entry.asset_id))
        selected = candidates[0]
        alternatives = tuple(entry.asset_id for entry in candidates[1:])
        rationale = "; ".join(notes) if notes else "unique table match"
        return TableSelection(
            entry=selected,
            query=query,
            provenance=Provenance.from_entry(selected),
            rationale=rationale,
            alternatives=alternatives,
        )

    @staticmethod
    def _filter_stock_height(
        candidates: list[CatalogEntry], query: CurveQuery, notes: list[str]
    ) -> list[CatalogEntry]:
        """Filter candidates by stock height and record the default.

        Parameters
        ----------
        candidates : list of CatalogEntry
            Candidate entries.
        query : CurveQuery
            Original query.
        notes : list of str
            Selection rationale accumulator.

        Returns
        -------
        list of CatalogEntry
            Filtered candidates.

        Raises
        ------
        UnsupportedQueryError
            When an exact stock height is requested but no table matches.
        """
        if query.stock_height_m is not None:
            exact = [
                entry
                for entry in candidates
                if entry.stock_height_m is not None
                and abs(entry.stock_height_m - query.stock_height_m) <= 1e-9
            ]
            if not exact:
                message = f"no table with stock height {query.stock_height_m}"
                raise UnsupportedQueryError(message)
            return exact
        no_height = [entry for entry in candidates if entry.stock_height_m is None]
        if no_height:
            notes.append("default stock height unspecified")
            return no_height
        heights = sorted(
            {entry.stock_height_m for entry in candidates if entry.stock_height_m is not None}
        )
        chosen = heights[0]
        notes.append(f"default stock height {chosen}")
        return [
            entry
            for entry in candidates
            if entry.stock_height_m is not None and abs(entry.stock_height_m - chosen) <= 1e-9
        ]
