# Changelog

## [Unreleased]

### Added
- Added `ScrubLayer.add_uuid_field()`.
- Added `ScrubLayer.extract_by_attribute()`.
- Added `ScrubLayer.extract_by_expression()`.
- Added `ScrubLayer.extract_by_aggregate_membership()`.
- Added `ScrubLayer.difference_layer()`.
- Added `ScrubLayer.spatial_join_with_predicate()`.
- Added `ScrubLayer.extract_unique_by_field()`.

### Planned
- Extend spatial join to support multiple predicates.

---

## [0.2.1] - 2026-05-27

### Fixed
- Fixed the published dependency requirement for `sabu-chassis` so CityGISOO
  can install with the currently available `sabu-chassis` release on PyPI.

---

## [0.2.0] - 2026-05-27

### Added
- Added package logging through the `sabu-chassis` logging system, giving
  CityGISOO workflows consistent log messages for layer loading, exports,
  schema operations, cleaning steps, and adapter runs.
- Added `FieldSchemaManager` to manage attribute schemas across supported map
  layer formats, including Shapefile and GeoJSON. It supports field listing,
  validation, renaming, removal, reordering, null-feature detection, GeoJSON
  export, ID-field creation, and field standardization workflows.
- Added `BuildingContractAdapter`, which uses `FieldSchemaManager` to prepare
  building map layers for downstream UBEM archetype-assignment inputs by
  exporting to GeoJSON, standardizing contract fields, removing incomplete
  contract records, and promoting generated IDs to GeoJSON feature IDs.

### Fixed
- Fixed `ScrubLayer.duplicate_layer()` text handling by writing duplicated
  layers with UTF-8 encoding through QGIS vector writer options.

---

## [0.1.3] - 2026-04-23

### Changed
- Updated the README logo to load from the public website so PyPI can render it correctly.

---

## [0.1.2] - 2026-04-10

### Added
- Added `file_join()`.

### Changed
- Extended `conditional_delete_record()` to support string conditions.

---

## [0.1.1] - 2026-03-07

- Expanded and clarified README documentation (project scope, JUGS context, and naming/dedication notes).
- No functional code changes.

## [0.1.0] - 2026-02-10

- Initial release.
- Includes `basic_functions` and the main `ScrubLayer` class.
