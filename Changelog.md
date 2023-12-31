# Changelog

This describes user-visible changes, not changes to the internals.

## [0.1.0] - 2023-11-14 - Ross Boylan <ross.boylan@ucsf.edu>

### Added

- Clear all fields after `Save` and before reading in a new parameter file.  Closes #6.
  Why both?  Someone might make some entries in the form, accidentally or
  deliberately, after hitting `Save` and before reading in a new file.
- Improved handling when input file's text doesn't match allowed values (Closes #11)
  - ComboBoxes that don't match have red text of  `?` followed by the value in file on yellow background
  - Checkboxes that don't match will be in yellow, but considerd as unchecked
  - With explanatory tooltip
- Breast L/R now accepts "left" or "right", any case, as inputs from text file

### Changed

- Site now starts blank (not `Georgetown`), and has an "Other" option. (Fixes #10 after changing goal)
- Visit starts blank (not `1`) and allows selection set to blank (tangential hit #11).
- Autotiming and FOV fields have different appearance.
- Breast L/R now appears as uppercase, continues to write data lowercase, accepts any case as input



## [0.0.7] - 2023-10-25 - Ross Boylan <ross.boylan@ucsf.edu>

### Added

- Error reporting (Fixes #4)
  - Report errors graphically and to terminal
  - Exit program and release all locks if error
- Missing fields (Fixes #9)
  - Correctly write `report_received_date` and `report_returned_date` to db (was just putting None)
  - Possibly correct codes for dates as mdy or uk; was None.
- Popup confirms successful save (Fix #5)
 
### Changed

- Comments textbox default and minimum reduced to 3 rows from 4.  Really still on Issue #1.  It's unclear if this changed anything visible.

### Fixed

- Failure when no deviation reasons selected (fixes #3)

### Removed

- Cryptic Pop-Up for Invalid dates (Partially addresses #8)


## [0.0.6] - 2023-09-30 - Ross Boylan <ross.boylan@ucsf.edu>

### Fixed

- Now with scrollbars if screen is small (Closes #1)
