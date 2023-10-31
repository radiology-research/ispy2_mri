# based on https://doc.qt.io/qtforpython-6/tutorials/basictutorial/dialog.html
# error handling based on https://timlehr.com/2018/01/python-exception-hooks-with-qt-message-box/
from PySide6.QtWidgets import *
from PySide6.QtCore import Slot, QSize
from datetime import date, datetime
import logging
import sys
import traceback
import pyodbc
from pathlib import Path
from ispy2_mri.flowlayout import FlowLayout
import re

# set up logging to the terminal
log = logging.getLogger(__name__)
handler = logging.StreamHandler(stream=sys.stdout)
log.addHandler(handler)


def show_exception_box(log_msg):
	"""Checks if a QApplication instance is available and shows a messagebox with the exception message.
	Logs the notice to terminal if no GUI (which should be impossible).
	"""
	if QApplication.instance() is not None:
			QMessageBox.critical(None, "Fatal Error--No data saved",
				"An unexpected error occurred:\n{0}\n\nThis program will exit when you click OK.\n".format(log_msg))
	else:
		log.critical(log_msg)

class UnexpectedInputError(Exception):
	def __init__(self, obj=None):
		super().__init__(obj)

class BreastWidget:
	"""
	Abstract class for Mixins with QWidgets of various kinds
	Must implement the following protocol.

	Place the mixin at the end of the inheritance list.
	"""
	def __init__(self, *args, **kwargs):
		"""HACK.
		For reasons I don't understand, the arguments, such as parent, to the concrete classees end
		up being passed to object.__initialize__().  This causes an error, since it takes no arguments
		other than self.

		Here we intercept and remove all extra arguments.
		The mixing should be last so that other classes have a chance to process the arguments.

		The error process happens even if there are no explicit calls to super.
		"""
		super().__init__()

	def todb(self):
		"return value appropriate for insertion into database"
		pass

	def fromdb(self, v):
		"set value of widget with value v from database"
		pass

	def fromtext(self, v: str):
		"set value of widget from a textual value of v, e.g., from a text file"
		# default implementaiton
		self.fromdb(v)

	def clear(self):
		"set to blank or initial state"
		# default implementation
		self.fromtext("")

	def isValid(self):
		"return True if I contain a valid value"
		return True

class BSmallDateWidget(QWidget, BreastWidget):
	"""Allow date entry via 3 drop-down boxes in a row.
	"""
	def __init__(self, parent=None):
		QWidget.__init__(self, parent)
		layout = QHBoxLayout(self)
		self._mowidg = self._makemo()
		self._dawidg = self._makeda()
		self._yrwidg = self._makeyr()
		layout.addWidget(self._mowidg)
		layout.addWidget(self._dawidg)
		layout.addWidget(self._yrwidg)
		# it seems the tab order is set already, but just in case
		QWidget.setTabOrder(self._mowidg, self._dawidg)
		QWidget.setTabOrder(self._dawidg, self._yrwidg)

	def _makeRange(self, stop:int, start=1):
		"general combobox maker"
		cb = QComboBox(self)
		cb.addItem("", -1)
		for i in range(start, stop+1):
			cb.addItem(str(i), i)
		cb.setCurrentIndex(-1)
		return cb

	def _makemo(self):
		cb = self._makeRange(12)
		cb.setPlaceholderText("Month")
		return cb

	def _makeda(self):
		cb = self._makeRange(31)
		cb.setPlaceholderText("Day")
		return cb

	def _makeyr(self):
		cb = self._makeRange(date.today().year, start=2020)
		cb.editable = True
		cb.setPlaceholderText("Year")
		return cb

	def setDate(self, date: date):
		"set self from a Date or DateTime"
		if date is None:
			return self.setNoDate()
		self._mowidg.setCurrentText(str(date.month))
		self._dawidg.setCurrentText(str(date.day))
		self._yrwidg.setCurrentText(str(date.year))

	def date(self) -> date:
		"May also return None"
		ymd = 	(self._yrwidg.currentText().strip(),
				self._mowidg.currentText().strip(),
		  		self._dawidg.currentText().strip())
		if all(x.isdigit() for x in ymd):
			try:
				return date(*(int(x) for x in ymd))
			except ValueError as err:
				pass
		return None

	def isValid(self) -> bool:
		"considers blank or unknown as valid values"
		d = self.date()
		return isinstance(d, date) or d is None

	def todb(self):
		return self.date()

	def fromdb(self, v):
		self.setDate(v)

	def setNoDate(self):
		"set self to be an empty or unknown date"
		self._yrwidg.setCurrentIndex(-1)
		self._mowidg.setCurrentIndex(-1)
		self._dawidg.setCurrentIndex(-1)

	def clear(self):
		self.setNoDate()

	def fromtext(self, txt):
		if len(txt.strip()) == 0:
			self.setNoDate()
		else:
			# this is what I was using for text files.  It makes a lot of assumptions.
			# It also loses the time info, which of course can't be displayed in the
			# widget anyway.
			self.setDate(datetime.strptime(txt.split(sep=" ", maxsplit=1)[0], '%m/%d/%Y'))



