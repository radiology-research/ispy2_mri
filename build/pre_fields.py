#! /usr/bin/python3

# File: pre_fields.py
# Author: Ross Boylan <ross.boylan@ucsf.edu>
# Created: 2023-07-19
# License: GPLv3 https://www.gnu.org/licenses/gpl-3.0.en.html

# Assemble list of fields for form and generate a Python program.
# This is not part of the app; it is used to generate the app.

## Inputs
#  bdb\insert\ispy2.jsp page definition of original web app
#  pre_fields.py    Start of the generated code, used literally.
#
## Outputs
#  tqt.py   or name of your choice.  The generated application.

## To Do
# recreate writing process of jsp
    # mri_code = uk -> mri_date = NULL
    # logic of java getDateString and getDateCode
    # All the following are integer or NULL
        # late_exam_overdue OK
        # site OK
        # pe_threshold OK
        # fov* OK
        # id ?there is no self.id.  ispy2_id is BLineEdit, not BIntEdit.
        #    But this may be the id returned from the query?
    # scan_duration is double or NULL OK
    # report_returned_code is uk -> report_returned_date = NULL
    # report_received_code is uk -> report_received_date = NULL

# The parameter file *may* be missing.

# Undo automatic selection of file for development
# Review for other todo comments
# Package

## For Jessica
# Name of program: ispy2_breastdb_entry?
# loss of time info on scans (MRI Date): OK
# uk use. is blank OK instead.  either fine


## Low priority: 
# addition of new site: the sites have a number which must be entered when a new one is added: could be 4 or 5 digits
# prefer upper case for breast laterality
# data entry vs data review windows: add logic and GUI to accept results and review automatic values
# Allow tab to move between fields for combobox, at least for date.  It already does, 
# but the thing to add is for it to trigger accept of existing value.  I.e., currently one must hit
# enter and then tab, would like to just hit tab.

## Done
# Add commit to db transaction
# add site numbers to site pulldown and use them for db insertion
# pull values from GUI + insert in db
# test writing None/Null to db, include None for dates
# eliminate placholder text with widget __str__
# basic write to db
# site
#      develop special adaptor, subset of BComboBox for site
#      to and from db should use number
#      from file use site name, but only if it matches
# finish reading values from text file
# check whether % is part of some fields.  It's not.
# review that isvalid and extractors are using new scheme
# for dates allow typein for year, if possible
# only 2020 and on should be drop down list
# visit and site allow typein of new values
# pull institutions from db for dropdown site.
# get preferred alternatives and order for visit

# it would be desirable in combo boxes for tab to accept the current value and move to next field
# at the moment must hit enter to accept and then tab
# tab seems to do nothing, though it might be a trigger for autocompletion
# https://stackoverflow.com/questions/48328147/how-to-select-an-item-in-a-qcombobox-using-the-tab-key
# has one approach to this, though the event filter it refers to is obsolete according to
# https://doc.qt.io/qt-6/qwidget.html#nativeEvent.  But maybe that's just for native events.
# https://doc.qt.io/qt-6/eventsandfilters.html specifically mentions the tab key and provides an
# example of overriding it in the event() method.  event() returns True if event is handled.
# Below that is a discussion of event filters.  They allow other objects to install handlers.
# and there is an example of using it to intercept tab.  eventFilter() is a method on a filter
# object.  Any QObject implementing eventFilter() is a filter, if it's installed.
# QComboBox did not have an obvious signal for "item selected", though it had several
# related signals.

## "Special Handling necessary" and "Problems loading on Aegis" also should be deleted
## there are some other things we could trim.
## site list may get additions. but it will be prepopulated.

## Design Notes
# This is a pre-processing application, hence `pre` in the name, that generates a Python
# program that provides an interactive form to log receipt of ispy2 images from study sites.
# Those functions were initially accomplished via a web application, and the file defining the 
# HMTL form is the main input of this program.

