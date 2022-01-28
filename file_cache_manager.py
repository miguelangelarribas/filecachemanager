import os
from PySide2 import QtCore as core
from PySide2 import QtWidgets as wdg
from functools import partial

class MainWindow(wdg.QMainWindow):
    def __init__(self, parent=hou.ui.mainQtWindow()):
        # inicializamos el init de la clase padre con super
        super(MainWindow, self).__init__(parent)

        self.ROOT = hou.node("/obj")
        self.ATTR_ROLE = core.Qt.UserRole
        self.VALUE_ROLE = core.Qt.UserRole + 1
        self.file_cache_list = []

        self._save_buttons = {}
        self._reload_buttons = {}

        self.setWindowTitle("FileCache Manager")
        self.setMinimumWidth(800)
        self.create_widgets()
        self.create_layouts()
        self.create_conexions()

    def create_widgets(self):
        self.table_wdg = wdg.QTableWidget()
        self.path_lab = wdg.QLabel("Cache Path")
        self.path_le = wdg.QLineEdit()
        self.path_le.setText("$JOB")
        self.set_path_btn = wdg.QPushButton("Set Path")
        self.load_all_cache = wdg.QCheckBox("Load All")
        self.table_wdg.setColumnCount(7)
        self.table_wdg.setColumnWidth(0, 70)
        self.table_wdg.setColumnWidth(1, 400)
        self.table_wdg.setColumnWidth(2, 20)
        self.table_wdg.setColumnWidth(3, 50)
        self.table_wdg.setColumnWidth(4, 100)
        self.table_wdg.setColumnWidth(5, 100)
        self.table_wdg.setColumnWidth(6, 100)
        self.table_wdg.setHorizontalHeaderLabels(["FileCache","Path", "Load", "Start", "End", "Save", "Reload"])
        header_view = self.table_wdg.horizontalHeader()
        header_view.setSectionResizeMode(1, wdg.QHeaderView.Stretch)
        self.update_btn = wdg.QPushButton("Update")
        self.cancel_btn = wdg.QPushButton("Cancel")
        self.save_btn = wdg.QPushButton("Save")
        self.save_btn.setMinimumWidth(100)

    def create_layouts(self):
        btn_lyt = wdg.QHBoxLayout()
        btn_lyt.setContentsMargins(6,6,6,6)
        btn_lyt.setSpacing(8)
        btn_lyt.addWidget(self.load_all_cache)
        btn_lyt.addStretch()
        btn_lyt.addWidget(self.update_btn)
        btn_lyt.addWidget(self.cancel_btn)

        set_path_lyt = wdg.QHBoxLayout()
        set_path_lyt.setContentsMargins(10,10,10,10)
        set_path_lyt.setSpacing(3)
        set_path_lyt.addWidget(self.path_lab)
        set_path_lyt.addWidget(self.path_le)
        set_path_lyt.addWidget(self.set_path_btn)

        main_lyt = wdg.QVBoxLayout()
        main_lyt.setContentsMargins(3,3,3,3)
        main_lyt.setSpacing(3)
        main_lyt.addWidget(self.table_wdg)
        main_lyt.addLayout(set_path_lyt)
        main_lyt.addLayout(btn_lyt)

        widget = wdg.QWidget()
        widget.setLayout(main_lyt)

        self.setCentralWidget(widget)

    def create_conexions(self):
        self.set_cell_changed_connection_enabled(True)
        self.update_btn.clicked.connect(self.update_table)
        self.cancel_btn.clicked.connect(self.close)
        self.set_path_btn.clicked.connect(self.set_path)
        self.load_all_cache.stateChanged.connect(self.load_caches)

    def set_cell_changed_connection_enabled(self, enabled):
        #cellChanged manda al slot row y column cambiados
        if enabled:
            self.table_wdg.cellChanged.connect(self.on_cell_changed)
        else:
            self.table_wdg.cellChanged.disconnect(self.on_cell_changed)

    def showEvent(self, e):
        super(MainWindow, self).showEvent(e)
        self.update_table()

    def update_table(self):
        self.set_cell_changed_connection_enabled(False)
        self.table_wdg.setRowCount(0)

        self.file_cache_list = [node
                           for node in self.ROOT.allSubChildren()
                           if node.type().name() == 'filecache']

        for i, node in enumerate(self.file_cache_list):
            file_cache_path = node.parm("file").unexpandedString()
            load_cache = node.evalParm("loadfromdisk")
            frame_parm = node.parmTuple("f")
            frame = node.evalParmTuple("f")
            frame_parm.deleteAllKeyframes()
            name = node.name()
            self.table_wdg.insertRow(i)
            self.insert_item(i, 0, name, name, node, False)
            self.insert_item(i, 1, file_cache_path, file_cache_path, node, False)
            self.insert_item(i, 2, "",node, load_cache,  True)
            self.insert_item(i, 3, self.float_to_string(frame[0]), frame[0], node, False)
            self.insert_item(i, 4, self.float_to_string(frame[1]), frame[1], node, False)
            self._save_buttons[i] = wdg.QPushButton("Save"), node
            self._reload_buttons[i] = wdg.QPushButton("Reload"), node

        self.create_save_buttons()
        self.set_cell_changed_connection_enabled(True)

    def create_save_buttons(self):
        for k,v in self._save_buttons.items():
            self.table_wdg.setCellWidget(k, 5, v[0])
            v[0].clicked.connect(partial(self.save_cache, v[1]))

        for k,v in self._reload_buttons.items():
            self.table_wdg.setCellWidget(k, 6, v[0])
            v[0].clicked.connect(partial(self.reload_cache, v[1]))

    def set_path(self):
        for cache_node in self.file_cache_list:

            new_path = self.path_le.text()
            actual_full_path = cache_node.parm("file").unexpandedString()
            file_name = os.path.basename(actual_full_path)
            file_dir = file_name.partition(".")[0]
            new_fullpath = os.path.join(new_path,file_dir, file_name)
            cache_node.parm("file").set(new_fullpath)
            self.update_table()

    def load_caches(self, s):
        state = s == core.Qt.Checked
        for cache_node in self.file_cache_list:
            cache_node.parm("loadfromdisk").set(state)
        self.update_table()

    def save_cache(self, nodo):
        hou.hipFile.save()
        nodo.parm("executebackground").pressButton()
        #todo mostrar feedback al usuario de abriendo opensheduler

    def reload_cache(self, nodo):
        nodo.parm("reload").pressButton()

    def on_cell_changed(self, row, column):
        self.set_cell_changed_connection_enabled(False)
        #seleccionamos el item de esa fila y columna recibido desde el slot
        item = self.table_wdg.item(row, column)
        if column in [0, 1]:
            self.rename(item, column)
        elif column == 2:
            self.update_check(item)
        elif column in  [3, 4]:
            self.reframe(item, column)
        self.set_cell_changed_connection_enabled(True)

    def insert_item(self, row, column, text, attr, value, is_boolean):
        item = wdg.QTableWidgetItem(text)
        self.set_item_attr(item, attr)
        self.set_item_value(item, value)
        self.table_wdg.setItem(row, column, item)

        if is_boolean:
            item.setFlags(core.Qt.ItemIsUserCheckable | core.Qt.ItemIsEnabled)
            self.set_item_checked(item, value)

    def rename(self, item, column):
        file_cache_node = self.get_item_value(item) #node
        old_name = self.get_item_attr(item) #path
        new_name = self.get_item_text(item) #new_path

        if old_name != new_name and column == 0:
            try:
                file_cache_node.setName(new_name)
                actual_new_name = file_cache_node.name()
                if actual_new_name != new_name:
                    self.set_item_text(item, actual_new_name)
                self.set_item_attr(item, actual_new_name)
            except:
                file_cache_node.setName(old_name)
                #todo implementar diplay message de houdini
                print "Escriba un Nombre valido"
                return
        elif old_name != new_name and column == 1:
            file_cache_node.parm("file").set(new_name)
            actual_new_name = file_cache_node.parm("file").unexpandedString()
            if actual_new_name != new_name:
                self.set_item_text(item, actual_new_name)
            self.set_item_attr(item, actual_new_name)

    def reframe(self, item, column):
        file_cache_node = self.get_item_value(item) #node
        old_frame = self.float_to_string(self.get_item_attr(item)) #int
        new_frame = self.get_item_text(item)  # new_frame_string
        new_frame_float = 0
        try:
            new_frame_float = float(new_frame)
        except:
            print "No puedo convertir a float"

        if old_frame != new_frame and column == 3:
            file_cache_node.parm("f1").set(new_frame_float)
            self.set_item_text(item, new_frame)
            self.set_item_attr(item, new_frame_float)
        elif old_frame != new_frame and column == 4:
            file_cache_node.parm("f2").set(new_frame_float)
            self.set_item_text(item, new_frame)
            self.set_item_attr(item, new_frame_float)

    def update_check(self, item):
        is_checked = self.is_item_checked(item)
        node = self.get_item_attr(item)
        node.parm("loadfromdisk").set(is_checked)


    def set_item_attr(self, item, attr):
        item.setData(self.ATTR_ROLE, attr)

    def get_item_attr(self, item):
        return item.data(self.ATTR_ROLE)

    def set_item_value(self, item, value):
        item.setData(self.VALUE_ROLE, value)

    def get_item_value(self, item):
        return item.data(self.VALUE_ROLE)

    def get_item_text(self, item):
        return item.text()

    def set_item_checked(self, item, checked):
        if checked:
            item.setCheckState(core.Qt.Checked)
        else:
            item.setCheckState(core.Qt.Unchecked)

    def set_item_text(self, item, text):
        item.setText(text)

    def is_item_checked(self, item):
        return item.checkState() == core.Qt.Checked

    def float_to_string(self, num):
            return str(int(num))

window = MainWindow()
window.show()
