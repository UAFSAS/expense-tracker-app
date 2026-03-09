import sys
import re

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtChart import *

from utilities import DatabaseManager, Capitalize, ExportHandler, \
                    TableView_Delegate, AddDataDialog, CategoryTable_Delegate

import breeze_resources # light and dark mode

class MonthlyCostsViewer(QWidget):
    def __init__(self,external_widgets=None):

        super().__init__()

        # Initialize databases and variables
        self.db_manager = DatabaseManager()
        self.db_manager.open_database('app_data.db')

        self.category_view_widget = external_widgets
        self.export_handler = ExportHandler(self)

        self.table_names = self.db_manager.Tables()
        self.sort_order = Qt.DescendingOrder  # Default to descending order
        self.filter_texts = {}

        self.init_ui()

    def init_expenses_table(self):
        self.table_monthlyexpenses = QTableWidget(self)
        self.table_monthlyexpenses.setColumnCount(4)
        self.table_monthlyexpenses.itemChanged.connect(self.item_changed)

    def init_ui(self):

        # Layouts
        self.table_layout = QVBoxLayout()
        self.buttons_toolbar_layout = QToolBar()

        # Create table
        self.init_expenses_table()

        # widgets outside this widget ##############################################################################

        self.text_label = QLabel('Months:')
        self.text_label.setFont(QFont('Arial',9,QFont.Bold))

        self.combobox_months = QComboBox()
        self.combobox_months.currentIndexChanged.connect(self.load_table_data)
        self.combobox_months.addItems(self.table_names)
        self.combobox_months.currentIndexChanged.connect(self.update_total_label)
        self.combobox_months.setFixedHeight(37)


        # Toolbar for table ########################################################################################
        self.buttons_toolbar_layout.setIconSize(QSize(24,24))
        self.buttons_toolbar_layout.setStyleSheet("QToolBar { spacing: 0px; }")

        self.create_toolbar_action('remove_icon.png','Delete',self.delete_row,self.buttons_toolbar_layout)
        self.create_toolbar_action('add_icon.png','Add',self.add_rows,self.buttons_toolbar_layout)
        self.create_toolbar_action('copy_icon.png','Duplicate',self.copy_selected_rows,self.buttons_toolbar_layout)
        self.create_toolbar_action('delete_all_icon.png','Clear entire table',self.clear_table,self.buttons_toolbar_layout)
        self.buttons_toolbar_layout.addSeparator()
        self.create_toolbar_action('clear_filters_icon.png','Reset filters',self.clear_table_filters,self.buttons_toolbar_layout)
        self.create_toolbar_action('clear_sorting_icon.png','Reset order of rows to default',self.clear_sorting,self.buttons_toolbar_layout)
        self.buttons_toolbar_layout.addSeparator()

        self.toggle_replace_action = QAction(QIcon('images/search_icon.png'),'Toggle search and replace toolbar', self,checkable=True)
        self.toggle_replace_action.triggered.connect(self.toggle_replace_layout)
        self.buttons_toolbar_layout.addAction(self.toggle_replace_action)

        self.buttons_toolbar_layout.addSeparator()
        self.create_toolbar_action('export_icon.png','Download expense data',lambda: self.export_handler.export_data('all'),self.buttons_toolbar_layout)

        # Add widgets to main table layout #####################################################################
        self.create_total_label()
        self.table_layout.addWidget(self.buttons_toolbar_layout)
        self.table_layout.addWidget(self.table_monthlyexpenses)
        self.init_replace_layout()
        self.init_status_label()

        self.setLayout(self.table_layout)


    def toggle_replace_layout(self):
        is_checked = self.toggle_replace_action.isChecked()
        self.replace_widget.setVisible(is_checked)

    def create_status_message(self,message):
        self.status_bar.showMessage(message,5000)

    def init_status_label(self):
        self.status_bar = QStatusBar()
        self.table_layout.addWidget(self.status_bar)

    def create_total_label(self):
        frame = QFrame()
        frame_layout = QVBoxLayout(frame)

        self.label_monthlytotal = QLabel()
        self.label_monthlytotal.setAlignment(Qt.AlignCenter)
        frame_layout.addWidget(self.label_monthlytotal)
        frame.setLayout(frame_layout)

        frame.setStyleSheet('''
            QFrame 
            {
                background-color: #008FEC; /* Set the background color */
                border-radius: 10px; /* Set the border radius for rounded corners */
            }

            QLabel {
                color: #FFFFFF; /* Set text color */
                font-size: 15px; /* Set the font size to 18 pixels */
                font-family: Arial, sans-serif; /* Set the font family */
                font-weight: bold; /* Set the font weight to bold */
            }
        ''')

        self.table_layout.addWidget(frame)
        self.update_total_label()

    def clear_sorting(self):
        if self.table_monthlyexpenses.rowCount()>0:
            col_index = 0
            setattr(self,'sort_order_0',Qt.AscendingOrder)

            self.sort_table(col_index)

            sort_btn = self.table_monthlyexpenses.cellWidget(0, col_index)
            sort_btn.setIcon(QIcon('images/sort_icon.png'))

    def create_label(self,text,stylesheet,layout):
        label = QLabel()
        label.setText(text)
        label.setStyleSheet(stylesheet)
        layout.addWidget(label)

    def create_toolbar_action(self,icon_path,tooltip,function,toolbar):

        action = QAction(QIcon(f'images/{icon_path}'),tooltip,self)

        if function:
            action.triggered.connect(function)


        if tooltip == 'Download expense data':
            month = self.combobox_months.currentText()
            data = self.get_table_data()

            menu = QMenu()

            export_csv_action = QAction('CSV File', menu)
            export_csv_action.triggered.connect(lambda: self.export_handler.export_data('csv'))

            export_excel_action = QAction('Excel File', menu)
            export_excel_action.triggered.connect(lambda: self.export_handler.export_data('xlsx'))

            export_text_action = QAction('Text File', menu)
            export_text_action.triggered.connect(lambda: self.export_handler.export_data('txt'))

            menu.addAction(export_csv_action)
            menu.addAction(export_excel_action)
            menu.addAction(export_text_action)
            action.setMenu(menu)
        toolbar.addAction(action)

    def init_replace_layout(self):
        replace_layout = QVBoxLayout()
        replace_layout.setSpacing(5)

        f_layout = QHBoxLayout()
        r_layout = QHBoxLayout()

        # Search entry ##############################################################################
        self.lineEdit_search = QLineEdit()
        self.lineEdit_search.setPlaceholderText('Search...')
        self.lineEdit_search.setClearButtonEnabled(True)
        self.lineEdit_search.setFixedHeight(30)
        self.lineEdit_search.textChanged.connect(self.searchTable)

        options = QAction(QIcon('images/search_icon.png'),'Search Options',self.lineEdit_search)
        dropdown_menu = QMenu()

        self.whole_text_action = QAction('Whole Text', dropdown_menu, checkable=True)
        self.whole_text_action.triggered.connect(lambda: self.searchTable(self.lineEdit_search.text()))
        dropdown_menu.addAction(self.whole_text_action)

        self.case_sensitive_action = QAction('Case Sensitive', dropdown_menu, checkable=True)
        self.case_sensitive_action.triggered.connect(lambda: self.searchTable(self.lineEdit_search.text()))
        dropdown_menu.addAction(self.case_sensitive_action)

        options.setMenu(dropdown_menu)
        self.lineEdit_search.addAction(options, QLineEdit.LeadingPosition)

        # Replace entry ##############################################################################
        self.lineEdit_replace = QLineEdit()
        self.lineEdit_replace.setPlaceholderText('Replace with...')
        self.lineEdit_replace.setClearButtonEnabled(True)
        self.lineEdit_replace.setFixedHeight(30)

        self.combobox_months.currentIndexChanged.connect(lambda: self.lineEdit_search.setText(''))
        self.combobox_months.currentIndexChanged.connect(lambda: self.lineEdit_replace.setText(''))
        
        btn_apply = QPushButton()
        btn_apply.setIcon(QIcon('images/go_icon.png'))
        btn_apply.setIconSize(QSize(20,20))
        btn_apply.setToolTip('Go')
        btn_apply.clicked.connect(self.replace_words)

        btn_clear = QPushButton()
        btn_clear.setIcon(QIcon('images/remove_icon.png'))
        btn_clear.setIconSize(QSize(22,22))
        btn_clear.setToolTip('Clear search and replace entries')
        btn_clear.clicked.connect(lambda:self.lineEdit_search.setText(''))
        btn_clear.clicked.connect(lambda:self.lineEdit_replace.setText(''))

        f_layout.addWidget(self.lineEdit_search)
        r_layout.addWidget(self.lineEdit_replace)
        r_layout.addWidget(btn_apply)
        r_layout.addWidget(btn_clear)

        replace_layout.addLayout(f_layout)
        replace_layout.addLayout(r_layout)

        # Add to main layout
        self.replace_widget = QWidget()
        self.replace_widget.setLayout(replace_layout)
        self.table_layout.addWidget(self.replace_widget)

        self.toggle_replace_layout()

    def replace_words(self):
        search_text = self.lineEdit_search.text()
        replacement_text = self.lineEdit_replace.text()

        whole_text_search = self.whole_text_action.isChecked()
        case_sensitive = self.case_sensitive_action.isChecked()
        
        if (search_text and replacement_text) or (search_word and replace_word):
            msg = QMessageBox.question(self, 'Confirmation', f'Replace  \"{search_text}\"\nwith \"{replacement_text}\"?')
            if msg == QMessageBox.Yes:

                # Iterate through all rows and columns
                for row in range(1, self.table_monthlyexpenses.rowCount()):
                    for col in range(self.table_monthlyexpenses.columnCount()):
                        item = self.table_monthlyexpenses.item(row, col)

                        if item and search_text:
                            item_text = item.text()

                            # Update search_function based on new search options
                            if whole_text_search:
                                search_function = lambda x, y: x == y if case_sensitive else x.lower() == y.lower()
                            else:
                                search_function = lambda x, y: y.find(x) != -1 if case_sensitive else y.lower().find(x.lower()) != -1

                            if search_function(search_text, item_text):
                                item.setText(replacement_text)
                                item.setBackground(QBrush())  # Reset background color

    def searchTable(self, search_text):
        self.clear_table_filters()
        self.table_monthlyexpenses.blockSignals(True)

        # Apply the updated search options
        whole_text_search = self.whole_text_action.isChecked()
        case_sensitive = self.case_sensitive_action.isChecked()

        if whole_text_search:
            search_pattern = QRegExp(f"\\b{re.escape(search_text)}\\b", Qt.CaseInsensitive if not case_sensitive else Qt.CaseSensitive)
        else:
            search_pattern = QRegExp(search_text, Qt.CaseInsensitive if not case_sensitive else Qt.CaseSensitive, QRegExp.FixedString)

        for row in range(1, self.table_monthlyexpenses.rowCount()):
            for col in range(self.table_monthlyexpenses.columnCount()):
                item = self.table_monthlyexpenses.item(row, col)
                if search_text:
                    if search_pattern.indexIn(item.text()) != -1:
                        item.setBackground(QBrush(QColor(255, 255, 190)))  # Yellow background for matching items
                    else:
                        item.setBackground(QBrush())  # Reset background color
                else:
                    item.setBackground(QBrush())  # Reset background color when search is empty
        self.table_monthlyexpenses.blockSignals(False)

    def clear_table_filters(self):
        for col in range(1, self.table_monthlyexpenses.columnCount()):
            filter_line_edit = self.table_monthlyexpenses.cellWidget(0, col)
            if isinstance(filter_line_edit, QLineEdit):
                filter_line_edit.clear()

    def load_table_data(self):
        self.table_monthlyexpenses.blockSignals(True)

        # Clear existing data
        self.table_monthlyexpenses.clear()
        self.table_monthlyexpenses.setRowCount(0)

        # Display headers
        self.table_monthlyexpenses.setHorizontalHeaderLabels(['#', 'Details', 'Category', 'Amount (RM)'])

        # Fetch data from database table
        selected_table = self.combobox_months.currentText()
        data_query = f"SELECT * FROM {selected_table};"
        data = self.db_manager.fetch_all(data_query)

        if data:

            # Add filter line edits to first row
            self.init_table_filters()

            # Add data
            for row, record in enumerate(data,start=1):
                self.table_monthlyexpenses.insertRow(row)
                for col, value in enumerate(record):
                    item = self.create_table_item(col, value)
                    self.table_monthlyexpenses.setItem(row, col, item)

        self.apply_table_settings()
        self.table_monthlyexpenses.blockSignals(False)
        

    def update_filter(self, column, text):
        # Update the filter text for the specified column
        self.filter_texts[column] = text

        # Apply the filters using the stored filter texts
        self.apply_filters()

    def apply_filters(self):

        self.table_monthlyexpenses.blockSignals(True)

        for row in range(1, self.table_monthlyexpenses.rowCount()):
            visible = True
            for col in range(1, self.table_monthlyexpenses.columnCount()):
                item = self.table_monthlyexpenses.item(row, col)
                if item:
                    filter_text = self.filter_texts.get(col, '')
                    if filter_text and filter_text.lower() not in item.text().lower():
                        visible = False
                        break

            self.table_monthlyexpenses.setRowHidden(row, not visible)

        self.table_monthlyexpenses.blockSignals(False)

    def create_table_item(self,column_position,value):
        if column_position == 3:
            return QTableWidgetItem('{0:.2f}'.format(float(value)))
        else:
            return QTableWidgetItem(str(value).strip())

    def update_total_label(self):
        column_index = 3
        column_sum = sum(
            float(self.table_monthlyexpenses.item(row, column_index).text()) if self.table_monthlyexpenses.item(row, column_index) is not None else 0
            for row in range(self.table_monthlyexpenses.rowCount())
        )

        self.label_monthlytotal.setText(f'RM {column_sum:.2f}')




    def item_changed(self,item):

        # Retrieve items to be saved
        current_table = self.combobox_months.currentText()
        column_name = [column[1] for column in (self.db_manager.fetch_all(f'PRAGMA table_info({current_table})'))][item.column()]
        row_id = self.table_monthlyexpenses.item(item.row(),0).text()
        new_value = item.text()

        if item.column() == 3:
            value = '{0:.2f}'.format(float(new_value))
            item.setText(value)
        else:   
            item.setText(new_value.strip())

        # Save to database table
        update_query = f'UPDATE {current_table} SET {column_name} = ? WHERE ID = ?'
        self.db_manager.execute_query(update_query, (new_value, row_id))

        self.category_view_widget.update_category_totals(self.combobox_months.currentText())
        self.update_total_label()


    def copy_selected_rows(self):
        selected_rows = set(item.row() for item in self.table_monthlyexpenses.selectedItems())

        if selected_rows:
            # Copy and save selected rows to the database
            current_table = self.combobox_months.currentText()

            # Get the current maximum index in the table
            current_max_index = self.max_value()

            # Iterate through the selected rows
            for row_index in selected_rows:
                # Insert a new row at the end of the table
                self.table_monthlyexpenses.insertRow(self.table_monthlyexpenses.rowCount())

                # Set the item in the first column (ID) with a new index value
                self.table_monthlyexpenses.setItem(
                    self.table_monthlyexpenses.rowCount() - 1, 0,
                    self.create_table_item(0, str(current_max_index + 1))
                )

                # Set items in the remaining columns based on the selected row
                for col_index in range(1, self.table_monthlyexpenses.columnCount()):
                    item = self.table_monthlyexpenses.item(row_index, col_index)
                    if item:
                        self.table_monthlyexpenses.setItem(
                            self.table_monthlyexpenses.rowCount() - 1, col_index,
                            self.create_table_item(col_index, item.text())
                        )
                current_max_index += 1

            # Save the changes to the database
            new_data = self.get_table_data()

            update_query = f'INSERT INTO {current_table} (id, Details, Remarks, Out) VALUES (?,?,?,?)'

            for row in new_data[-len(selected_rows):]:
                self.db_manager.execute_query(update_query, row)

            self.category_view_widget.update_category_totals(self.combobox_months.currentText())
            self.update_total_label()
            self.create_status_message('Row(s) copied')


    def delete_row(self):
        current_table = self.combobox_months.currentText()
        selected_rows = set(item.row() for item in self.table_monthlyexpenses.selectedItems())

        if selected_rows:
            # Select rows to indicate
            self.table_monthlyexpenses.setSelectionMode(QAbstractItemView.MultiSelection)
            for i in self.table_monthlyexpenses.selectedItems():
                self.table_monthlyexpenses.selectRow(i.row())

            # Confirmation
            msg = QMessageBox.question(self, 'Confirmation', 'Delete selected row(s)?')

            if msg == QMessageBox.Yes:
                # Delete and save changes to the database
                row_ids = [self.table_monthlyexpenses.item(row, 0).text() for row in selected_rows]
                delete_query = f'DELETE FROM {current_table} WHERE ID IN ({",".join("?" for _ in row_ids)})'
                self.db_manager.execute_query(delete_query, tuple(row_ids))

                # Remove selected rows from the table without reloading the entire data
                for row in sorted(selected_rows, reverse=True):
                    self.table_monthlyexpenses.removeRow(row)

                self.create_status_message('Row(s) successfully removed')

            self.table_monthlyexpenses.setSelectionMode(QAbstractItemView.ExtendedSelection)

            # Update category totals after deletion
            self.category_view_widget.update_category_totals(self.combobox_months.currentText())
            self.update_total_label()


    def clear_table(self):
        current_table = self.combobox_months.currentText()
        msg = QMessageBox.question(self,'Confirmation','Clear Table?')
        if msg == QMessageBox.Yes:
            self.table_monthlyexpenses.setRowCount(0)
            self.db_manager.delete_all(current_table)
            self.category_view_widget.update_category_totals(self.combobox_months.currentText())
            self.update_total_label()
            self.create_status_message('Expense history successfully cleared')


    def add_rows(self):
        # Create an instance of Dialog_AddRow
        dialog = AddDataDialog(self)

        # Display the dialog and wait for the user's response
        if dialog.exec_() == QDialog.Accepted:

            # Extract the data from the dialog
            rows = dialog.TableData()

            # Get the current maximum index in the table
            current_max_index = self.max_value()

            # Add filter line edits to the first row if the table is empty
            if rows:
                if not self.table_monthlyexpenses.rowCount():
                    self.init_table_filters()

            # Iterate through the rows obtained from user input
            for row_index, row in enumerate(rows):
                self.table_monthlyexpenses.insertRow(self.table_monthlyexpenses.rowCount()) # Insert a new row at the end of the table

                # Set the item in the first column (ID) with a new index value
                self.table_monthlyexpenses.setItem(
                    self.table_monthlyexpenses.rowCount() - 1, 0,
                    self.create_table_item(0, str(current_max_index + row_index + 1))
                )

                # Set items in the remaining columns based on user input
                for col_index, col in enumerate(row, start=1):
                    self.table_monthlyexpenses.setItem(
                        self.table_monthlyexpenses.rowCount() - 1, col_index,
                        self.create_table_item(col_index, col)
                    )

            # Save the changes to the database
            current_table = self.combobox_months.currentText()
            new_data = self.get_table_data()

            update_query = f'INSERT INTO {current_table} (id, Details, Remarks, Out) VALUES (?,?,?,?)'

            for row in new_data:
                self.db_manager.execute_query(update_query, row)

            self.category_view_widget.update_category_totals(current_table)
            self.update_total_label()
            self.create_status_message('Expenses successfully added')


    def max_value(self):
        max_value = max((int(self.table_monthlyexpenses.item(row, 0).text()) for row in range(1, self.table_monthlyexpenses.rowCount())), default=0)

        column_index = 0
        values = [int(self.table_monthlyexpenses.item(row, column_index).text())
                for row in range(1, self.table_monthlyexpenses.rowCount())
                if self.table_monthlyexpenses.item(row, column_index) is not None]

        try:
            max_value = max(values)
        except:
            max_value = 0

        return max_value

    def sort_table(self, column):
        self.table_monthlyexpenses.blockSignals(True)

        # Reset the icons of non-focused sort buttons
        for col in range(4):
            if (col not in [1,2]):
                if col != column:
                    sort_btn = self.table_monthlyexpenses.cellWidget(0, col)
                    sort_btn.setIcon(QIcon('images/sort_icon.png'))

        # Get all items the VISIBLE from the table, if filter is applied

        filter_text = self.table_monthlyexpenses.cellWidget(0, column).text()

        items = []
        for row in range(1, self.table_monthlyexpenses.rowCount()):
            item = self.table_monthlyexpenses.item(row, column)
            if not self.table_monthlyexpenses.isRowHidden(row):
                data = (item.text(), [self.table_monthlyexpenses.item(row, col).text() for col in range(self.table_monthlyexpenses.columnCount())])
                items.append(data)
        
        # Sorting
        if items and all(float(value) is not None for value, _ in items):
            items.sort(key=lambda x: float(x[0]), reverse=(getattr(self, f'sort_order_{column}') == Qt.DescendingOrder))
        else:
            items.sort(key=lambda x: x[0], reverse=(getattr(self, f'sort_order_{column}') == Qt.DescendingOrder))

        # Toggle the sorting order for the next sort
        setattr(self, f'sort_order_{column}', Qt.AscendingOrder if getattr(self, f'sort_order_{column}') == Qt.DescendingOrder else Qt.DescendingOrder)

        # Update the sort button icon based on the current sort order
        sort_btn = self.table_monthlyexpenses.cellWidget(0, column)
        sort_btn.setIcon(QIcon('images/up.png' if getattr(self, f'sort_order_{column}') == Qt.AscendingOrder else 'images/down.png'))

        # Sorts the table
        for new_row, (_, row_data) in enumerate(items, start=1):
            for col, value in enumerate(row_data):
                # Clone the item to avoid ownership conflict
                item_clone = QTableWidgetItem(value)
                self.table_monthlyexpenses.setItem(new_row, col, item_clone)

        # Explicitly apply filters after sorting
        self.apply_filters()

        self.table_monthlyexpenses.blockSignals(False)

    def init_table_filters(self):

        def init_text_filters(col):
            filter_line_edit = QLineEdit(self)
            filter_line_edit.setPlaceholderText("Filter...")
            filter_line_edit.setClearButtonEnabled(True)
            filter_line_edit.addAction(QIcon('images/filter_icon.png'), QLineEdit.LeadingPosition)
            filter_line_edit.textChanged.connect(lambda text, col=col: self.update_filter(col, text))
            self.table_monthlyexpenses.setCellWidget(0, col, filter_line_edit)

        def create_sort_button(col):
            sort_btn = QPushButton()
            sort_btn.setIcon(QIcon('images/sort_icon.png'))
            sort_btn.setToolTip('Sort values')
            sort_btn.setIconSize(QSize(20, 20))
            sort_btn.clicked.connect(lambda checked, col=col: self.sort_table(col))
            self.table_monthlyexpenses.setCellWidget(0, col, sort_btn)

            # Add a separate variable to track the sort order for each column
            setattr(self, f'sort_order_{col}', Qt.DescendingOrder)

        self.table_monthlyexpenses.insertRow(0)

        # Add data organization widgets to first row of table
        create_sort_button(0)
        init_text_filters(1)
        init_text_filters(2)
        create_sort_button(3)


    def get_table_data(self):
        data = [
            tuple(
                int(item.text()) if col == 0 else ('{0:.2f}'.format(float(item.text())) if col == 3 else item.text())
                for col, item in enumerate((self.table_monthlyexpenses.item(row, col) for col in range(self.table_monthlyexpenses.columnCount())))
            )
            for row in range(1, self.table_monthlyexpenses.rowCount())
            if not self.table_monthlyexpenses.isRowHidden(row)
        ]
        return data

    def apply_table_settings(self):

        # Disable id column
        for row in range(self.table_monthlyexpenses.rowCount()):
            item = self.table_monthlyexpenses.item(row,0)
            if item:
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)

        # Make first column resize to view content
        header = self.table_monthlyexpenses.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)

        # Restrict last column to ONLY decimal/integer values
        delegate = TableView_Delegate(self)
        self.table_monthlyexpenses.setItemDelegate(delegate)

        # Make last column stretch to fill table
        self.table_monthlyexpenses.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table_monthlyexpenses.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        
        # Remove table id's
        self.table_monthlyexpenses.verticalHeader().setVisible(False)