# Unlike the web application, this one attempts to fill in some information automatically
# from a user-selected file.  We generate that file as part of our routine processing.
# In fact, we generate twice, once in Aegis (or during the Aegis processin), and once from brtool.
# The duplication arose because the Aegis processing was not working for awhile.

# We have also departed from the web form in various ways.  Some fields that we haven't used
# are suppressed, and some lists of alternatives have been expanded.

# The initial parsing of the source jsp file is a little delicate, since we encounter row and
# field definitions before they are complete.  So some things we'd like to do immediately, like
# replacing the parsed values, have to wait til later, often until the Python code is generated in
# `make_Qt()`.  `Fixer` is a helper class that applies most of these tweaks.

# Note also that looking up values in the database during pre-processing, or simply setting them
# by fiat (or from the values in the jsp), is not the same as looking them up at run time in the
# generated application.  `SelectField`, defined in this file, is for values done during
# pre-processing, while `DynamicComboBox` looks up values at run time.  The latter requires 
# support in `pre_fields_preamble.py`.  There is also potentially a difference between looking
# up values when the main program starts vs looking up the values each time they are needed,
# e.g. each time a combobox pops up.  We do only the former.

# Each widget for a particular fields requires standard ways to read, write, and validate its value.
# One could make separate adaptor classes like smalltalk value-models, or maintain tables of functions
# doing the necessary operation for each field.  But it seemed easiest to built the logic into
# the widgets themselves.  Hence all concrete widget classes have a mixin `BreastWidget` from which
# they must inherit.  See the comments on that class in `pre_fields_preamble.py` for details,
# including some implementation hiccups.

# This file also has classes mirroring the widget hierarchy.  But these are not actual widgets;
# they just have the key information needed to generate the actual code.  And the mirroring classes
# do not appear in the final application.  `pre_fields_preamble.py` has the run-time widget definitions.


from collections import Counter
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
import pyodbc
import re
import sys

MYDIR = Path(__file__).parent

class Fixer:
    """Perform various special handling to modify default behavior.
    Generally involves either retrieving info from database or
    modifying field.

    Note that section is called from the parser before the section's 
    fields have been scanned, while the other methods are called
    as the output program is produced, e.g., my make_Qt.
    """
    skipDatesRE = re.compile(r"^(mri|(report_(received|returned)))_(month|day|year)$")

    def __init__(self, DSN: str):
        "set up database connection to named ODBC dataset"
        self.DSN = DSN
        self.conn = pyodbc.connect(f"DSN={self.DSN}")  #passwordless login
        self.curs = self.conn.cursor()

    def section(self, section: "Section"):
        "modify a Section if appropriate"
        if len(section.des2) == 1 and section.des2[0] == "If not compliant, what was deviation?":
            # len check to avoid repeating this if there are later lines
            return self._section_deviation(section)
        # match requires Python 3.10+
        match section.des2[0]:
            case "Report received date":
                return self._section_date(section, "report_received")
            case "Report returned to site":
                return self._section_date(section, "report_returned")
            case "MRI Date":
                return self._section_date(section, "mri_date")
            
    def _section_date(self, section: "Section", varname: str):
        "add a simple calendar date picker and call it varname"
        section.addInput(DateField(varname))

    def _section_deviation(self, section: "Section"):
        "handle deviation section"
        for r in self.curs.execute('SELECT id, deviation FROM dbo.ispy2_deviation_reason\
                   ORDER BY position ASC'):
            rid = int(r[0])
            if rid in (7, 8, 11, 12):
                # skip
                continue
            des = r[1]
            section.addInput(CustomCheck(f"discrep{rid}", f"{des}", rid))

    def section_drop(self, section: "Section"):
        """return true if entire section should be removed from interface
        Also may modify the section
        The modifications are for ones that can't be done earlier in the process"""
        if len(section.des2) == 0:
            return False
        if section.nInputs() == 1:
            inp = section.inputs[0]
            # the instance check is gauche, but avoids having to 
            # implement disableLabel for all inputs, including those
            # that are not AbstractFields
            if isinstance(inp, CheckField):
                # no point in repeating the label
                inp.disableLabel()
                # and proceed with further processing
        if section.des2[0] == "Site":
            # rewrite
            section.replaceInput(DynamicComboField("site", "siteRecs"))
            return False
        return section.des2[0] in ("Special Handling necessary (header reading, other)",
                                   "Problems loading on AEGIS" )
    
    def section_automatic(self, section: "Section"):
        "return true if we can usually get this info from file"
        if len(section.des2) == 0:
            return False
        return section.des2[0] in ("ISPY-2 ID",
                                   "MRI Date",
                                   "Breast",
                                   "Site",
                                   "Tumor Volume Submitted",
                                   "Auto Timing",
                                   "Scan Duration",
                                   "PE Threshold Processed",
                                   "Background/Grey Threshold",
                                   "FOV")
    
    def field_drop(self, fld: "AbstractField"):
        "return True if field should not appear. May also edit field."
        if fld._name == "visit_number":
            # Yes, in this order
            fld.replace_choices(["1", "A3w", "A6w", "A12w", "B3w", "B6w", "B12w",
                                 "S1", "5", "2", "2.5", "3", "3.5", "4"])
            return False
        # site needs more work and is not a LineEdit
        if fld._name in ("deviation_late_exam_overdue",
                        #"site",
                        "pe_threshold",
                        "fov1", "fov2"):
            fld.setConstruct("BIntEdit()")
            return False
        if fld._name == "scan_duration":
            fld.setConstruct("BNumEdit(p=5, s=2)")
            return False
        return self.skipDatesRE.match(fld._name) or \
            fld._name in ("deviation", "deviation_other_reason")


