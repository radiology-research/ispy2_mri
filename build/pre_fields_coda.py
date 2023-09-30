		self.visit_number.setEditable(True)
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
	