class MonthlyCategoriesViewer(QWidget):
    def __init__(self):
        super().__init__()

        self.db_manager = DatabaseManager()
        self.db_manager.open_database('app_data.db')

        self.layout = QVBoxLayout()
        self.inner_layout = QHBoxLayout()
        self.setLayout(self.layout)

        self.init_ui()

    def init_ui(self):

        self.init_total_label()
        self.init_pie_chart()
        self.init_category_table()
        self.layout.addLayout(self.inner_layout)

        self.update_category_totals('January')

    def init_total_label(self):
        frame = QFrame()
        frame_layout = QVBoxLayout(frame)

        self.label_monthlytotal = QLabel()
        self.label_monthlytotal.setAlignment(Qt.AlignCenter)
        frame_layout.addWidget(self.label_monthlytotal)
        frame.setLayout(frame_layout)

        frame.setStyleSheet('''
            QFrame 
            {
                background-color: #008FEC; /* Set the background color */
                border-radius: 10px; /* Set the border radius for rounded corners */
            }

            QLabel {
                color: #FFFFFF; /* Set text color */
                font-size: 15px; /* Set the font size to 18 pixels */
                font-family: Arial, sans-serif; /* Set the font family */
                font-weight: bold; /* Set the font weight to bold */
            }
        ''')

        self.layout.addWidget(frame)

    def init_pie_chart(self):

        self.pie_chart_view = QChartView()
        self.pie_chart_view.setMouseTracking(True)
        self.pie_chart_view.setRenderHint(QPainter.Antialiasing)

        self.pie_chart = QChart()
        self.pie_chart.setTheme(QChart.ChartThemeBlueNcs)
        self.pie_chart_view.setChart(self.pie_chart)


        self.pie_series = QPieSeries()
        self.pie_series.setHoleSize(0.2)
        self.pie_series.hovered.connect(self.onSliceHovered)


        self.pie_chart.addSeries(self.pie_series)
        self.pie_chart.setAnimationOptions(QChart.AllAnimations)
        self.pie_chart.legend().setVisible(False)

        # Add pie chart view to layout
        self.inner_layout.addWidget(self.pie_chart_view,40)

    def onSliceHovered(self,slice,state):

        slice.setExploded(state)
        slice.setLabelVisible(state)
        self.pie_chart_view.repaint()

    def onTableSelectionChanged(self):
        selected_items = self.table_categories.selectedItems()

        series = self.pie_chart.series()[0]
        slices = series.slices()

        for slice in slices:
            slice.setExploded(False)
            slice.setLabelVisible(False)

        for item in selected_items:
            row = item.row()
            slices[row].setExploded(True)
            slices[row].setLabelVisible(True)


        self.pie_chart_view.repaint()

    def init_category_table(self):

        self.table_categories = QTableWidget()
        self.table_categories.setColumnCount(4)
        self.table_categories.setHorizontalHeaderLabels(['Color','Category','Total','Percentage'])
        self.table_categories.setItemDelegate(CategoryTable_Delegate())
        self.table_categories.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_categories.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_categories.itemSelectionChanged.connect(self.onTableSelectionChanged)
        self.table_categories.setColumnWidth(0, 50)
        self.table_categories.setShowGrid(False)

        self.table_categories.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table_categories.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table_categories.horizontalHeader().setSectionResizeMode(0,QHeaderView.Fixed)

        # Add category table to layout
        self.inner_layout.addWidget(self.table_categories,60)

    def update_category_totals(self, month):

        data = self.db_manager.fetch_all(f'SELECT LOWER(Remarks) AS Category, SUM(Out) FROM {month} GROUP BY Category')
        data = [(Capitalize(category[0]), category[1]) for category in data]  # Capitalize Categories
        total_expense = sum(category[1] for category in data) # Total expenses for that month

        self.update_graph(data)
        self.label_monthlytotal.setText(f"RM {float(total_expense):.2f}")

    def update_legend(self):


        self.table_categories.setRowCount(0)

        for i, slice_ in enumerate(self.pie_series.slices()):
            color_item = QTableWidgetItem()
            color_item.setBackground(QColor(slice_.color()))

            category_item = QTableWidgetItem(slice_.label())
            value_item = QTableWidgetItem(f"RM {'{0:.2f}'.format(float(slice_.value()))}")
            percentage_item = QTableWidgetItem(f"{slice_.percentage() * 100:.1f}%")

            self.table_categories.insertRow(i)
            self.table_categories.setItem(i, 0, color_item)
            self.table_categories.setItem(i, 1, category_item)
            self.table_categories.setItem(i, 2, value_item)
            self.table_categories.setItem(i, 3, percentage_item)

    def update_graph(self, data):

        if data:
            self.pie_series.clear()

            for category,value in data:
                self.pie_series.append(category,value)

        else:
            self.pie_series.clear()
        self.update_legend()