Fix = Fixer('breastdb-new')  # global fixer

class Section:
    """
    A single section of the table presented to the user.
    It has text on the left and input(s) on the right.
    Those inputs are one or more variables and their widget type.
    """
    def __init__(self):
        self.des2 = []  # optional additional text for description
        self.inputs = []  # controls and related info

    def addDes(self, des: str):
        #  some des have leading or trailing spaces
        des = des.strip()
        self.des2.append(des)
        Fix.section(self)

    def addInput(self, inp):
        "inp should be an AbstractField."
        self.inputs.append(inp)

    def replaceInput(self, newInp):
        """
        newInp replaces the previous input field with the same name
        """
        i0 = None
        for i, x in enumerate(self.inputs):
            if x._name == newInp._name:
                i0 = i
                break
        # deliberately raise error if no match found
        self.inputs[i0] = newInp


    def nInputs(self):
        return len(self.inputs)

    def __str__(self):
        return " | ".join(self.des2) + ": " + ("; ".join(str(x) for x in self.inputs))
    
    def make_Qt(self, ostr, leader = ""):
        if Fix.section_drop(self):
            return
        des = '\\n'.join(self.des2)  # literal \n
        vnames = [f.make_Qt(ostr, leader) for f in self.inputs if not Fix.field_drop(f)]
        if len(vnames) > 1:
            ostr.write(f'{leader}group = QGroupBox()\n')
            ostr.write(f'{leader}box = FlowLayout()\n')
            iRow = 0
            iCol = 0
            for nm in vnames:
                ostr.write(f'{leader}box.addWidget(self.{nm})\n')
                if iCol >= 3:
                    iCol = 0
                    iRow += 1
                else:
                    iCol += 1
            ostr.write(f'{leader}group.setLayout(box)\n')
        else:
            ostr.write(f'{leader}group = self.{vnames[0]}\n')
        ostr.write(f'{leader}self.outer.addRow("{des}", group)\n')
        if Fix.section_automatic(self):
            ostr.write(f'{leader}self._mark_automatic(self.outer, group)\n')
    