class BTextEdit(QTextEdit, BreastWidget):
	"""created to override the excessive size of the parent class

	Implementation note: sizeHint is an attribute according to the documentation.
	But replacing it with a QSize fails because it gets invoked as a method.
	So we take a more indirect approach to setting it.
	"""

	def __init__(self, parent=None, rows=4, cols=80):
		"rows is preferred number of rows, similarly columns"
		QTextEdit.__init__(self, parent)
		# next seems to work even though this is early in setup
		fm = self.fontMetrics()
		# using maxWidth produces very wide dimensions, which affect the entire window being displayed
		self.myPreferredSize = QSize(fm.averageCharWidth()*cols, fm.lineSpacing()*rows)
		self.myrows = rows
		self.mycols = cols

	def sizeHint(self):
		return self.myPreferredSize

	def todb(self):
		return self.toPlainText()

	def fromdb(self, v):
		self.setPlainText(v)

class BLineEdit(QLineEdit, BreastWidget):
	def __init__(self, parent=None):
		QLineEdit.__init__(self, parent)

	def todb(self):
		# selectedText is  blank when values from file I inserted
		return self.displayText()

	def fromdb(self, v):
		self.setText(v)

class BIntEdit(BLineEdit):
	def todb(self):
		txt = super().todb().strip()
		if txt is None or len(txt)==0:
			return None
		# weirdly, some of these have fractions
		return round(float(txt))

class BNumEdit(BLineEdit):
	"for values that are numeric(p, s)"
	def __init__(self, parent=None, p=8, s=3):
		"we don't actually use the precision, but retain it for reference"
		super().__init__(parent)
		self._precision = p
		self._scale = s

	def todb(self):
		txt = super().todb().strip()
		if txt is None or len(txt)==0:
			return None
		return float(txt)

class BComboBox(QComboBox, BreastWidget):
	def __init__(self, parent=None):
		QComboBox.__init__(self, parent)

	def todb(self):
		return self.currentText()

	def fromdb(self, v):
		self.setEditText(v)

	def clear(self):
		self.setEditText("")
		self.setCurrentIndex(-1)


class BSiteComboBox(BComboBox):
	"""
	ComboBox specifically designed for sites, which have the following peculiarities:
	1. List of sites comes from a query of a special stored procedure.
	2. Sites have 3 pieces on information: an internal id, a numeric site id, and a name.
	3. We want to display them with site id and name in the drop-down.
	4. Insertion is based on the site id.
	Because of all this, new sites, and free-form site names, are a problem.
	The free-form names often don't match the ones we have, and new sites
	require a name and a number.  For now we leave adding sites alone.
	"""
	def __init__(self, parent=None, data=None):
		"""
		Data should be an iterable, indexable collection of data records.
		Each has (internl_id, site_id, site_name).
		This collection should be persistent for the life of the interface, i.e., don't
		use the database cursor directly.
		"""
		super().__init__(parent)
		for rec in data:
			label = f"{rec[1]:6d} | {rec[2]}"
			self.addItem(label, rec)
		self.addItem("Other (put site info in comment)", None)
		self.setCurrentIndex(-1)

	def todb(self):
		"must be something that was on the list"
		if self.currentIndex() < 0:
			return None
		x = self.currentData()
		if x:
			return x[1]
		return None

	def fromdb(self, v):
		"v will be the site id"
		for i in range(self.count()):
			r = self.itemData(i)
			if r[1] == v:
				self.setCurrentIndex(i)
				return
		raise UnexpectedInputError(f"Unknown site id {v} read from database.")

	def fromtext(self, v: str):
		"v is a site name.  It probably won't be an exact match"
		for i in range(self.count()):
			r = self.itemData(i)
			if r[2] == v:
				self.setCurrentIndex(i)
				return
		# not good if we get here, but for now we let it go
		self.setCurrentIndex(-1)
		pass  # mostly here so can set breakpoint

