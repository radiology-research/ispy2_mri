# This is a fragment for inclusion by pre_fields.py
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
		"""
		set value of widget from a textual value of v, e.g., from a text file
		Note: May throw UnexpectedInputError using v as the value
		"""
		# default implementaiton
		self.fromdb(v)

	def clear(self):
		"set to blank or initial state"
		# default implementation
		self.fromtext("")

	def isValid(self):
		"return True if I contain a valid value"
		return True
	
	### following services provided as an optional convenience
	def setError(self):
		"""
		Indicate that something is wrong with the values in this widget.
		"""
		self.setStyleSheet("* {color: red; background-color: yellow}")

	def setOK(self):
		"""
		Remove any error conditions from this widget.
		"""
		self.setStyleSheet("")

	
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

	def setMaxLength(self, n: int, char="m") -> None:
		"""
		set maximum number of characters to n.

		Additionally, resize the width to match; the superclass often
		leaves the width excessive.  Allow enough space for n copies of char.

		See https://stackoverflow.com/a/47307180 for details of the translation
		from characters to pixels.  But it seems a bit dated.

		In experiments, overriding preferredSize() seems ineffective
		"""
		super().setMaxLength(n)
		fm = self.fontMetrics()
		m = self.textMargins()
		c = self.contentsMargins()
		w = (n+1)*fm.horizontalAdvance(char)+m.left()+m.right()+c.left()+c.right()
		self.setMaximumWidth(w)

class BPctEdit(BLineEdit):
	"""
	Interprets entered values as percentages.
	Strips % from text from file.

	This is used for 2 fields: pe_threshold and bg_grey_threshold.
	Unfortunately the former is type int in database while latter is 
	type varchar.  So the first would more properly be a subclass of
	BIntEdit.
	"""
	def __init__(self, parent=None):
		super().__init__(parent)

	def fromtext(self, v: str):
		"""set a percent value into widget, removing %
		"""
		v = v.strip()
		if v[-1] == "%":
			v = v[:-1]
		super().fromtext(v)

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
		self.currentIndexChanged.connect(self.noteIndexChanged)

	def todb(self):
		return self.currentText()
	
	def setVal(self, v:str)->int :
		"""
		Set the widget to v provided it is one of the allowed values.
		Returns the index of the selection, or -1 if no match.
		Does NOT throw an error.

		The code is this specific way because others that sound as if
		they should work do not.
		setEditText() only affects the display if the widget is editable.
		Mine usually are not, but neither setEditText() nor setCurrentText()
		change the current index, despite documentation that seems to say they
		do.  Also, if there is a failure, the selection is left at the previous
		value.  This code removes the previous selection.
		"""
		i = self.findText(v)
		self.setCurrentIndex(i)
		return i
	
	def fromdb(self, v):
		self.setVal(v)

	def fromtext(self, v: str):
		if v:
			i = self.setVal(v)
		else:
			self.clear()
			# NB: do not raise exception
			return
		if i >= 0:
			# real data, successfully set
			# noteIndexedChange should be triggered automatically and clean up
			return
		# No match
		self.setError(v)

	def setError(self, v:str):
		self.setPlaceholderText(f"? {v}")
		self.setToolTip(f"Unrecognized text. Please select from drop-down.")
		super().setError()
		raise UnexpectedInputError(v)
	
	def setOK(self):
		self.setToolTip("")
		super().setOK()
		# leave placeholder text, which should be invisible	

	@Slot()
	def noteIndexChanged(self, i):
		# handling of non-selection varies by context
		# so we do nothing here
		if i < 0:
			return
		# otherwise, a valid data selection has been made
		# undo all the weird stuff
		self.setOK()


	def clear(self):
		self.setEditText("")
		self.setCurrentIndex(-1)
		self.setOK()
		self.setPlaceholderText("")


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
		self.setError(v)
		raise UnexpectedInputError(f"Unknown site id {v} read from database.")
	
	def fromtext(self, v: str):
		"v is a site name.  It probably won't be an exact match"
		for i in range(self.count()):
			r = self.itemData(i)
			if r and r[2] == v:
				self.setCurrentIndex(i)
				return
		self.setCurrentIndex(-1)
		self.setError(v)
		self.setToolTip(f"Unrecognized site. Please select from drop-down.")
		raise UnexpectedInputError(v)