class AbstractField:
    "some widget on the jsp web page representing a single variable"
    def __init__(self):
        self._value = None

    def _get_value(self, attrs):
        """
        set _value with the info from the end of the attribute list
        return the remaining attributes

        Typically the value field is split into multiple attributes because of an embedded "".
        """
        r = [] # return value
        foundValue = False
        for nm, v in attrs:
            if not foundValue:
                if nm == "value":
                    foundValue = True
                    self._value = v
                else:
                    r.append((nm, v))
            else:
                # we are accumulating the rest of value
                self._value += nm
                if nm == '"':
                    self._value += nm
                if v:
                    self._value += v
        return r
    
    def _clean_name(self, nm:str) ->str :
        "return cleaned up version of nm"
        if nm.endswith("[]"):
            return nm[0:(len(nm)-2)]
        return nm
    


class TextField(AbstractField):
    def __init__(self, attrs):
        super().__init__()
        for nm, v in self._get_value(attrs):
            if nm == "type":
                assert v == "text"
            elif nm == "name":
                self._name = self._clean_name(v)
            elif nm == "maxlength":
                self._maxlength = int(v)
            elif nm == "size":
                self._size = int(v)
            else:
                assert False
        self._ctor = "BLineEdit()"

    def setConstruct(self, txt: str):
        "change type of final widget.  Include () in string"
        self._ctor = txt
    
    def __str__(self):
        return f"Text({self._name})"
    
    def make_Qt(self, ostr, leader):
        """
        Output Qt code for this input field to ostr with indicated leader.
        Defines it as a variable and return value of that variable.
        I.e., return self._name
        """
        ostr.write(f"{leader}self.{self._name} = {self._ctor}\n")
        #ostr.write(f"{leader}self.{self._name}.setPlaceholderText('{self._name}')\n")
        ostr.write(f"{leader}self._fields['{self._name}'] = self.{self._name}\n")
        return self._name
    
class TextArea(AbstractField):
    "a box of text"
    def __init__(self, attrs):
        super().__init__()
        self._wrap = False
        for nm, v in self._get_value(attrs):
            if nm == "name":
                self._name = self._clean_name(v)
            elif nm == "rows":
                self._rows = int(v)
            elif nm == "cols":
                self._cols = int(v)
            elif nm == "wrap":
                self._wrap = True
            else:
                assert False

    def __str__(self):
        return f"TextArea({self._name}, {self._rows}x{self._cols})"
    
    def make_Qt(self, ostr, leader):
        me = f"self.{self._name}"
        ostr.write(f"{leader}{me} = BTextEdit(self, {self._rows}, {self._cols})\n")
        #ostr.write(f"{leader}{me}.setPlaceholderText('{str(self)}')\n")
        ostr.write(f"{leader}self._fields['{self._name}'] = self.{self._name}\n")
        return self._name
    
class CheckField(AbstractField):
    "checkbox"
    def __init__(self, attrs):
        super().__init__()
        for nm, v in self._get_value(attrs):
            if nm == "type":
                assert v == "checkbox"
            elif nm == "name":
                self._name = self._clean_name(v)
            else:
                assert False
        self._showLabel = True  # should the box be labelled?

    def __str__(self):
        return f"CheckBox({self._name})"
    
    def disableLabel(self):
        "suppress printing of label for checkbox"
        self._showLabel = False
    
    def make_Qt(self, ostr, leader):
        if self._showLabel:
            ostr.write(f'{leader}self.{self._name} = BCheckBox("{self._name}", self)\n')
        else:
            ostr.write(f'{leader}self.{self._name} = BCheckBox(self)\n')
        ostr.write(f"{leader}self._fields['{self._name}'] = self.{self._name}\n")
        return self._name
    