class MonthlyExpensesViewer(QWidget):
    def __init__(self):
        super().__init__()

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.category_view = MonthlyCategoriesViewer()
        self.table_view = MonthlyCostsViewer(self.category_view)

        self.init_combobox_months()
        self.init_tab_widget()


    def change_tab_name(self):
        tab_name = f'{self.table_view.combobox_months.currentText()[:3]} Expenses'
        self.tab_widget.setTabText(0,tab_name)
        self.category_view.update_category_totals(self.table_view.combobox_months.currentText())

    def init_tab_widget(self):
        # Tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("QTabBar::tab { alignment: center; min-height: 40px; }")
        self.tab_widget.tabBar().setIconSize(QSize(24,24))
        self.tab_widget.tabBar().setFont(QFont('Arial',8,QFont.Bold))
        self.layout.addWidget(self.tab_widget)

        # Set to current month
        from datetime import datetime
        index = datetime.now().date().month
        self.table_view.combobox_months.setCurrentIndex(index-1)


        # Monthly expenses tab
        self.tab_widget.addTab(self.table_view,f'{self.table_view.combobox_months.currentText()[:3]} Expenses')
        self.tab_widget.setTabIcon(0, QIcon("images/months_icon.png"))

        self.table_view.combobox_months.currentIndexChanged.connect(self.change_tab_name)

        # Monthly category expenses tab
        self.tab_widget.addTab(self.category_view,QIcon("images/details_icon.png"),'Category')


    def init_combobox_months(self):

        self.months_option_layout = QHBoxLayout()
        self.months_option_layout.addWidget(self.table_view.combobox_months)

        self.layout.addLayout(self.months_option_layout)

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        # Set up window
        self.setWindowTitle('Expense Tracker')
        self.setWindowIcon(QIcon('images/window_icon.png'))
        self.setGeometry(500,50,800,800)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.layout.addWidget(MonthlyExpensesViewer())

def gui_darkstyle():
    file = QFile(":/dark/stylesheet.qss")
    file.open(QFile.ReadOnly | QFile.Text)
    stream = QTextStream(file)
    darkstyle = stream.readAll()

    return darkstyle


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet(gui_darkstyle())

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

    # Closes database when the user exits the application
    app.aboutToQuit.connect(window.db_manager.close_database)