class BCheckBox(QCheckBox, BreastWidget):
	def __init__(self, parent=None, asText=True, val=None):
		QCheckBox.__init__(self, parent)
		self.asText = asText
		self._val = val
		# next connection clears errors on user selection
		self.clicked.connect(self.setOK)

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

	def fromtext(self, v:str):
		v = v.lower()
		match v:
			case 'n' | 'no'| 'none':
				self.setChecked(False) # probably the default
				self.setOK()
			case 'y' | 'yes':
				self.setChecked(True)
				self.setOK()
			case _:
				self.setChecked(False)
				raise UnexpectedInputError(f"Unrecognized value {v} for checkbox")

	def clear(self):
		self.setChecked(False)

	def setError(self, v):
		super().setError()
		self.setToolTip(f"Unrecognized value {v}. Please select or not as needed.")

	@Slot()
	def setOK(self):
		self.setToolTip("")
		super().setOK()

class BAutoTimingWidget(QWidget, BreastWidget):
	"""
	Groups together 3 fields related to auto-timing.

	Unlike most other widgets, this corresponds to 3 separate fields
	in the database.  todb() returns those 3 fields in the conventional 
	order.

	When receiving info from a plain text file, a single line combines
	all 3 fields.
	"""
	def __init__(self, i:int, options, parent=None):
		"""
		i is the index indicating auto-timing 1 or 2
		options is a list of  alternative for the options widget
		"""
		super().__init__(parent)
		self.seq = i
		layout = QHBoxLayout(self)
		self._minwidg = self._makemin()
		self._secwidg = self._makesec()
		self._optionwidg = self._makeoption(options)
		layout.addWidget(self._minwidg)
		layout.addWidget(self._secwidg)
		layout.addWidget(self._optionwidg)
		# it seems the tab order is set already, but just in case
		QWidget.setTabOrder(self._minwidg, self._secwidg)
		QWidget.setTabOrder(self._secwidg, self._optionwidg)

	def _makemin(self):
		w = BLineEdit(self)
		w.setPlaceholderText("Minutes")
		w.setToolTip("Minutes")
		# on development machine the advanceWidth of any digit is 6, of m is 11
		# and the font metric's maxWith (widest character) is 32.
		w.setMaxLength(8, char="8")
		return w
	
	def _makesec(self):
		w = BLineEdit(self)
		w.setPlaceholderText("Seconds")
		w.setToolTip(("Seconds"))
		w.setMaxLength(4, char="8")
		return w
	
	def _makeoption(self, options):
		cb = BComboBox(self)
		cb.addItem("", -1)
		# hack for a value that sometimes occurs, but not in original interface
		if self.seq == 2:
			cb.addItem("4", 4)
		for x in options:
			# avoid duplicate entries for ""
			if x != "":
				cb.addItem(str(x), x)
		cb.setCurrentIndex(-1)
		return cb

	def _mydata(self):
		"generator for all my data widgets"
		yield self._minwidg
		yield self._secwidg
		yield self._optionwidg

	def clear(self):
		for w in self._mydata():
			w.clear()

	def todb(self):
		"unlike all other widgets, returns a tuple"
		return (w.todb() for w in self._mydata())
	
	def fromdb(self, v):
		raise NotImplementedError("No single database entry corresponds to auto_timing")

	timingRE = re.compile(r"(\d*):(\d+)\s+\((\d)\)")
	def fromtext(self, v: str):
		m = self.timingRE.match(v)
		if m:
			for x, w in zip(m.groups(), self._mydata()):
				w.fromtext(x)
		else:
			# really should do more
			# eg set placeholder in first field, change colors....
			raise UnexpectedInputError(v)
		
