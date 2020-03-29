# 此文件用于建立帮助窗口Ui
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import os

class Help(QObject):
    def __init__(self,widget):
        super().__init__()
        self.__widget = widget          # 承载ui的窗口

    #建立ui-----------------------------------------------------------------------------------------------
    def setupUi(self):
        self.__widget.setObjectName("HelpWidget")
        self.__widget.resize(1200, 600)
        self.gridLayout = QtWidgets.QGridLayout(self.__widget)
        self.gridLayout.setObjectName("gridLayout")
        self.textBrowser = QtWidgets.QTextBrowser(self.__widget)
        self.textBrowser.setObjectName("textBrowser")
        self.gridLayout.addWidget(self.textBrowser, 0, 0, 1, 1)
        
        self.textBrowser.setText('1')

        self.retranslateUi(self.__widget)

    def retranslateUi(self, widget):
        _translate = QtCore.QCoreApplication.translate
        widget.setWindowTitle(_translate("HelpWidget", "HelpWidget"))


    def showWidget(self,filePath):
        f = open(filePath,'r',encoding='utf-8')

        with f:
            #接受读取的内容，并显示到多行文本框中
            data = f.read()
            self.textBrowser.setText(data)      

        if not self.__widget.isVisible():
            self.__widget.show()