class BCheckBox(QCheckBox, BreastWidget):
	def __init__(self, parent=None, asText=True, val=None):
		QCheckBox.__init__(self, parent)
		self.asText = asText
		self._val = val

	def val(self):
		return self._val

	def todb(self):
		"Return Y/N if asText is True, else True/False"
		if self.isChecked():
			if self.asText:
				return "Y"
			else:
				return True
		else:
			if self.asText:
				return "N"
			else:
				return False

	def fromdb(self, v):
		if isinstance(v, bool):
			self.setChecked(v)
		elif isinstance(v, str) and len(v)>0:
			if v[0].upper() == 'Y':
				self.setChecked(True)
			elif v[0].upper() == 'N':
				self.setChecked(False)
		# otherwise do nothing. maybe throw error

	def clear(self):
		self.setChecked(False)


class BreastForm(QDialog):

	def getFile(self) -> str :
		"prompt user for file with scan parameters. Return path and set parameterFile, or return None"
		(fname, filter) = QFileDialog.getOpenFileName(self, "Scan Parameters File", ".", "Scan Files (*.txt)")
		if fname:
			self.clear()
			self.parameterFile = Path(fname)
			self.fileButton.setText(self.parameterFile.name)
			self.readFile(self.parameterFile)
			return fname
		return None

	paramRE = re.compile(r'^\s*(?P<var>[^:]+)\s*:\s*(?P<val>.*\S)\s*$')
	def readFile(self, path):
		"""
		parse the file in path and populate the appropriate fields
		"""
		r = {}
		with path.open("rt") as fin:
			for line in fin:
				m = self.paramRE.match(line)
				if m:
					v = m.group('val')
					match m.group('var'):
						# probably these should all set the field with fromtext, with logic moved there
						case 'I-SPY ID':
							self.ispy2_id.setText(v)
						case 'Date':
							self.mri_date.fromtext(v)
						case 'Visit ID':
							self.visit_number.setCurrentText(v)
						case 'Institution':
							# it would be good to do something other than put if the string
							# is not an exact match.  At least display it to user in some way.
							self.site.fromtext(v)
						case 'Breast':
							self.breast.setCurrentText(v.lower())
						case 'Tumor Volume':
							self.tumor_volume_submitted.setText(v)
						case 'Early Post Timing':
							self._set_auto_timing(1, v)
						case 'Late Post Timing':
							self._set_auto_timing(2, v)
						case 'PE Threshold':
							self._set_pct(self.pe_threshold, v)
						case 'Scan Duration':
							self.scan_duration.setText(v)
						case 'Gray Threshold':
							self._set_pct(self.bg_grey_threshold, v)
						case 'MOCO':
							v = v.lower()
							match v:
								case 'n' | 'no'| 'none':
									self.moco.setChecked(False) # probably the default
								case 'y' | 'yes':
									self.moco.setChecked(True)
								case _:
									raise UnexpectedInputError(f"Unrecognized value {v} for MOCO")
						case 'FOV':
							self._set_fov(v)
						case _:
							raise UnexpectedInputError(f"Can't handle input: {line}")


						#'I-SPY ID': '54346', 'Date': '01/24/2023 15:31:28', 'Visit ID': 'A3W', 'Institution': 'UCSF Medical Center PCMB', 'Breast': 'L', 'Tumor Volume': '21.946', 'Early Post Timing': '2:28 (2)', 'Late Post Timing': '7:25 (5)', 'PE Threshold': '70%', 'Scan Duration': '99.0', 'Gray Threshold': '60%', 'MOCO': 'None', 'FOV': '38.0 x 38.0'}
					r[m.group('var')] = m.group('val')
				elif line.strip():
					raise UnexpectedInputError(f"Can't handle mystery line: {line}")
		print(r)
		return r

	def _set_pct(self, widget, v: str):
		"""set a percent value into widget, removing %
		widget is assumed to be a QLineEdit, or at least something that responds to setText().
		"""
		v = v.strip()
		if v[-1] == "%":
			v = v[:-1]
		widget.setText(v)

	FOVRE = re.compile(r"([0-9.]+)\s+x\s+([0-9.]+)")
	def _set_fov(self, v: str):
		"set value like '32.0 x 32.0' into fov fields"
		m = self.FOVRE.match(v)
		if m:
			self.fov1.setText(m.group(1))
			self.fov2.setText(m.group(2))
		else:
			raise UnexpectedInputError(f"{v} value unparseable for FOV")

	timingRE = re.compile(r"(\d*):(\d+)\s+\((\d)\)")
	def _set_auto_timing(self, n:int, v:str):
		"""set values from text file into timing fields
		n  index of field to insert, 1 or 2
		v	field value, usually from text file
		"""
		m = self.timingRE.match(v)
		(m, s, x) = m.groups()
		getattr(self, f"auto_timing{n}_min").setText(m)
		getattr(self, f"auto_timing{n}_sec").setText(s)
		getattr(self, f"auto_timing{n}_option").setCurrentText(x)

	def _mark_automatic(self, form, widget):
		"""
		Mark row in layout as being something that can be filled in from file.
		Hides the row.
		Must call after widget has been inserted into the form.
		"""
		i = form.rowCount()-1
		self._automatics.append(i)
		# show everything
		#form.setRowVisible(i, False)

	def is_sane(self):
		"""Check that the values appear complete and correct, ready for insertion in db.
		Return True if they are, else False.
		May pop up dialogs to describe problems, or even to correct them.
		"""
		bad = [k for (k, v) in self._fields.items() if not v.isValid()]
		if bad:
			QMessageBox.warning(self, "You must fix fields before saving",
			   "Errors in "+", ".join(bad))
			return False
		return True

	def make_sane(self):
		"""Assure that values are internally consistent
		At the moment, these mirror the actions the web app performs before
		writing out the results.
		"""
		return
		# we don't have any of the _code fields until we write to db
		# so checking them isn't even possible.
		for k in ("mri", "report_received", "report_returned"):
			kcode = k+"_code"
			kdate = k+"_date"
			if getattr(self, kcode).todb() == "uk":
				getattr(self, kdate).setNoDate()

	def all_values(self):
		"return a dictionary of {field name, value}"
		return {fld: widg.todb() for fld, widg in self._fields.items()}

	def db_values(self):
		"""return iterable with values in correct order for db query
		Some of the requested fields are not on the form (or in some cases have a different name).
		Those will require some special handling, but for now they are all None.
		Note that the final field, id, is an output of the stored procedure.
		"""
		ordered_fields = (
			"ispy2_id",
			"visit_number",
			"submitted",
			"mri_date",
			"mri_code",
			"breast",
			"dce_compliant",
			"deviation_other_reason",
			"deviation_late_exam_overdue",
			"volume_calculation",
			"site",
			"tumor_volume_submitted",
			"auto_timing1_min",
			"auto_timing1_sec",
			"auto_timing1_option",
			"auto_timing2_min",
			"auto_timing2_sec",
			"auto_timing2_option",
			"scan_duration",
			"pe_threshold",
			"special_handling",
			"aegis_issues",
			"final_processing_location",
			"final_processing_aegis",
			"comments",
			"screen_fail",
			"report_returned_date",
			"report_returned_code",
			"bg_grey_threshold",
			"injection_rate",
			"flush_volume",
			"fov1",
			"fov2",
			"moco",
			"motion_brtool",
			"report_received_date",
			"report_received_code",
			"id"
   		)
		# fields not present on form or
		# on web form, but currently left blank: 'special_handling', 'aegis_issues' (checkboxes)
		# 'deviation_other_reason'
		# or otherwise requiring special handling
		# `mri_code` is alway mdy
		# 'report_returned_code' and 'report_received_code' either mdy or uk if the date is blank
		special_fields = ['mri_code', 'deviation_other_reason', 'special_handling', 'aegis_issues',
			'report_returned_date', 'report_returned_code', 'report_received_date',
			'report_received_code', 'id']
		self.make_sane()
		return [self._db_special(k) for k in ordered_fields]

	def _datecode(self, wdgt:BSmallDateWidget)->str:
		"Return an appropriate code for the date"
		if wdgt.todb():
			return 'mdy'
		return 'uk'

	def _db_special(self, field:str):
		"""
		Return a value to insert in the database for a field
		"""
		match field:
			# first 2 only here because lose the _date
			case 'report_received_date':
				return self.report_received.todb()
			case 'report_returned_date':
				return self.report_returned.todb()
			case 'report_received_code':
				return self._datecode(self.report_received)
			case 'report_returned_code':
				return self._datecode(self.report_returned)
			case 'mri_code':
				return self._datecode(self.mri_date)
		# none of special cases matched
		if field in self._fields:
			return self._fields[field].todb()
		return None

	def _discrep_widgets(self):
		"""Generator returning all checked discrepancy widgets.
		Returns any widget named discrep\d+.  No particular order is guaranteed.
		"""
		discRE = re.compile(r"^discrep\d+$")
		for nm, wdgt in self._fields.items():
			if discRE.match(nm) and wdgt.isChecked():
				yield wdgt

	def discrep_values(self):
		"""return a string with all checked ids for discrepancies
		This is the format expected the insert_ispy2_deviation stored procedure.
		"""
		r = ", ".join(str(w.val()) for w in self._discrep_widgets())
		if r:
			return r
		else:
			# The empty string will cause a syntax error on server side
			return "null"

	def write(self):
		"""
		Write my values into the database.  Return True on success.
		This uses database transactions to assure that either all tables are updated or none.
		It is not clear to me what happens when the submit button on
		insert\ispy2.jsp is pressed.  It probably does a submit_page, but there are 2 different
		implementations in 2 files.  Both do lots of checking, but don't seem as if they are for this form--wrong
		field list.  I think in the end
		insert\ispy2_action.jsp has the insert commands.  The commands which follow are loosely based
		on it.

   @ispy2_id varchar(10) = NULL,
   @visit_number varchar(10) = NULL,
   @submitted char(1) = NULL,
   @mri_date datetime2(3) = NULL,
   @mri_code varchar(3) = 'uk',
   @breast char(1) = NULL,
   @dce_compliant char(1) = NULL,
   @deviation_other_reason varchar(1000) = NULL,
   @deviation_late_exam_overdue int = NULL, --apparently number of days or NULL
   @volume_calculation varchar(100) = NULL,
   @site int = NULL,
   @tumor_volume_submitted varchar(10) = NULL,
   @auto_timing1_min varchar(10) = NULL,
   @auto_timing1_sec varchar(10) = NULL,
   @auto_timing1_option varchar(10) = NULL,
   @auto_timing2_min varchar(10) = NULL,
   @auto_timing2_sec varchar(10) = NULL,
   @auto_timing2_option varchar(10) = NULL,
   @scan_duration numeric(5, 2) = NULL,  -- 2 digit numbers. some end .80 or .90 so not seconds.  translate input?
   @pe_threshold int = NULL, -- probably % as integer. NULL or values from 7-89
   @special_handling char(1) = NULL,
   @aegis_issues char(1) = NULL,
   @final_processing_location varchar(50) = NULL,
   @final_processing_aegis varchar(50) = NULL,
   @comments varchar(1000) = NULL,
   @screen_fail char(1) = NULL,
   @report_returned_date datetime2(3) = NULL,
   @report_returned_code varchar(3) = 'uk',
   @bg_grey_threshold  varchar(10) = NULL,
   @injection_rate char(1) = NULL,
   @flush_volume char(1) = NULL,
   @fov1 int = NULL,  -- mostly NULL, integers from 22-48
   @fov2 int = NULL,
   @moco char(1) = NULL,
   @motion_brtool char(1) = NULL,
   @report_received_date datetime2(3) = NULL,
   @report_received_code varchar(3) = 'uk',
   @id numeric(5, 0) = NULL  OUTPUT
		"""

		# ignore this test for now
		if False and not self.is_sane():
			return False
		vals = self.db_values()
		self.curs.execute(
			"{call rb_insert_ispy2(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)}",
			vals
		)
		self.curs.nextset()  # otherwise get Previous SQL was not a query
		ispy2_tbl_id = self.curs.fetchone().ispy2_tbl_id
		discrepvals = self.discrep_values()
		# even empty could mean reseting some existing values
		self.curs.execute(
			"{call insert_ispy2_deviation(?,?)}", (ispy2_tbl_id, discrepvals)
		)
		self.curs.commit()
		QMessageBox.information(None, "Successful write to database",
						  f"""The new record is id={ispy2_tbl_id} in the ispy2 table.
Additional values may have been changed in the ispy2_deviations table.""")
		self.clear()
		self.fileButton.setText("Select File")
		return True

	@Slot()
	def save(self):
		self.write()

	def clear(self):
		"blank all fields"
		for w in self._fields.values():
			w.clear()

	def exception_hook(self, exc_type, exc_value, exc_traceback):
		"""Function handling uncaught exceptions.
		It is triggered each time an uncaught exception occurs.
		"""
		if issubclass(exc_type, KeyboardInterrupt):
			# ignore keyboard interrupt to support console applications
			sys.__excepthook__(exc_type, exc_value, exc_traceback)
		else:
			exc_info = (exc_type, exc_value, exc_traceback)
			log_msg = '\n'.join([''.join(traceback.format_tb(exc_traceback)),
					'{0}: {1}'.format(exc_type.__name__, exc_value)])
			self.curs.rollback()  # cancel transaction and release lock
			show_exception_box(log_msg)
			QApplication.instance().exit(1)

			#log.critical("Uncaught exception:\n {0}".format(log_msg), exc_info=exc_info)

			# trigger message box show
			#self._exception_caught.emit(log_msg)

	def __init__(self, parent=None):
		super(BreastForm, self).__init__(parent)
		self._automatics = []  # layout row indices for material to obtain from parameterFile
		self._fields = {}  # keys are field names, values are BreastWidgets
		sys.excepthook = self.exception_hook  # establish error handling
		self.outer = QFormLayout(self)
		self.setLayout(self.outer)
		self.DSN = 'breastdb-new'
		self.conn = pyodbc.connect(f"DSN={self.DSN}")  #passwordless login
		# self.conn.autocommit == False by default, which we want
		self.curs = self.conn.cursor()

		self.siteRecs = []
		rs = self.curs.execute("{call select_ispy2_sites}")
		r = rs.fetchone()
		while r:
			self.siteRecs.append((r.id, r.site, r.name))
			r = rs.fetchone()

		self.fileButton = QPushButton("Select File")
		self.fileButton.clicked.connect(self.getFile)
		self.outer.addRow("Scan Parameters", self.fileButton)
		## end of material from pre_fields_preamble.py
		self.submitted = BComboBox()
		self.submitted.addItems(["", "Y", "N"])
		self._fields['submitted'] = self.submitted
		group = self.submitted
		self.outer.addRow("Protocol Deviation submitted?", group)
		self.ispy2_id = BLineEdit()
		self._fields['ispy2_id'] = self.ispy2_id
		self.visit_number = BComboBox()
		self.visit_number.addItems(["", "1", "A3w", "A6w", "A12w", "B3w", "B6w", "B12w", "S1", "5", "2", "2.5", "3", "3.5", "4"])
		self._fields['visit_number'] = self.visit_number
		group = QGroupBox()
		box = FlowLayout()
		box.addWidget(self.ispy2_id)
		box.addWidget(self.visit_number)
		group.setLayout(box)
		self.outer.addRow("ISPY-2 ID", group)
		self._mark_automatic(self.outer, group)
		self.mri_date = BSmallDateWidget()
		self._fields['mri_date'] = self.mri_date
		group = self.mri_date
		self.outer.addRow("MRI Date", group)
		self._mark_automatic(self.outer, group)
		self.breast = BComboBox()
		self.breast.addItems(["", "r", "l"])
		self._fields['breast'] = self.breast
		group = self.breast
		self.outer.addRow("Breast", group)
		self._mark_automatic(self.outer, group)
		self.dce_compliant = BComboBox()
		self.dce_compliant.addItems(["", "Y", "N"])
		self._fields['dce_compliant'] = self.dce_compliant
		group = self.dce_compliant
		self.outer.addRow("DCE Protocol compliant", group)
		self.screen_fail = BCheckBox(self)
		self._fields['screen_fail'] = self.screen_fail
		group = self.screen_fail
		self.outer.addRow("Screen fail", group)
		self.discrep13 = BCheckBox("Motion", self, 13)
		self._fields['discrep13'] = self.discrep13
		self.discrep14 = BCheckBox("Background/Grey not 60", self, 14)
		self._fields['discrep14'] = self.discrep14
		self.discrep15 = BCheckBox("FOV outside range", self, 15)
		self._fields['discrep15'] = self.discrep15
		self.discrep16 = BCheckBox("FOV overlarge for patient", self, 16)
		self._fields['discrep16'] = self.discrep16
		self.discrep17 = BCheckBox("FOV inconsistent between visits", self, 17)
		self._fields['discrep17'] = self.discrep17
		self.discrep18 = BCheckBox("Poor fat suppression", self, 18)
		self._fields['discrep18'] = self.discrep18
		self.discrep19 = BCheckBox("Different scanner used from baseline", self, 19)
		self._fields['discrep19'] = self.discrep19
		self.discrep20 = BCheckBox("Contrast off protocol", self, 20)
		self._fields['discrep20'] = self.discrep20
		self.discrep21 = BCheckBox("Scan duration more than 5 seconds different from baseline", self, 21)
		self._fields['discrep21'] = self.discrep21
		self.discrep1 = BCheckBox("Boxing not consistent", self, 1)
		self._fields['discrep1'] = self.discrep1
		self.discrep2 = BCheckBox("Timing deviation - Auto timing", self, 2)
		self._fields['discrep2'] = self.discrep2
		self.discrep3 = BCheckBox("Scan duration off protocol", self, 3)
		self._fields['discrep3'] = self.discrep3
		self.discrep4 = BCheckBox("PE threshold not 70%", self, 4)
		self._fields['discrep4'] = self.discrep4
		self.discrep5 = BCheckBox("PE threshold not consistent", self, 5)
		self._fields['discrep5'] = self.discrep5
		self.discrep6 = BCheckBox("Late exam submission", self, 6)
		self._fields['discrep6'] = self.discrep6
		self.discrep9 = BCheckBox("Scan quality insufficient", self, 9)
		self._fields['discrep9'] = self.discrep9
		self.discrep10 = BCheckBox("Image artifact present", self, 10)
		self._fields['discrep10'] = self.discrep10
		self.deviation_late_exam_overdue = BIntEdit()
		self._fields['deviation_late_exam_overdue'] = self.deviation_late_exam_overdue
		group = QGroupBox()
		box = FlowLayout()
		box.addWidget(self.discrep13)
		box.addWidget(self.discrep14)
		box.addWidget(self.discrep15)
		box.addWidget(self.discrep16)
		box.addWidget(self.discrep17)
		box.addWidget(self.discrep18)
		box.addWidget(self.discrep19)
		box.addWidget(self.discrep20)
		box.addWidget(self.discrep21)
		box.addWidget(self.discrep1)
		box.addWidget(self.discrep2)
		box.addWidget(self.discrep3)
		box.addWidget(self.discrep4)
		box.addWidget(self.discrep5)
		box.addWidget(self.discrep6)
		box.addWidget(self.discrep9)
		box.addWidget(self.discrep10)
		box.addWidget(self.deviation_late_exam_overdue)
		group.setLayout(box)
		self.outer.addRow("If not compliant, what was deviation?\n(check all that apply)", group)
		self.volume_calculation = BComboBox()
		self.volume_calculation.addItems(["", "Possible", "Not Possible"])
		self._fields['volume_calculation'] = self.volume_calculation
		group = self.volume_calculation
		self.outer.addRow("Volume Calculation", group)
		self.site = BSiteComboBox(data=self.siteRecs)
		self._fields['site'] = self.site
		group = self.site
		self.outer.addRow("Site", group)
		self._mark_automatic(self.outer, group)
		self.tumor_volume_submitted = BLineEdit()
		self._fields['tumor_volume_submitted'] = self.tumor_volume_submitted
		group = self.tumor_volume_submitted
		self.outer.addRow("Tumor Volume Submitted", group)
		self._mark_automatic(self.outer, group)
		self.auto_timing1_min = BLineEdit()
		self._fields['auto_timing1_min'] = self.auto_timing1_min
		self.auto_timing1_sec = BLineEdit()
		self._fields['auto_timing1_sec'] = self.auto_timing1_sec
		self.auto_timing1_option = BComboBox()
		self.auto_timing1_option.addItems(["", "1", "2", "3", "4"])
		self._fields['auto_timing1_option'] = self.auto_timing1_option
		self.auto_timing2_min = BLineEdit()
		self._fields['auto_timing2_min'] = self.auto_timing2_min
		self.auto_timing2_sec = BLineEdit()
		self._fields['auto_timing2_sec'] = self.auto_timing2_sec
		self.auto_timing2_option = BComboBox()
		self.auto_timing2_option.addItems(["", "5", "6", "7", "8"])
		self._fields['auto_timing2_option'] = self.auto_timing2_option
		group = QGroupBox()
		box = FlowLayout()
		box.addWidget(self.auto_timing1_min)
		box.addWidget(self.auto_timing1_sec)
		box.addWidget(self.auto_timing1_option)
		box.addWidget(self.auto_timing2_min)
		box.addWidget(self.auto_timing2_sec)
		box.addWidget(self.auto_timing2_option)
		group.setLayout(box)
		self.outer.addRow("Auto Timing", group)
		self._mark_automatic(self.outer, group)
		self.scan_duration = BNumEdit(p=5, s=2)
		self._fields['scan_duration'] = self.scan_duration
		group = self.scan_duration
		self.outer.addRow("Scan Duration", group)
		self._mark_automatic(self.outer, group)
		self.pe_threshold = BIntEdit()
		self._fields['pe_threshold'] = self.pe_threshold
		group = self.pe_threshold
		self.outer.addRow("PE Threshold Processed", group)
		self._mark_automatic(self.outer, group)
		self.bg_grey_threshold = BLineEdit()
		self._fields['bg_grey_threshold'] = self.bg_grey_threshold
		group = self.bg_grey_threshold
		self.outer.addRow("Background/Grey Threshold", group)
		self._mark_automatic(self.outer, group)
		self.injection_rate = BCheckBox(self)
		self._fields['injection_rate'] = self.injection_rate
		group = self.injection_rate
		self.outer.addRow("Injection rate\n2cc/second", group)
		self.flush_volume = BCheckBox(self)
		self._fields['flush_volume'] = self.flush_volume
		group = self.flush_volume
		self.outer.addRow("Flush volume\n20 cc", group)
		self.final_processing_location = BComboBox()
		self.final_processing_location.addItems(["", "UCSF", "Site"])
		self._fields['final_processing_location'] = self.final_processing_location
		self.final_processing_aegis = BComboBox()
		self.final_processing_aegis.addItems(["", "AEGIS", "No AEGIS"])
		self._fields['final_processing_aegis'] = self.final_processing_aegis
		group = QGroupBox()
		box = FlowLayout()
		box.addWidget(self.final_processing_location)
		box.addWidget(self.final_processing_aegis)
		group.setLayout(box)
		self.outer.addRow("Final (official) processing done by UCSF?", group)
		self.comments = BTextEdit(self, 3, 60)
		self._fields['comments'] = self.comments
		group = self.comments
		self.outer.addRow("Comments", group)
		self.fov1 = BIntEdit()
		self._fields['fov1'] = self.fov1
		self.fov2 = BIntEdit()
		self._fields['fov2'] = self.fov2
		group = QGroupBox()
		box = FlowLayout()
		box.addWidget(self.fov1)
		box.addWidget(self.fov2)
		group.setLayout(box)
		self.outer.addRow("FOV", group)
		self._mark_automatic(self.outer, group)
		self.moco = BCheckBox(self)
		self._fields['moco'] = self.moco
		group = self.moco
		self.outer.addRow("MOCO to pre in Aegis", group)
		self.motion_brtool = BCheckBox(self)
		self._fields['motion_brtool'] = self.motion_brtool
		group = self.motion_brtool
		self.outer.addRow("Motion- brtool registration", group)
		self.report_received = BSmallDateWidget()
		self._fields['report_received'] = self.report_received
		group = self.report_received
		self.outer.addRow("Report received date", group)
		self.report_returned = BSmallDateWidget()
		self._fields['report_returned'] = self.report_returned
		group = self.report_returned
		self.outer.addRow("Report returned to site", group)
		self.submit = QPushButton('Save')
		self.getFile()  # must be after all input widgets created
		self.submit.clicked.connect(self.save)

		self.outer.addRow('', self.submit)


def launch():
	app = QApplication(sys.argv)
	form = BreastForm()
	sa = QScrollArea()
	sa.setWidgetResizable(True)
	sa.setWidget(form)
	# fSize captured immediately after form creation is not full size
	fSize = form.size()+QSize(0, 3)  # extra vertical to avoid scrollbars
	saSize = fSize.boundedTo(form.screen().availableSize())
	sa.resize(saSize)
	sa.show()

	sys.exit(app.exec())

if __name__ == '__main__':
	launch()

