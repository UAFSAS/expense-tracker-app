import sqlite3
import pandas as pd

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

""""
values = [value for category,value in data]

chart = QChart()

bar_set = QBarSet('Total')
bar_series = QBarSeries()


bar_set.append(values)
bar_series.append(bar_set)

chart.addSeries(bar_series)
chart.setAnimationOptions(QChart.SeriesAnimations)

axis_x = QBarCategoryAxis()
axis_x.append([categories for categories,value in data])
axis_x.setTitleText('Expense Category')
axis_x.setLabelsFont(font)
chart.addAxis(axis_x,Qt.AlignBottom)

axis_y = QValueAxis()
axis_y.setMax(max(values))
axis_y.setTitleText('Total')
axis_y.setLabelsFont(font)
chart.addAxis(axis_y,Qt.AlignLeft)
"""

class ExportHandler:
    def __init__(self, table_viewer_layout):
        self.table_viewer_layout = table_viewer_layout

    def export_data(self, file_format):
        current_table = self.table_viewer_layout.combobox_months.currentText()
        data = self.table_viewer_layout.get_table_data()

        if file_format == 'all':
            self.export_all_data(data)
        elif file_format == 'csv':
            self.export_to_csv(data)
        elif file_format == 'xlsx':
            self.export_to_excel(data)
        elif file_format == 'txt':
            self.export_to_text(data)

    def export_all_data(self, data):
        # Show a dialog to choose the format
        file_format, _ = QFileDialog.getSaveFileName(
            None, 'Save All Data', '', 'CSV Files (*.csv);;Excel Files (*.xlsx);;Text Files (*.txt)'
        )
        if file_format:
            if file_format.lower().endswith('.csv'):
                self.export_to_csv(data, file_format)
            elif file_format.lower().endswith('.xlsx'):
                self.export_to_excel(data, file_format)
            elif file_format.lower().endswith('.txt'):
                self.export_to_text(data, file_format)

    def export_to_csv(self, data, file_format=None):
        if not file_format:
            file_path, _ = QFileDialog.getSaveFileName(None, 'Save CSV File', '', 'CSV Files (*.csv);;All Files (*)')
        else:
            file_path = file_format

        if file_path:
            df = pd.DataFrame(data, columns=['ID', 'Details', 'Remarks', 'Out'])
            df.to_csv(file_path, index=False)
            self.table_viewer_layout.create_status_message(f'Data exported to CSV: {file_path}')

    def export_to_excel(self, data, file_format=None):
        if not file_format:
            file_path, _ = QFileDialog.getSaveFileName(None, 'Save Excel File', '', 'Excel Files (*.xlsx);;All Files (*)')
        else:
            file_path = file_format

        if file_path:
            df = pd.DataFrame(data, columns=['ID', 'Details', 'Remarks', 'Out'])
            df.to_excel(file_path, index=False, engine='openpyxl')
            self.table_viewer_layout.create_status_message(f'Data exported to Excel: {file_path}')

    def export_to_text(self, data, file_format=None):
        if not file_format:
            file_path, _ = QFileDialog.getSaveFileName(None, 'Save Text File', '', 'Text Files (*.txt);;All Files (*)')
        else:
            file_path = file_format

        if file_path:
            with open(file_path, 'w') as file:
                for row in data:
                    file.write('\t'.join(map(str, row)) + '\n')
            self.table_viewer_layout.create_status_message(f'Data exported to Text file: {file_path}')


class CategoryTable_Delegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        if index.column() == 0: # Remove selected state for column 0
            option.state &= ~QStyle.State_Selected
        super().paint(painter, option, index)

class TableView_Delegate(QStyledItemDelegate):
    # Only allow numerical/decimal values to be written to last column
    # Reject blank/empty spaces for 2nd and 3rd column
    def __init__(self, parent=None):
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        if index.column() in (1, 2, 3):  # Apply delegate to columns 1, 2, and 3
            editor = QLineEdit(parent)
            
            if index.column() == 3:  # For the "Out" column (column index 3)
                validator = QRegExpValidator(QRegExp(r'^\d+(\.\d+)?$'))
            else:  # For the second and third columns (columns 1 and 2)
                validator = QRegExpValidator(QRegExp(r'^\S.*$'))  # Reject blank/empty values

            editor.setValidator(validator)
            return editor
        else:
            return super().createEditor(parent, option, index)
