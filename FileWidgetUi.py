# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'c:\Users\Administrator\Desktop\python\PyQt\test1\Inverted_pendulum\loadingWidget.ui'
#
# Created by: PyQt5 UI code generator 5.13.0
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import os
from FileClass import File

class fileWiget(QWidget):
    fileWidgetClosedSignal = QtCore.pyqtSignal()
    def closeEvent(self, event):
        print('fileWindow closed')
        self.fileWidgetClosedSignal.emit()
        

class FileUi(QObject):
    fileLoadedSignal = QtCore.pyqtSignal(bool)
    def __init__(self,widget,rod,ctrl):
        super().__init__()
        self.__widget = widget          # 承载ui的窗口
        self.__cwd = os.getcwd()        # 当前程序文件位置
        self.__file = File(rod,ctrl)
        self.__loaded = False           # 是否完成加载操作
    #建立ui-----------------------------------------------------------------------------------------------
    def setupUi(self):
        self.__widget.setObjectName("Form")
        self.__widget.resize(800, 600)
        self.gridLayout = QtWidgets.QGridLayout(self.__widget)
        self.gridLayout.setObjectName("gridLayout")
        self.gridLayout_2 = QtWidgets.QGridLayout()
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.pushButton_save = QtWidgets.QPushButton(self.__widget)
        self.pushButton_save.setObjectName("pushButton_save")
        self.gridLayout_2.addWidget(self.pushButton_save, 2, 0, 1, 1)
        self.pushButton_select = QtWidgets.QPushButton(self.__widget)
        self.pushButton_select.setObjectName("pushButton_select")
        self.gridLayout_2.addWidget(self.pushButton_select, 0, 0, 1, 2)
        self.pushButton_load = QtWidgets.QPushButton(self.__widget)
        self.pushButton_load.setObjectName("pushButton_load")
        self.gridLayout_2.addWidget(self.pushButton_load, 2, 1, 1, 1)
        self.gridLayout.addLayout(self.gridLayout_2, 0, 0, 1, 1)
        self.fileName = QtWidgets.QLineEdit(self.__widget)
        self.fileName.setObjectName("lineEdit")
        self.gridLayout_2.addWidget(self.fileName, 3, 0, 1, 2)
        self.textBrowser = QtWidgets.QTextBrowser(self.__widget)
        self.textBrowser.setObjectName("textBrowser")
        self.gridLayout.addWidget(self.textBrowser, 0, 1, 2, 1)
        self.treeWidget = QtWidgets.QTreeWidget(self.__widget)
        self.treeWidget.setObjectName("treeWidget")
        self.treeWidget.headerItem().setText(0, "files")
        self.gridLayout.addWidget(self.treeWidget, 1, 0, 1, 1)
        self.gridLayout.setColumnStretch(0, 2)
        self.gridLayout.setColumnStretch(1, 3)

        self.retranslateUi(self.__widget)
        self.__treeRoot = QTreeWidgetItem(self.treeWidget)

        self.pushButton_load.setEnabled(False)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "file"))
        self.pushButton_save.setText(_translate("Form", "保存"))
        self.pushButton_select.setText(_translate("Form", "选择文件夹"))
        self.pushButton_load.setText(_translate("Form", "加载"))

    
    #连接信号与槽------------------------------------------------------------------------------------------
    def initUi(self):
        self.pushButton_select.clicked.connect(self.getFileDir)
        self.pushButton_save.clicked.connect(self.saveFile)
        self.pushButton_load.clicked.connect(self.loadFile)
        self.treeWidget.clicked.connect(self.chooseFile)
        self.__widget.fileWidgetClosedSignal.connect(self.clearWindow)

    #槽函数，窗口关闭时进行清理
    def clearWindow(self):
        self.textBrowser.setText('')
        self.fileName.setText('')
        self.pushButton_load.setEnabled(False)
        self.fileLoadedSignal.emit(self.__loaded)
        self.__loaded = False

    #槽函数：选择配置文件夹
    def getFileDir(self):
        dir_choose = QFileDialog.getExistingDirectory(self.__widget, "选取文件夹", self.__cwd) # 起始路径

        if dir_choose == "":
            print("\n取消选择")
            return

        print("\n你选择的文件夹为:" + dir_choose)
        self.__dirPath = dir_choose

        self.refreshDirTree(dir_choose)
        self.fileName.setText('')

    #槽函数：保存配置文文件
    def saveFile(self):
        name = self.fileName.text()
        if name == '':
            self.textBrowser.setText('请输入文件名(.txt后缀) ！')
            return
        elif name[-4:] != '.txt':
            self.textBrowser.setText('文件名后缀不正确，应为.txt文件 ！')
            return

        #保存文件
        flag = self.__file.saveData(self.__dirPath,name)
        
        #提示
        if flag:
            self.textBrowser.setText("文件已覆盖")        
        else:
            self.textBrowser.setText("文件已保存")
        
        #刷新tree
        self.refreshDirTree(self.__dirPath) 

    #槽函数：加载配置文件
    def loadFile(self):
        fp = open(self.__filePath,'r')

        lines = fp.readlines()
        print(lines)

        if len(lines) != 15:
            self.textBrowser.setText('配置文件格式错误：文件行数错误!')
            return
        if lines[0] != 'Inverted pendulum simulator setting data\n':
            self.textBrowser.setText('配置文件格式错误：身份标识错误!')
            return
        elif lines[3] != 'v1.0\n':
            self.textBrowser.setText('配置文件格式错误：UI版本错误！')
            return
        elif lines[-1] != 'end':
            self.textBrowser.setText('配置文件格式错误：未检测到结束标识！')
            return

        #print(lines)
        self.__file.loadData(lines)
        self.Loaded()
        fp.close()

        self.__widget.close()

    #成员函数------------------------------------------------------------------------------------------
    #发生了文件加载，设置标志
    def Loaded(self):
        self.__loaded = True

    #显示fileWidget
    def showWidget(self):
        if not self.__widget.isVisible():
            self.__widget.show()
        print(self.__dirPath)
        self.refreshDirTree(self.__dirPath)

    #设置配置文件夹
    def setFileDir(self,dir):
        self.__dirPath = dir

    #获取文件夹中的文件,加入treeWidget
    def refreshDirTree(self,path):

        #设置列数
        self.treeWidget.setColumnCount(1)
        #设置树形控件头部的标题
        self.treeWidget.setHeaderLabels(['files'])

        #设置根节点
        self.__treeRoot.setText(0,'Root')
        #root.setIcon(0,QIcon('./images/root.png'))

        #先把以前的tree清空
        self.clearFileTree()

        #添加子节点
        files = os.listdir(path)
        for file in files:
            file_path = os.path.join(path, file)

            if os.path.isfile(file_path):
                print(file)

                child = QTreeWidgetItem()
                child.setText(0,file)
                self.__treeRoot.addChild(child)
            elif os.path.isdir(file_path):
                pass

        #节点全部展开
        self.treeWidget.expandAll()

    #清空treeWidget
    def clearFileTree(self):
        for i in range(self.__treeRoot.childCount()):
            self.__treeRoot.removeChild(self.__treeRoot.child(0))

    #在treeWidget中点击文件,在textBroswer现实预览
    def chooseFile(self,path):
        item = self.treeWidget.currentItem()
        print(item.text(0))
        self.fileName.setText(item.text(0))

        if item.text(0)[-4:] != '.txt':
            self.textBrowser.setText('文件类型错误！请选择.txt文件')
            self.pushButton_load.setEnabled(False)
        else:
            self.__filePath = self.__dirPath + '/'+ item.text(0)
            self.pushButton_load.setEnabled(True)

            f = open(self.__filePath,'r')

            with f:
                #接受读取的内容，并显示到多行文本框中
                data = f.read()
                self.textBrowser.setText(data)             