class BFOV(QWidget, BreastWidget):
	"""
	For FOV, which has 2 separate fields in the database.
	"""
	def __init__(self, parent=None):
		super().__init__(parent)
		self.fov1 = BIntEdit()
		self.fov1.setToolTip("FOV1")
		self.sep = QLabel("x")
		self.fov2 = BIntEdit()
		self.fov2.setToolTip("FOV2")
		layout = QHBoxLayout(self)
		self.setLayout(layout)
		layout.addWidget(self.fov1)
		layout.addWidget(self.sep)
		layout.addWidget(self.fov2)


	def clear(self):
		self.fov1.clear()
		self.fov2.clear()

	def todb(self):
		"returns a tuple of values for separate fields"
		return (self.fov1.todb(), self.fov2.todb())
	
	def fromdb(self, v):
		raise NotImplementedError("No single database entry corresponds to fov")
	
	FOVRE = re.compile(r"([0-9.]+)\s+x\s+([0-9.]+)")
	def fromtext(self, v: str):
		"set value like '32.0 x 32.0' into fov fields"
		m = self.FOVRE.match(v)
		if m:
			self.fov1.fromtext(m.group(1))
			self.fov2.fromtext(m.group(2))
		else:
			raise UnexpectedInputError(f"{v} value unparseable for FOV")

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
		# guide keys are line headers in text file
		# values are names of fields as strings
		guide = {
			'I-SPY ID': "ispy2_id",
		   	'Date': "mri_date",
			'Visit ID': "visit_number",
			'Institution': "site",
			'Breast': "breast", # currently needs to be v.lower()
			'Tumor Volume': "tumor_volume_submitted",
			'Early Post Timing': "auto_timing1",
			'Late Post Timing': "auto_timing2",
			'PE Threshold': "pe_threshold",
			'Scan Duration': "scan_duration",
			'Gray Threshold': "bg_grey_threshold",
			'MOCO': "moco",
			'FOV': "fov"
			}
		with path.open("rt") as fin:
			for line in fin:
				m = self.paramRE.match(line)
				if m:
					v = m.group('val')
					header = m.group('var')
					r[header] = v
					varname = guide[header]
					try:
						getattr(self, varname).fromtext(v)
					except UnexpectedInputError as e:
						pass
				elif line.strip():
					raise UnexpectedInputError(f"Can't handle mystery line: {line}")
		#print(r)
		return r
	
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
		"""return generator with values in correct order for db query
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

			# "auto_timing1_min",
			# "auto_timing1_sec",
			# "auto_timing1_option",
			# "auto_timing2_min",
			# "auto_timing2_sec",
			# "auto_timing2_option",
			# instead use
			"auto_timing1",
			"auto_timing2",

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
			# "fov1",
			# "fov2",
			# instead use
			"fov",

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
		for k in ordered_fields:
			yield from self._db_special(k)
	
	def _datecode(self, wdgt:BSmallDateWidget)->str:
		"Return an appropriate code for the date"
		if wdgt.todb():
			return 'mdy'
		return 'uk'
	
	def _db_special(self, field:str):
		"""
		yield a value to insert in the database for a field

		Because we are yielding rather than returning, must ensure only
		one yield executes.
		"""
		match field:
			# first 2 only here because lose the _date
			case 'report_received_date':
				yield self.report_received.todb()
			case 'report_returned_date':
				yield self.report_returned.todb()
			case 'report_received_code':
				yield self._datecode(self.report_received)
			case 'report_returned_code':
				yield self._datecode(self.report_returned)
			case 'mri_code':
				yield self._datecode(self.mri_date)
			case _:
				# none of special cases matched
				if field in self._fields:
					vs = self._fields[field].todb()
					if isinstance(vs, list):
						for v in vs:
							yield v
					else:
						yield vs
				else:
					yield None

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
			# when vals is a generator must use *; otherwise it's considered a single argument
			*vals
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