class AddDataDialog_TableDelegate(QStyledItemDelegate):
    # Only allow numerical/decimal values to be written to last column
    # Reject blank/empty spaces for 2nd and 3rd column
    def __init__(self, parent=None):
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        if index.column() in (1, 2):
            editor = QLineEdit(parent)
            
            if index.column() == 2:  # For the "Amount" column (column index 2)
                validator = QRegExpValidator(QRegExp(r'^\d+(\.\d+)?$'))

            editor.setValidator(validator)
            return editor
        else:
            return super().createEditor(parent, option, index)

class AddDataDialog(QDialog):
    def __init__(self,parent=None):
        super().__init__(parent)

        self.setWindowTitle("Add Data Dialog")
        self.setGeometry(200, 200, 700, 450)
        self.categories = ['Grocery','Gas','Pharmacy', 'Food', 'Shopping', 'Others']  # To store added categories

        self.init_table()
        self.init_category_list_widget()
        self.init_ok_cancel_box()

        # Add to main Layout
        layout = QVBoxLayout()

        categoryLayout = QHBoxLayout()
        categoryLayout.addLayout(self.tableLayout,70)
        categoryLayout.addWidget(self.categoryFrame,30)

        layout.addLayout(categoryLayout)
        layout.addSpacing(30)
        layout.addWidget(self.buttonBox)

        self.setLayout(layout)
        self.addRows(5)

    def init_table(self):
        self.tableWidget = QTableWidget()
        self.tableWidget.setColumnCount(3)
        self.tableWidget.setHorizontalHeaderLabels(["Details", "Category", "Amount"])
        delegate = AddDataDialog_TableDelegate(self.tableWidget)
        self.tableWidget.setItemDelegateForColumn(2, delegate)

        toolbar = QToolBar()
        toolbar.setIconSize(QSize(24,24))

        self.rowsSpinBox = QSpinBox()
        self.rowsSpinBox.setRange(1, 1000)
        self.rowsSpinBox.setFixedWidth(180)

        self.addRowsButton = QAction(QIcon('images/go_icon.png'),'add rows',self)
        self.addRowsButton.triggered.connect(self.addRows)

        self.deleteRowsButton = QAction(QIcon('images/remove_icon.png'),'delete row(s)',self)
        self.deleteRowsButton.triggered.connect(self.deleteRows)

        self.ClearAllRowsButton = QAction(QIcon('images/delete_all_icon.png'),'clear all rows',self)
        self.ClearAllRowsButton.triggered.connect(self.clearAllRows)

        self.CopyAllRowsButton = QAction(QIcon('images/copy_icon.png'),'duplicate rows',self)
        self.CopyAllRowsButton.triggered.connect(self.copyRows)

        self.actionToggleCategories = QAction(QIcon('images/categories_icon.png'),'Toggle categories list',self,checkable=True)
        self.actionToggleCategories.triggered.connect(self.toggle_categories_layout)

        toolbar.addWidget(self.rowsSpinBox)
        toolbar.addAction(self.addRowsButton)
        toolbar.addSeparator()
        toolbar.addAction(self.deleteRowsButton)
        toolbar.addAction(self.CopyAllRowsButton)
        toolbar.addAction(self.ClearAllRowsButton)
        toolbar.addSeparator()
        toolbar.addAction(self.actionToggleCategories)

        self.tableLayout = QVBoxLayout()
        self.tableLayout.addWidget(toolbar)
        self.tableLayout.addWidget(self.tableWidget)

    def toggle_categories_layout(self):
        is_checked = self.actionToggleCategories.isChecked()
        self.categoryFrame.setVisible(is_checked)

    def clearAllRows(self):
        self.tableWidget.setRowCount(0)

    def init_ok_cancel_box(self):
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.confirmCancel)

    def keyPressEvent(self, event):
        # Ignore the Enter key event to prevent the window from closing
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            event.ignore()
        else:
            super().keyPressEvent(event)


    def init_category_list_widget(self):
        self.categoryLineEdit = QLineEdit()
        self.categoryLineEdit.returnPressed.connect(self.addCategoryToComboBox)

        self.addCategoryButton = QPushButton(icon=QIcon('images/go_icon.png'))
        self.addCategoryButton.setToolTip('Insert new category option')
        self.addCategoryButton.clicked.connect(self.addCategoryToComboBox)

        self.categoryListWidget = QListWidget()
        self.categoryListWidget.setFixedHeight(150)
        self.updateCategoryList()

        self.removeCategoryButton = QPushButton(icon=QIcon('images/remove_icon.png'))
        self.removeCategoryButton.setToolTip('Remove currently selected category option')
        self.removeCategoryButton.clicked.connect(self.removeSelectedCategory)

        self.clearAllCategoriesButton = QPushButton(icon=QIcon('images/delete_all_icon.png'))
        self.clearAllCategoriesButton.setToolTip('Clear all category options')
        self.clearAllCategoriesButton.clicked.connect(self.clearAllCategories)

        label_title = QLabel('Categories',font=QFont('Arial',9,QFont.Bold))
        image_categories = QLabel(pixmap=QPixmap('images/categories_icon.png').scaled(26,26))
        image_categories.setStyleSheet('padding :0px')

        title = QHBoxLayout()
        title.setAlignment(Qt.AlignCenter)
        title.addWidget(image_categories)
        title.addWidget(label_title)

        self.renameLineEdit = QLineEdit()
        self.renameLineEdit.setPlaceholderText("Rename to...")
        self.renameLineEdit.returnPressed.connect(self.renameSelectedCategory)

        self.renameCategoryButton = QPushButton(icon=QIcon('images/rename_icon.png'))
        self.renameCategoryButton.clicked.connect(self.renameSelectedCategory)


        # Add to layouts
        self.categoryFrameLayout = QVBoxLayout()

        self.categoryFrameLayout.addLayout(title)

        addCategoryLayout = QHBoxLayout()
        addCategoryLayout.addWidget(self.categoryLineEdit)
        addCategoryLayout.addWidget(self.addCategoryButton)
        self.categoryFrameLayout.addLayout(addCategoryLayout)


        listwidgetlayout = QHBoxLayout()
        self.categoryFrameLayout.addLayout(listwidgetlayout)

        listwidgetlayout.addWidget(self.categoryListWidget)

        editCategoryLayout = QVBoxLayout()
        editCategoryLayout.setAlignment(Qt.AlignTop)

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setLineWidth(3)

        editCategoryLayout.addWidget(separator)
        editCategoryLayout.addWidget(self.clearAllCategoriesButton)
        editCategoryLayout.addWidget(self.removeCategoryButton)
        listwidgetlayout.addLayout(editCategoryLayout)


        renameCategoryLayout = QHBoxLayout()
        renameCategoryLayout.addWidget(self.renameLineEdit)
        renameCategoryLayout.addWidget(self.renameCategoryButton)
        self.categoryFrameLayout.addLayout(renameCategoryLayout)

        # Add a stretchable spacer to push the widgets to the top
        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.categoryFrameLayout.addSpacerItem(spacer)

        self.categoryFrame = QWidget()
        self.categoryFrame.setLayout(self.categoryFrameLayout)
        self.toggle_categories_layout()

    def TableData(self):
        data = []
        for row in range(self.tableWidget.rowCount()):
            details = self.tableWidget.item(row, 0).text()
            categoryComboBox = self.tableWidget.cellWidget(row, 1)
            category = categoryComboBox.currentText()

            amount = self.tableWidget.item(row, 2).text()

            try:
                amount = '{0:.2f}'.format(float(amount))
            except:
                amount = '{0:.2f}'.format(float('0'))

            if category:
                data.append([details, category, amount])
        return data

    def renameSelectedCategory(self):
        new_name = self.renameLineEdit.text().strip()
        selected_item = self.categoryListWidget.currentItem()

        if selected_item:
            old_name = selected_item.text()
            if new_name.lower() not in [item.lower() for item in self.categories if item.lower() != old_name.lower()]:

                # Clear rename line edit
                self.renameLineEdit.clear()

                # Update categories list
                index = self.categories.index(old_name)
                self.categories[index] = new_name

                # Update List Widget
                self.updateCategoryList()

                # Update comboboxes in the table
                for row in range(self.tableWidget.rowCount()):
                    combobox = self.tableWidget.cellWidget(row,1)
                    current_index = combobox.currentIndex()
                    combobox.clear()
                    combobox.addItem('')
                    combobox.addItems(self.categories)
                    combobox.setCurrentIndex(current_index)
                    if old_name.lower() == combobox.currentText().lower():
                        combobox.setCurrentText(new_name)

               
    def copyRows(self):
        selected_rows = set(index.row() for index in self.tableWidget.selectedItems())

        for row in sorted(selected_rows, reverse=True):
            current_row_count = self.tableWidget.rowCount()

            # Insert a new row below the selected row
            self.tableWidget.insertRow(row + 1)

            # Copy data from the selected row to the new row
            for col in range(self.tableWidget.columnCount()):
                item = self.tableWidget.item(row, col)
                if item:
                    new_item = QTableWidgetItem(item.text())
                    self.tableWidget.setItem(row + 1, col, new_item)

                widget = self.tableWidget.cellWidget(row, col)
                if widget:
                    if isinstance(widget, QComboBox):
                        new_widget = QComboBox()
                        new_widget.addItem("")  # Add a blank item
                        new_widget.addItems(self.categories)
                        new_widget.setCurrentText(widget.currentText())
                        self.tableWidget.setCellWidget(row + 1, col, new_widget)


    def deleteRows(self):
        selected_rows = set(index.row() for index in self.tableWidget.selectedItems())
        for row in sorted(selected_rows, reverse=True):
            self.tableWidget.removeRow(row)

    def confirmCancel(self):
        # Show a confirmation dialog before closing
        reply = QMessageBox.question(self,'Confirmation','Close dialog? Unsaved changes will be lost.',QMessageBox.Yes | QMessageBox.No,QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.reject()  # Close the dialog

    def addRows(self,num=None):
        if num:
            num_rows = num
        else:
            num_rows = self.rowsSpinBox.value()
        
        # Disable updates to improve performance during bulk insertion
        self.tableWidget.setUpdatesEnabled(False)

        try:
            current_row_count = self.tableWidget.rowCount()
            self.tableWidget.setRowCount(current_row_count + num_rows)

            for row in range(current_row_count, current_row_count + num_rows):
                categoryComboBox = QComboBox()
                categoryComboBox.addItem("")  # Set default value to blank
                categoryComboBox.addItems(self.categories)  # Populate with added categories

                self.tableWidget.setItem(row, 0, QTableWidgetItem(""))
                self.tableWidget.setCellWidget(row, 1, categoryComboBox)
                self.tableWidget.setItem(row, 2, QTableWidgetItem(""))
        finally:
            # Enable updates after bulk insertion
            self.tableWidget.setUpdatesEnabled(True)

    def addCategoryToComboBox(self):
        category = self.categoryLineEdit.text().strip()

        if not category:
            return

        # Check if a case-insensitive match already exists
        if any(existing_category.lower() == category.lower() for existing_category in self.categories):
            pass
        else:
            # Add the new category
            self.categories.append(category)
            self.categoryLineEdit.clear()
            self.updateCategoryList()
            self.updateComboBoxes()

    def updateComboBoxes(self):
        for row in range(self.tableWidget.rowCount()):
            categoryComboBox = self.tableWidget.cellWidget(row, 1)
            current_text = categoryComboBox.currentText()
            categoryComboBox.clear()
            categoryComboBox.addItem("")  # Set default value to blank
            categoryComboBox.addItems(self.categories)
            if current_text in self.categories:
                categoryComboBox.setCurrentText(current_text)

    def clearAllCategories(self):
        self.categories = []
        self.updateCategoryList()
        self.updateComboBoxes()

    def removeSelectedCategory(self):
        selected_items = self.categoryListWidget.selectedItems()
        for item in selected_items:
            category = item.text()
            if category in self.categories:
                self.categories.remove(category)

        self.updateCategoryList()
        self.updateComboBoxes()

    def updateCategoryList(self):
        self.categoryListWidget.clear()
        self.categoryListWidget.addItems(self.categories)


class Dialog_AddRow(QDialog):
    # ADDING ALGORITHM WORKS!!!
    # Change the way how the program highlights the errors
    # Make it more user friendly
    # Buttons: Copy,Paste,Cut,Import,undo,redo
    # Font size spinbox

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Enter Data")
        self.resize(400,400)
        self.layout = QVBoxLayout()


        self.text_edit = QTextEdit(self)
        self.text_edit.setStyleSheet('font-size: 20px')

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal,
            self
        )
        self.layout.addWidget(self.text_edit)
        self.layout.addWidget(self.buttons)

        self.buttons.accepted.connect(self.validate_and_accept)
        self.buttons.rejected.connect(self.reject)

        self.setLayout(self.layout)

    def validate_and_accept(self):
        # details,category,amount
        # details : can be NULL
        # category : cannot be NULL
        # amount: cannot be NULL, decimal/integer value ONLY

        data = self.text_edit.toPlainText()

        # Split all rows including empty ones
        rows = [row.split(',') for row in data.split('\n')]

        # Filter out empty lines for error highlighting
        error_rows = [i for i, row in enumerate(rows) if row and row != [''] and (len(row) != 3 or not row[1].strip() or not self.is_float(row[2].strip()))]

        if error_rows:
            self.highlight_error_rows(error_rows)
        else:
            self.accept()

    def highlight_error_rows(self,error_rows):
        cursor = self.text_edit.textCursor()
        cursor.setPosition(0, QTextCursor.MoveAnchor)
        cursor.setPosition(self.text_edit.document().characterCount() - 1, QTextCursor.KeepAnchor)
        fmt = QTextCharFormat()
        fmt.setBackground(QColor())
        cursor.mergeCharFormat(fmt)

        for row in error_rows:
            start_pos = self.text_edit.document().findBlockByLineNumber(row).position()
            cursor.setPosition(start_pos)
            cursor.movePosition(QTextCursor.EndOfBlock, QTextCursor.KeepAnchor)
            fmt = QTextCharFormat()
            fmt.setBackground(QColor(255, 0, 0, 100))
            cursor.mergeCharFormat(fmt)


    @staticmethod
    def is_float(value):
        try:
            float(value)
            return True
        except ValueError:
            return False