class CustomCheck(AbstractField):
    """Checkbox that is not defined by parsing JSP.
    May have a name that differs from the text displayed.
    May carry an extra value.
    """
    def __init__(self, varname: str, description: str, val=None):
        super().__init__()
        self._name = varname
        self._des = description
        self._val = val

    def __str__(self):
        if self._val is None:
            return f"CustCheck({self._name}, {self._des})"
        else:
            return f"CustCheck({self._name}, {self._des}, {self._val})"
    
    def make_Qt(self, ostr, leader):
        ostr.write(f'{leader}self.{self._name} = BCheckBox("{self._des}", self')
        if self._val is not None:
            ostr.write(f', {self._val}')
        ostr.write(')\n')
        ostr.write(f"{leader}self._fields['{self._name}'] = self.{self._name}\n")
        return self._name

class SelectField(AbstractField):
    "drop-down selection box"
    def __init__(self, attrs):
        super().__init__()
        self._choices = []  # options to select
        for nm, v in self._get_value(attrs):
            if nm == "name":
                self._name = self._clean_name(v)
            else:
                assert False
        # choices filled in later

    def add_choice(self, v):
        "indicate an available choice for selection"
        self._choices.append(v)

    def replace_choices(self, v):
        "replace existing choice list with v, a new list"
        self._choices = v.copy()

    def __str__(self):
        return f"Select({self._name}: {', '.join(self._choices)})"
    
    def make_Qt(self, ostr, leader):
        ### ToDo
        ostr.write(f'{leader}self.{self._name} = BComboBox()\n')
        # trying to do next 2 lines in a single line causes a hang
        altstrings = [f'"{v}"' for v in self._choices]
        altstrings = ", ".join(altstrings)
        ostr.write(f'{leader}self.{self._name}.addItems([{altstrings}])\n')
        ostr.write(f"{leader}self._fields['{self._name}'] = self.{self._name}\n")
        return self._name

## Some Input Fields that are not derived from parsing the jsp file
## They are therefor not AbstractFields, but must behave enough like
## them to be usable.
##  They must have a _name attribute and implement make_Qt(),
## including returning name, and str()

class DateField:
    """Simple one line set of dropdowns for date
    This is not an AbstractField because it does not come from parsing
    a jsp page.
    """
    def __init__(self, varname: str):
        "this field will be known as varname"
        self._name = varname

    def __str__(self):
        return f"Date({self._name})"
    
    def make_Qt(self, ostr, leader):
        fname = self._name
        ostr.write(f'{leader}self.{fname} = BSmallDateWidget()\n')
        ostr.write(f"{leader}self._fields['{fname}'] = self.{fname}\n")
        return self._name
    
class DynamicComboField:
    """
    A combo box whose contents are looked up at run-time.
    This is currently specialized for BSiteComboBox, the only context
    for which this class is needed.
    """
    def __init__(self, varname: str, dynamic: str):
        """
        Field will be known as varname
        getattr(self, dynamic) retrieves the list of alternatives
        """
        self._name = varname
        self._dynamic = dynamic

    def __str__(self):
        return f"DynCombo({self._name}, {self._dynamic})"
    
    def make_Qt(self, ostr, leader):
        ostr.write(f'{leader}self.{self._name} = BSiteComboBox(data=self.{self._dynamic})\n')
        #ostr.write(f'{leader}self.{self._name}.addItems(self.{self._dynamic})\n')
        ostr.write(f"{leader}self._fields['{self._name}'] = self.{self._name}\n")
        return self._name
    