class DatabaseManager:
    def __init__(self):
        self.connection = None
        self.cursor = None

    def open_database(self, file_path):
        if self.connection:
            self.connection.close()

        try:
            self.connection = sqlite3.connect(file_path)
            self.cursor = self.connection.cursor()
        except sqlite3.Error as e:
            print("Error: Couldn't open database.", e)

    def Tables(self):
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        return [i[0] for i in (self.cursor.fetchall())]

    def close_database(self):
        if self.connection:
            self.connection.commit()
            self.connection.close()
            self.connection = None
            self.cursor = None

    def delete_all(self,table):
        self.cursor.execute(f'DELETE FROM {table};')
        self.connection.commit()

    def execute_query(self, query, parameters=None):

        try:
            with self.connection:
                self.cursor.execute(query,parameters)
            return True
        except sqlite3.Error:
            return False

    def fetch_all(self, query):
        try:
            with self.connection:
                self.cursor.execute(query)
                return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(e)

    def print_table(self, table_name):
        try:
            query = f'SELECT * FROM {table_name};'
            result = self.fetch_all(query)

            if result:
                column_names = [description[0] for description in self.cursor.description]
                print("\t".join(column_names))
                for row in result:
                    print("\t".join(str(value) for value in row))
            else:
                print(f"No data in table {table_name}")

        except sqlite3.Error as e:
            print(f"Error printing table {table_name}: {e}")

def Capitalize(string):
    words = string.split()
    words = ' '.join(words)
    output = words.title()
    return output
    