class JSPParser(HTMLParser):
    """
    Parse the form that I think is the basis for the current display, to extract
    the fields and textual descriptions.
    This is a jsp page, but it is mostly html.
    """
    def __init__(self):
        HTMLParser.__init__(self)
        self.sections = []
        self.parsingDescription = False
        self.currentSection = None  # the section currently under construction
        self.currentSelection = None  # SelectionField under construction

    def handle_data(self, data):
        data = data.strip()
        if len(data)  == 0:
            return
        if self.parsingDescription:
            self.currentSection.addDes(data)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "td":
            for (nm, v) in attrs:
                if nm == "class":
                    if v == "fieldName":
                        self.parsingDescription = True
                        if self.currentSection:
                            self.sections.append(self.currentSection)
                        self.currentSection = Section()
                    return
        elif tag == "input":
            nm, v = attrs[0]
            assert nm == "type"
            if v == "text":
                self.currentSection.addInput(TextField(attrs))
            elif v == "checkbox":
                self.currentSection.addInput(CheckField(attrs))
            # otherwise ignore: hidden, submit, reset
        elif tag == "select":
            self.currentSelection = SelectField(attrs)
        elif tag == "option":
            nm, v = attrs[0]
            assert nm == "value"
            self.currentSelection.add_choice(v)
        elif tag == "textarea":
            self.currentSection.addInput(TextArea(attrs))
                
    def handle_endtag(self, tag):
        "there is not always a /td, and so allow other tags to end id"
        if tag in ("td", "tr", "table"):
            self.parsingDescription = False
        elif tag == "select":
            self.currentSection.addInput(self.currentSelection)
            self.currentSelection = None
        elif tag == "html":
            if self.currentSection:
                self.sections.append(self.currentSection)
                self.currentSection = None
    
    def make_Qt(self, ostr):
        "Convert self into Qt code and output to ostr, a stream like object"
        leader = self._qpreamble(ostr)
        #self._qsamples(ostr, leader)  # for development
        for s in self.sections:
            s.make_Qt(ostr, leader)
        self._qcoda(ostr, leader)

    def _qline(self, ostr, leader:str, line:str):
        "write line to ostr, adding leader at start and \n at end"
        ostr.write(f"{leader}{line}\n")

    def _qpreamble(self, ostr, leader:str = ""):
        with (MYDIR / "pre_fields_preamble.py").open("rt") as fin:
            skip = True
            for line in fin:
                if skip:
                    skip = False
                else:
                    self._qline(ostr, leader, line.rstrip())
        return leader+"\t\t"
    
    def _qsamples(self, ostr, leader):
        "Create some sample widgets"
        self._qline(ostr, leader, "self.sampCal = QCalendarWidget()\n")
        self._qline(ostr, leader, "self.outer.addRow('sample date', self.sampCal)\n")

    def _qcoda(self, ostr, leader = ""):
        "standard file end"
        self._qline(ostr, leader, "self.visit_number.setEditable(True)")
        #self._qline(ostr, leader, "self.site.setEditable(True)") # no good way to add for now
        self._qline(ostr, leader, "self.submit = QPushButton('Save')")
        self._qline(ostr, leader, "self.getFile()  # must be after all input widgets created")
        self._qline(ostr, leader, "self.submit.clicked.connect(self.save)\n")
        self._qline(ostr, leader, "self.outer.addRow('', self.submit)\n")
        ostr.write("\n")
        self._qline(ostr, "", "def launch():")
        leader = "\t"
        self._qline(ostr, leader, "app = QApplication(sys.argv)")
        self._qline(ostr, leader, "form = BreastForm()")
        self._qline(ostr, leader,  "form.show()")
        self._qline(ostr, leader, "sys.exit(app.exec())")
        ostr.write("\n")
        self._qline(ostr, "", "if __name__ == '__main__':")
        self._qline(ostr, leader, "launch()")

def parse_jsp(sourceFile):
    """
    Parse the jsp page on which the current web input form is defined

    It would be much easier to work with a DOM, but the XML based parsers
    don't consider the sourceFile to be valid input.
    """
    parser = JSPParser()
    parser.feed(open(sourceFile, "rt").read())
    if False:
        nFields = 0
        for s in parser.sections:
            nFields += s.nInputs()
        print(f"Found {len(parser.sections)} sections with {nFields} fields.")
        for (i, des) in enumerate(parser.sections):
            print(f"{i}: {des}")
    return parser

parser = parse_jsp(MYDIR / "ispy2.jsp")
target = Path(__file__).parents[1] / "src" / "ispy2_mri" / "ispy2_mri.py"
with target.open("wt") as fout:
    parser.make_Qt(fout)
 