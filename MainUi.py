# 此文件用于建立主窗口UI(前后端分离)
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import QPainter,QColor,QFont,QPen
from PyQt5 import QtCore, QtGui, QtWidgets
import numpy as np
import math
from RodClass import Rod

# 从QWidget继承，用来绘制移动的倒立摆
class RodWidget(QWidget):
    rodRepaintSignal = QtCore.pyqtSignal()          # 给类定义一个摆杆重绘信号（这个必须定义在类中）
    PIDCalSignal = QtCore.pyqtSignal(list)          # pid计算信号
    failSignal = QtCore.pyqtSignal()                # 摆杆偏移角度过大

    def __init__(self,rod,ctrl):
        super().__init__()    
        # 摆杆下端点（原点）相对工作区的坐标(用于确定摆相对窗口的位置)
        self.__oriPoint = np.mat([self.geometry().width()*0.5 , self.geometry().height()*0.6]) 
        self.__rod = rod
        self.__controller = ctrl
        self.__AutoReset = True                      # 默认进行自动重置

        # 配置定时器，调用paintEvent刷新频率周期为1ms
        self.timer = QTimer()
        self.timer.timeout.connect(self.update)

        # 默认进行动力学分析
        self.__kinematicsEnabled = True
    
    # 设置自动复位是否开启
    def setAuotReset(self,flag):
        self.__AutoReset = flag
        
    # 开始绘制，周期5ms
    def startPaintRod(self):
        self.timer.start(5)
    
    # 停止绘制
    def stopPaintRod(self):
        self.timer.stop()

    # 要不要使能运动学分析
    def setKinematicsEnable(self,flag):
        self.__kinematicsEnabled = flag

    # 绘制网格
    def drawGrid(self,painter,x,y):
        # 粗实线画X轴
        painter.setPen(QPen(Qt.blue, 3, Qt.SolidLine))  
        painter.drawLine(QLineF(0 , y , self.geometry().width() , y))

        # 如果位移没有超过出屏，Y轴就用粗实线画，否则用细实线画
        if self.__rod.getX() > -self.geometry().width()/2 and self.__rod.getX() < self.geometry().width()/2:
            painter.setPen(QPen(Qt.blue, 3, Qt.SolidLine))
            painter.drawLine(QLineF(x , 0 , x , self.geometry().height()))
        else:
            painter.setPen(QPen(Qt.blue, 1, Qt.SolidLine))
            painter.drawLine(QLineF(x , 0 , x , self.geometry().height()))

        # 细实线画网格
        painter.setPen(QPen(Qt.blue, 1, Qt.SolidLine))
        temp1 = temp2 = y
        while(temp1 > 0):
            temp1 -= 30
            painter.drawLine(QLineF(0 , temp1 , self.geometry().width() , temp1))
        while(temp2 < self.geometry().height()):
            temp2 += 30
            painter.drawLine(QLineF(0 , temp2 , self.geometry().width() , temp2))
        
        temp1 = temp2 = x
        while(temp1 > 0):
            temp1 -= 30
            painter.drawLine(QLineF(temp1 , 0 , temp1 , self.geometry().height()))
        while(temp2 < self.geometry().width()):
            temp2 += 30
            painter.drawLine(QLineF(temp2 , 0 , temp2 , self.geometry().height()))

    # pid计算
    def pidControl(self): 
        #获取当前角度
        currentAng = self.__rod.getAngle()

        #数据异常，自动复位
        if self.__AutoReset:
        #if self.__controller['DispPos'].isEnable() or self.__controller['DispSpd'].isEnable() or self.__controller['AngPos'].isEnable() or self.__controller['AngSpd'].isEnable():
            if (currentAng % 360 > 160 and currentAng % 360 < 200)  or self.__rod.getV() > 20000 or self.__rod.getV() < -20000 or self.__rod.getW() > 20000 or self.__rod.getW() < -20000 :
                self.failSignal.emit()

        res = [0.0,0.0,0.0,0.0]     #四个环的输出
        angOut = 0.0                #摆角两个环综合输出
        dispOut = 0.0               #位移两个环综合输出
        
        #位移位置环
        if self.__controller['DispPos'].isEnable():
            self.__controller['DispPos'].setRef(0)      #位置期望在原点，注意要放在原点附近才行
            self.__controller['DispPos'].setFdb(self.__rod.getX())
            res[2] = self.__controller['DispPos'].calculate()

        dispOut = res[2]

        #位移速度环
        if self.__controller['DispSpd'].isEnable():

            self.__controller['DispSpd'].setRef(res[2])  
            self.__controller['DispSpd'].setFdb(self.__rod.getV())
            res[3] = self.__controller['DispSpd'].calculate()

            dispOut = res[3]

        #摆角位置环
        if self.__controller['AngPos'].isEnable():
            self.__controller['AngPos'].setRef(0)   
            
            currentAng %= 360
            if currentAng > 180:
                currentAng -= 360
            self.__controller['AngPos'].setFdb(currentAng)
            res[0] = self.__controller['AngPos'].calculate()
        
        angOut = res[0]

        #摆角速度环
        if self.__controller['AngSpd'].isEnable():

            self.__controller['AngSpd'].setRef(res[0])  
            self.__controller['AngSpd'].setFdb(self.__rod.getW())
            res[1] = self.__controller['AngSpd'].calculate()

            angOut = res[1]
        
        self.PIDCalSignal.emit(res)
        return angOut + dispOut

    # 摆杆绘制事件
    def paintEvent(self,event):
        # 重新适配原点y坐标位置
        self.__oriPoint = np.mat([self.geometry().width()*0.5 , self.geometry().height()*0.6]) 

        # 开始绘制
        painter = QPainter(self)
        painter.begin(self)

        # 更新摆杆数据(每轮刷新迭代10次)
        if self.__kinematicsEnabled:
            for i in range(100):
                self.__rod.setF(self.pidControl())  
                self.__rod.update()
                
        posTemp = self.__oriPoint.copy()
        posTemp[0,0] += self.__rod.getX()       #把摆杆下端点位移加上工作区中点坐标，写回rod.__pos，这样返回直线坐标时适配窗口拖动
        posTemp[0,0] %= self.geometry().width()
        self.__rod.setPos(posTemp)

        # 绘制坐标网格
        self.drawGrid(painter , self.__oriPoint[0,0] , self.__oriPoint[0,1])

        # 绘制摆杆
        painter.setPen(QPen(Qt.red, 3, Qt.SolidLine))   #设置画笔颜色   
        rodLine = self.__rod.returnAsLine() 
        painter.drawLine(QLineF(rodLine[0,0],rodLine[0,1],rodLine[0,2],rodLine[0,3]))

        # 发送信号，通知主界面更新数据
        self.rodRepaintSignal.emit()

        # 绘制结束
        painter.end()
        
# 主窗口UI
class Ui_MainWindow(object):
    def setupUi(self,MainWindow,rod,ctrl):
        # 中心窗口
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(970, 714)

        # 中心窗口的尺寸
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(MainWindow.sizePolicy().hasHeightForWidth())
        MainWindow.setSizePolicy(sizePolicy)
        MainWindow.setMinimumSize(QtCore.QSize(0, 680))
        
        # 中心网格布局
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout_5 = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout_5.setSizeConstraint(QtWidgets.QLayout.SetDefaultConstraint)
        self.gridLayout_5.setObjectName("gridLayout_5")

        # 中心布局上的分割线
        self.line_11 = QtWidgets.QFrame(self.centralwidget)
        self.line_11.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_11.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_11.setObjectName("line_11")
        self.gridLayout_5.addWidget(self.line_11, 0, 0, 1, 4)
        self.line_1 = QtWidgets.QFrame(self.centralwidget)
        self.line_1.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_1.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_1.setObjectName("line_1")
        self.gridLayout_5.addWidget(self.line_1, 5, 0, 1, 1)
        self.line_2 = QtWidgets.QFrame(self.centralwidget)
        self.line_2.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_2.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_2.setObjectName("line_2")
        self.gridLayout_5.addWidget(self.line_2, 5, 2, 1, 2)
        self.line_3 = QtWidgets.QFrame(self.centralwidget)
        self.line_3.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_3.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_3.setObjectName("line_3")
        self.gridLayout_5.addWidget(self.line_3, 2, 0, 1, 4)
        self.line_4 = QtWidgets.QFrame(self.centralwidget)
        self.line_4.setFrameShape(QtWidgets.QFrame.VLine)
        self.line_4.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_4.setObjectName("line_4")
        self.gridLayout_5.addWidget(self.line_4, 4, 1, 1, 2)
        self.line_5 = QtWidgets.QFrame(self.centralwidget)
        self.line_5.setFrameShape(QtWidgets.QFrame.VLine)
        self.line_5.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_5.setObjectName("line_5")
        self.gridLayout_5.addWidget(self.line_5, 6, 1, 1, 1)
        self.line_6 = QtWidgets.QFrame(self.centralwidget)
        self.line_6.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_6.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_6.setObjectName("line_6")
        self.gridLayout_5.addWidget(self.line_6, 8, 0, 1, 4)

        # rodWidget部分
        #self.widget = QtWidgets.QWidget(self.centralwidget)
        self.widget = RodWidget(rod,ctrl)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.widget.sizePolicy().hasHeightForWidth())
        self.widget.setSizePolicy(sizePolicy)
        self.widget.setMinimumSize(QtCore.QSize(0, 250))
        self.widget.setAccessibleDescription("")
        self.widget.setObjectName("widget")
        self.gridLayout_5.addWidget(self.widget, 1, 0, 1, 4)

        #PID参数部分网格布局
        self.gridLayout_PID = QtWidgets.QGridLayout()
        self.gridLayout_PID.setSizeConstraint(QtWidgets.QLayout.SetMinimumSize)
        self.gridLayout_PID.setObjectName("gridLayout_PID")
        self.line_8 = QtWidgets.QFrame(self.centralwidget)
        self.line_8.setFrameShape(QtWidgets.QFrame.VLine)
        self.line_8.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_8.setObjectName("line_8")
        self.gridLayout_PID.addWidget(self.line_8, 0, 6, 10, 1)
        self.in_KP_DispSpd = QtWidgets.QLineEdit(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.in_KP_DispSpd.sizePolicy().hasHeightForWidth())
        self.in_KP_DispSpd.setSizePolicy(sizePolicy)
        self.in_KP_DispSpd.setMinimumSize(QtCore.QSize(0, 0))
        self.in_KP_DispSpd.setObjectName("in_KP_DispSpd")
        self.gridLayout_PID.addWidget(self.in_KP_DispSpd, 2, 12, 1, 1)
        self.KP_DispPos = QtWidgets.QLabel(self.centralwidget)
        self.KP_DispPos.setObjectName("KP_DispPos")
        self.gridLayout_PID.addWidget(self.KP_DispPos, 2, 7, 1, 2)
        self.line_10 = QtWidgets.QFrame(self.centralwidget)
        self.line_10.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_10.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_10.setObjectName("line_10")
        self.gridLayout_PID.addWidget(self.line_10, 5, 3, 1, 3)
        self.KD_DispPos = QtWidgets.QLabel(self.centralwidget)
        self.KD_DispPos.setObjectName("KD_DispPos")
        self.gridLayout_PID.addWidget(self.KD_DispPos, 4, 7, 1, 2)
        self.outData_AngPos = QtWidgets.QLabel(self.centralwidget)
        self.outData_AngPos.setObjectName("outData_AngPos")
        self.gridLayout_PID.addWidget(self.outData_AngPos, 6, 1, 1, 1)
        self.in_KP_AngSpd = QtWidgets.QLineEdit(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.in_KP_AngSpd.sizePolicy().hasHeightForWidth())
        self.in_KP_AngSpd.setSizePolicy(sizePolicy)
        self.in_KP_AngSpd.setObjectName("in_KP_AngSpd")
        self.gridLayout_PID.addWidget(self.in_KP_AngSpd, 2, 5, 1, 1)
        self.KD_DispSpd = QtWidgets.QLabel(self.centralwidget)
        self.KD_DispSpd.setObjectName("KD_DispSpd")
        self.gridLayout_PID.addWidget(self.KD_DispSpd, 4, 11, 1, 1)
        self.outData_AngSpd = QtWidgets.QLabel(self.centralwidget)
        self.outData_AngSpd.setObjectName("outData_AngSpd")
        self.gridLayout_PID.addWidget(self.outData_AngSpd, 6, 5, 1, 1)
        self.outData_DispSpd = QtWidgets.QLabel(self.centralwidget)
        self.outData_DispSpd.setObjectName("outData_DispSpd")
        self.gridLayout_PID.addWidget(self.outData_DispSpd, 6, 12, 1, 1)
        self.in_KD_DispPos = QtWidgets.QLineEdit(self.centralwidget)
        self.in_KD_DispPos.setObjectName("in_KD_DispPos")
        self.gridLayout_PID.addWidget(self.in_KD_DispPos, 4, 9, 1, 1)
        self.in_KI_AngPos = QtWidgets.QLineEdit(self.centralwidget)
        self.in_KI_AngPos.setMinimumSize(QtCore.QSize(0, 0))
        self.in_KI_AngPos.setObjectName("in_KI_AngPos")
        self.gridLayout_PID.addWidget(self.in_KI_AngPos, 3, 1, 1, 1)
        self.KP_DispSpd = QtWidgets.QLabel(self.centralwidget)
        self.KP_DispSpd.setObjectName("KP_DispSpd")
        self.gridLayout_PID.addWidget(self.KP_DispSpd, 2, 11, 1, 1)
        self.out_AngSpd = QtWidgets.QLabel(self.centralwidget)
        self.out_AngSpd.setObjectName("out_AngSpd")
        self.gridLayout_PID.addWidget(self.out_AngSpd, 6, 3, 1, 2)
        self.label_DispSpe = QtWidgets.QLabel(self.centralwidget)
        self.label_DispSpe.setObjectName("label_DispSpe")
        self.gridLayout_PID.addWidget(self.label_DispSpe, 0, 11, 2, 2)
        self.in_KI_DispSpd = QtWidgets.QLineEdit(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.in_KI_DispSpd.sizePolicy().hasHeightForWidth())
        self.in_KI_DispSpd.setSizePolicy(sizePolicy)
        self.in_KI_DispSpd.setMinimumSize(QtCore.QSize(0, 0))
        self.in_KI_DispSpd.setObjectName("in_KI_DispSpd")
        self.gridLayout_PID.addWidget(self.in_KI_DispSpd, 3, 12, 1, 1)
        self.out_DispSpd = QtWidgets.QLabel(self.centralwidget)
        self.out_DispSpd.setObjectName("out_DispSpd")
        self.gridLayout_PID.addWidget(self.out_DispSpd, 6, 11, 1, 1)
        self.label_AngPos = QtWidgets.QLabel(self.centralwidget)
        self.label_AngPos.setMinimumSize(QtCore.QSize(0, 0))
        self.label_AngPos.setObjectName("label_AngPos")
        self.gridLayout_PID.addWidget(self.label_AngPos, 0, 0, 2, 2)
        self.KI_DispSpd = QtWidgets.QLabel(self.centralwidget)
        self.KI_DispSpd.setObjectName("KI_DispSpd")
        self.gridLayout_PID.addWidget(self.KI_DispSpd, 3, 11, 1, 1)
        self.in_KD_AngPos = QtWidgets.QLineEdit(self.centralwidget)
        self.in_KD_AngPos.setMinimumSize(QtCore.QSize(0, 0))
        self.in_KD_AngPos.setObjectName("in_KD_AngPos")
        self.gridLayout_PID.addWidget(self.in_KD_AngPos, 4, 1, 1, 1)
        self.in_KD_DispSpd = QtWidgets.QLineEdit(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.in_KD_DispSpd.sizePolicy().hasHeightForWidth())
        self.in_KD_DispSpd.setSizePolicy(sizePolicy)
        self.in_KD_DispSpd.setMinimumSize(QtCore.QSize(0, 0))
        self.in_KD_DispSpd.setObjectName("in_KD_DispSpd")
        self.gridLayout_PID.addWidget(self.in_KD_DispSpd, 4, 12, 1, 1)
        self.label_DispPos = QtWidgets.QLabel(self.centralwidget)
        self.label_DispPos.setObjectName("label_DispPos")
        self.gridLayout_PID.addWidget(self.label_DispPos, 0, 7, 2, 3)
        self.in_KP_DispPos = QtWidgets.QLineEdit(self.centralwidget)
        self.in_KP_DispPos.setObjectName("in_KP_DispPos")
        self.gridLayout_PID.addWidget(self.in_KP_DispPos, 2, 9, 1, 1)
        self.out_DispPos = QtWidgets.QLabel(self.centralwidget)
        self.out_DispPos.setObjectName("out_DispPos")
        self.gridLayout_PID.addWidget(self.out_DispPos, 6, 7, 1, 2)
        self.EnableBox_DispPos = QtWidgets.QCheckBox(self.centralwidget)
        self.EnableBox_DispPos.setMinimumSize(QtCore.QSize(0, 0))
        self.EnableBox_DispPos.setObjectName("EnableBox_DispPos")
        self.gridLayout_PID.addWidget(self.EnableBox_DispPos, 7, 7, 3, 3)
        self.line_7 = QtWidgets.QFrame(self.centralwidget)
        self.line_7.setFrameShape(QtWidgets.QFrame.VLine)
        self.line_7.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_7.setObjectName("line_7")
        self.gridLayout_PID.addWidget(self.line_7, 0, 2, 10, 1)
        self.line_9 = QtWidgets.QFrame(self.centralwidget)
        self.line_9.setFrameShape(QtWidgets.QFrame.VLine)
        self.line_9.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_9.setObjectName("line_9")
        self.gridLayout_PID.addWidget(self.line_9, 0, 10, 10, 1)
        self.EnableBox_AnglePos = QtWidgets.QCheckBox(self.centralwidget)
        self.EnableBox_AnglePos.setMinimumSize(QtCore.QSize(0, 25))
        self.EnableBox_AnglePos.setObjectName("EnableBox_AnglePos")
        self.gridLayout_PID.addWidget(self.EnableBox_AnglePos, 7, 0, 3, 2)
        self.KI_AnglePos = QtWidgets.QLabel(self.centralwidget)
        self.KI_AnglePos.setMinimumSize(QtCore.QSize(0, 0))
        self.KI_AnglePos.setObjectName("KI_AnglePos")
        self.gridLayout_PID.addWidget(self.KI_AnglePos, 3, 0, 1, 1)
        self.KP_AngleSpd = QtWidgets.QLabel(self.centralwidget)
        self.KP_AngleSpd.setObjectName("KP_AngleSpd")
        self.gridLayout_PID.addWidget(self.KP_AngleSpd, 2, 3, 1, 2)
        self.EnableBox_DispSpd = QtWidgets.QCheckBox(self.centralwidget)
        self.EnableBox_DispSpd.setObjectName("EnableBox_DispSpd")
        self.gridLayout_PID.addWidget(self.EnableBox_DispSpd, 7, 11, 3, 2)
        self.KI_AngleSpd = QtWidgets.QLabel(self.centralwidget)
        self.KI_AngleSpd.setObjectName("KI_AngleSpd")
        self.gridLayout_PID.addWidget(self.KI_AngleSpd, 3, 3, 1, 2)
        self.KI_DispPos = QtWidgets.QLabel(self.centralwidget)
        self.KI_DispPos.setObjectName("KI_DispPos")
        self.gridLayout_PID.addWidget(self.KI_DispPos, 3, 7, 1, 2)
        self.in_KD_AngSpd = QtWidgets.QLineEdit(self.centralwidget)
        self.in_KD_AngSpd.setObjectName("in_KD_AngSpd")
        self.gridLayout_PID.addWidget(self.in_KD_AngSpd, 4, 5, 1, 1)
        self.out_AngPos = QtWidgets.QLabel(self.centralwidget)
        self.out_AngPos.setObjectName("out_AngPos")
        self.gridLayout_PID.addWidget(self.out_AngPos, 6, 0, 1, 1)
        self.in_KI_DispPos = QtWidgets.QLineEdit(self.centralwidget)
        self.in_KI_DispPos.setObjectName("in_KI_DispPos")
        self.gridLayout_PID.addWidget(self.in_KI_DispPos, 3, 9, 1, 1)
        self.line = QtWidgets.QFrame(self.centralwidget)
        self.line.setFrameShape(QtWidgets.QFrame.HLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line.setObjectName("line")
        self.gridLayout_PID.addWidget(self.line, 5, 0, 1, 2)
        self.in_KI_AngSpd = QtWidgets.QLineEdit(self.centralwidget)
        self.in_KI_AngSpd.setObjectName("in_KI_AngSpd")
        self.gridLayout_PID.addWidget(self.in_KI_AngSpd, 3, 5, 1, 1)
        self.KD_AngleSpd = QtWidgets.QLabel(self.centralwidget)
        self.KD_AngleSpd.setObjectName("KD_AngleSpd")
        self.gridLayout_PID.addWidget(self.KD_AngleSpd, 4, 3, 1, 2)
        self.EnableBox_AngleSpd = QtWidgets.QCheckBox(self.centralwidget)
        self.EnableBox_AngleSpd.setObjectName("EnableBox_AngleSpd")
        self.gridLayout_PID.addWidget(self.EnableBox_AngleSpd, 7, 3, 3, 3)
        self.KD_AnglePos = QtWidgets.QLabel(self.centralwidget)
        self.KD_AnglePos.setMinimumSize(QtCore.QSize(0, 0))
        self.KD_AnglePos.setObjectName("KD_AnglePos")
        self.gridLayout_PID.addWidget(self.KD_AnglePos, 4, 0, 1, 1)
        self.in_KP_AngPos = QtWidgets.QLineEdit(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.in_KP_AngPos.sizePolicy().hasHeightForWidth())
        self.in_KP_AngPos.setSizePolicy(sizePolicy)
        self.in_KP_AngPos.setMinimumSize(QtCore.QSize(0, 0))
        self.in_KP_AngPos.setObjectName("in_KP_AngPos")
        self.gridLayout_PID.addWidget(self.in_KP_AngPos, 2, 1, 1, 1)
        self.KP_AnglePos = QtWidgets.QLabel(self.centralwidget)
        self.KP_AnglePos.setMinimumSize(QtCore.QSize(0, 0))
        self.KP_AnglePos.setObjectName("KP_AnglePos")
        self.gridLayout_PID.addWidget(self.KP_AnglePos, 2, 0, 1, 1)
        self.outData_DispPos = QtWidgets.QLabel(self.centralwidget)
        self.outData_DispPos.setObjectName("outData_DispPos")
        self.gridLayout_PID.addWidget(self.outData_DispPos, 6, 9, 1, 1)
        self.line_12 = QtWidgets.QFrame(self.centralwidget)
        self.line_12.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_12.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_12.setObjectName("line_12")
        self.gridLayout_PID.addWidget(self.line_12, 5, 7, 1, 3)
        self.line_13 = QtWidgets.QFrame(self.centralwidget)
        self.line_13.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_13.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_13.setObjectName("line_13")
        self.gridLayout_PID.addWidget(self.line_13, 5, 11, 1, 2)
        self.label_AngSpd = QtWidgets.QLabel(self.centralwidget)
        self.label_AngSpd.setObjectName("label_AngSpd")
        self.gridLayout_PID.addWidget(self.label_AngSpd, 0, 3, 2, 3)
        self.gridLayout_5.addLayout(self.gridLayout_PID, 6, 0, 1, 1)
        self.in_KP_AngPos.setEnabled(False)
        self.in_KD_AngPos.setEnabled(False)
        self.in_KI_AngPos.setEnabled(False)
        self.in_KP_AngSpd.setEnabled(False)
        self.in_KI_AngSpd.setEnabled(False)
        self.in_KD_AngSpd.setEnabled(False)
        self.in_KP_DispPos.setEnabled(False)
        self.in_KI_DispPos.setEnabled(False)
        self.in_KD_DispPos.setEnabled(False)
        self.in_KP_DispSpd.setEnabled(False)
        self.in_KI_DispSpd.setEnabled(False)
        self.in_KD_DispSpd.setEnabled(False)

        #提示信息部分网格布局
        self.gridLayout_Info = QtWidgets.QGridLayout()
        self.gridLayout_Info.setSizeConstraint(QtWidgets.QLayout.SetMinimumSize)
        self.gridLayout_Info.setObjectName("gridLayout_Info")
        self.InfoData_ang = QtWidgets.QLabel(self.centralwidget)
        self.InfoData_ang.setObjectName("InfoData_ang")
        self.gridLayout_Info.addWidget(self.InfoData_ang, 2, 1, 1, 1)
        self.InfoLabel_x = QtWidgets.QLabel(self.centralwidget)
        self.InfoLabel_x.setObjectName("InfoLabel_x")
        self.gridLayout_Info.addWidget(self.InfoLabel_x, 2, 3, 1, 1)
        self.InfoLabel_a = QtWidgets.QLabel(self.centralwidget)
        self.InfoLabel_a.setObjectName("InfoLabel_a")
        self.gridLayout_Info.addWidget(self.InfoLabel_a, 4, 3, 1, 1)
        self.line_0 = QtWidgets.QFrame(self.centralwidget)
        self.line_0.setFrameShape(QtWidgets.QFrame.VLine)
        self.line_0.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_0.setObjectName("line_0")
        self.gridLayout_Info.addWidget(self.line_0, 2, 2, 3, 1)
        self.InfoLabel_ang = QtWidgets.QLabel(self.centralwidget)
        self.InfoLabel_ang.setObjectName("InfoLabel_ang")
        self.gridLayout_Info.addWidget(self.InfoLabel_ang, 2, 0, 1, 1)
        self.InfoLabel_v = QtWidgets.QLabel(self.centralwidget)
        self.InfoLabel_v.setObjectName("InfoLabel_v")
        self.gridLayout_Info.addWidget(self.InfoLabel_v, 3, 3, 1, 1)
        self.InfoLabel_A = QtWidgets.QLabel(self.centralwidget)
        self.InfoLabel_A.setObjectName("InfoLabel_A")
        self.gridLayout_Info.addWidget(self.InfoLabel_A, 3, 0, 1, 1)
        self.InfoLabel_w = QtWidgets.QLabel(self.centralwidget)
        self.InfoLabel_w.setObjectName("InfoLabel_w")
        self.gridLayout_Info.addWidget(self.InfoLabel_w, 4, 0, 1, 1)
        self.InfoData_x = QtWidgets.QLabel(self.centralwidget)
        self.InfoData_x.setObjectName("InfoData_x")
        self.gridLayout_Info.addWidget(self.InfoData_x, 2, 4, 1, 1)
        self.InfoData_w = QtWidgets.QLabel(self.centralwidget)
        self.InfoData_w.setObjectName("InfoData_w")
        self.gridLayout_Info.addWidget(self.InfoData_w, 3, 1, 1, 1)
        self.InfoData_v = QtWidgets.QLabel(self.centralwidget)
        self.InfoData_v.setObjectName("InfoData_v")
        self.gridLayout_Info.addWidget(self.InfoData_v, 3, 4, 1, 1)
        self.InfoData_A = QtWidgets.QLabel(self.centralwidget)
        self.InfoData_A.setObjectName("InfoData_A")
        self.gridLayout_Info.addWidget(self.InfoData_A, 4, 1, 1, 1)
        self.InfoData_a = QtWidgets.QLabel(self.centralwidget)
        self.InfoData_a.setObjectName("InfoData_a")
        self.gridLayout_Info.addWidget(self.InfoData_a, 4, 4, 1, 1)
        self.angleSetter = QtWidgets.QSlider(self.centralwidget)
        self.angleSetter.setEnabled(True)
        self.angleSetter.setOrientation(QtCore.Qt.Horizontal)
        self.angleSetter.setObjectName("angleSetter")
        self.gridLayout_Info.addWidget(self.angleSetter, 1, 0, 1, 5)
        self.gridLayout_Info.setColumnStretch(0, 2)
        self.gridLayout_Info.setColumnStretch(1, 3)
        self.gridLayout_Info.setColumnStretch(3, 2)
        self.gridLayout_Info.setColumnStretch(4, 3)
        self.gridLayout_5.addLayout(self.gridLayout_Info, 6, 2, 1, 2)

        # 扰动部分网格布局
        self.gridLayout_Stri = QtWidgets.QGridLayout()
        self.gridLayout_Stri.setSizeConstraint(QtWidgets.QLayout.SetMinimumSize)
        self.gridLayout_Stri.setObjectName("gridLayout_Stri")
        self.in_Stir_w = QtWidgets.QLineEdit(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.in_Stir_w.sizePolicy().hasHeightForWidth())
        self.in_Stir_w.setSizePolicy(sizePolicy)
        self.in_Stir_w.setMinimumSize(QtCore.QSize(0, 0))
        self.in_Stir_w.setObjectName("in_Stir_w")
        self.gridLayout_Stri.addWidget(self.in_Stir_w, 0, 2, 1, 1)
        self.stirLabel_v = QtWidgets.QLabel(self.centralwidget)
        self.stirLabel_v.setObjectName("stirLabel_v")
        self.gridLayout_Stri.addWidget(self.stirLabel_v, 1, 1, 1, 1)
        self.pushButton_StirCCW = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_StirCCW.setMinimumSize(QtCore.QSize(0, 25))
        self.pushButton_StirCCW.setObjectName("pushButton_StirCCW")
        self.gridLayout_Stri.addWidget(self.pushButton_StirCCW, 0, 0, 1, 1)
        self.in_Stir_v = QtWidgets.QLineEdit(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.in_Stir_v.sizePolicy().hasHeightForWidth())
        self.in_Stir_v.setSizePolicy(sizePolicy)
        self.in_Stir_v.setObjectName("in_Stir_v")
        self.gridLayout_Stri.addWidget(self.in_Stir_v, 1, 2, 1, 1)
        self.stirLabel_w = QtWidgets.QLabel(self.centralwidget)
        self.stirLabel_w.setObjectName("stirLabel_w")
        self.gridLayout_Stri.addWidget(self.stirLabel_w, 0, 1, 1, 1)
        self.pushButton_StirCW = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_StirCW.setMinimumSize(QtCore.QSize(0, 25))
        self.pushButton_StirCW.setObjectName("pushButton_StirCW")
        self.gridLayout_Stri.addWidget(self.pushButton_StirCW, 0, 3, 1, 1)
        self.pushButton_StirL = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_StirL.setMinimumSize(QtCore.QSize(0, 25))
        self.pushButton_StirL.setObjectName("pushButton_StirL")
        self.gridLayout_Stri.addWidget(self.pushButton_StirL, 1, 0, 1, 1)
        self.pushButton_StirR = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_StirR.setMinimumSize(QtCore.QSize(0, 25))
        self.pushButton_StirR.setObjectName("pushButton_StirR")
        self.gridLayout_Stri.addWidget(self.pushButton_StirR, 1, 3, 1, 1)
        self.gridLayout_5.addLayout(self.gridLayout_Stri, 4, 2, 1, 2)
        self.pushButton_StirCCW.setEnabled(False)
        self.pushButton_StirCW.setEnabled(False)
        self.pushButton_StirL.setEnabled(False)
        self.pushButton_StirR.setEnabled(False)

        # 控制按钮部分网格布局
        self.gridLayout_Ctrl = QtWidgets.QGridLayout()
        self.gridLayout_Ctrl.setSizeConstraint(QtWidgets.QLayout.SetMinimumSize)
        self.gridLayout_Ctrl.setObjectName("gridLayout_Ctrl")
        self.pushButton_Pause = QtWidgets.QPushButton(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pushButton_Pause.sizePolicy().hasHeightForWidth())
        self.pushButton_Pause.setSizePolicy(sizePolicy)
        self.pushButton_Pause.setMinimumSize(QtCore.QSize(0, 25))
        self.pushButton_Pause.setObjectName("pushButton_Pause")
        self.gridLayout_Ctrl.addWidget(self.pushButton_Pause, 0, 0, 1, 1)
        self.pushButton_Start = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_Start.setMinimumSize(QtCore.QSize(0, 25))
        self.pushButton_Start.setObjectName("pushButton_Start")
        self.gridLayout_Ctrl.addWidget(self.pushButton_Start, 0, 1, 1, 2)
        self.pushButton_Reset = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_Reset.setMinimumSize(QtCore.QSize(0, 25))
        self.pushButton_Reset.setObjectName("pushButton_Reset")
        self.gridLayout_Ctrl.addWidget(self.pushButton_Reset, 2, 1, 1, 2)
        self.checkBox_autoReset = QtWidgets.QCheckBox(self.centralwidget)
        self.checkBox_autoReset.setObjectName("checkBox_autoReset")
        self.gridLayout_Ctrl.addWidget(self.checkBox_autoReset, 2, 0, 1, 1)
        self.gridLayout_5.addLayout(self.gridLayout_Ctrl, 4, 0, 1, 1)
        #中心布局的尺寸比例关系
        self.gridLayout_5.setColumnStretch(0,1)
        self.gridLayout_5.setColumnStretch(3, 1)

        #把中心网格布局放到中心窗口上
        MainWindow.setCentralWidget(self.centralwidget)

        #菜单栏和状态栏
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 940, 26))
        self.menubar.setObjectName("menubar")
        self.menu_help = QtWidgets.QMenu(self.menubar)
        self.menu_help.setObjectName("menu_help")
        self.menu_future = QtWidgets.QMenu(self.menubar)
        self.menu_future.setObjectName("menu_future")
        self.menu_file = QtWidgets.QMenu(self.menubar)
        self.menu_file.setObjectName("menu_file")
        MainWindow.setMenuBar(self.menubar)


        self.action_file = QtWidgets.QAction(MainWindow)
        self.action_file.setObjectName("action_file")
        self.action_file.setShortcut("Ctrl+F")#设置快捷键

        self.action_help = QtWidgets.QAction(MainWindow)
        self.action_help.setObjectName("action_help")
        self.action_me = QtWidgets.QAction(MainWindow)
        self.action_me.setObjectName("action_me")
        self.action_future = QtWidgets.QAction(MainWindow)
        self.action_future.setObjectName("action_future")
        self.menu_help.addAction(self.action_help)
        self.menu_help.addAction(self.action_me)
        self.menu_future.addAction(self.action_future)
        self.menu_file.addAction(self.action_file)
        self.menubar.addAction(self.menu_file.menuAction())
        self.menubar.addAction(self.menu_help.menuAction())
        self.menubar.addAction(self.menu_future.menuAction())
        
        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.KD_AnglePos.setText(_translate("MainWindow", "KD："))
        self.KP_AnglePos.setText(_translate("MainWindow", "KP："))
        self.KI_AnglePos.setText(_translate("MainWindow", "KI："))
        self.label_DispSpe.setText(_translate("MainWindow", "位移速度环"))
        self.label_AngPos.setText(_translate("MainWindow", "摆角位置环"))
        self.KP_AngleSpd.setText(_translate("MainWindow", "KP:"))
        self.KI_AngleSpd.setText(_translate("MainWindow", "KI:"))
        self.KI_DispSpd.setText(_translate("MainWindow", "KI:"))
        self.KP_DispSpd.setText(_translate("MainWindow", "KP:"))
        self.KD_AngleSpd.setText(_translate("MainWindow", "KD:"))
        self.KD_DispSpd.setText(_translate("MainWindow", "KD:"))
        self.KP_DispPos.setText(_translate("MainWindow", "KP:"))
        self.label_DispPos.setText(_translate("MainWindow", "位移位置环"))
        self.KI_DispPos.setText(_translate("MainWindow", "KI:"))
        self.KD_DispPos.setText(_translate("MainWindow", "KD:"))
        self.label_AngSpd.setText(_translate("MainWindow", "摆角速度环"))
        self.InfoLabel_x.setText(_translate("MainWindow", "位移："))
        self.InfoLabel_a.setText(_translate("MainWindow", "加速度："))
        self.InfoLabel_ang.setText(_translate("MainWindow", "角度："))
        self.InfoLabel_v.setText(_translate("MainWindow", "速度："))
        self.InfoLabel_A.setText(_translate("MainWindow", "角速度："))
        self.InfoLabel_w.setText(_translate("MainWindow", "角加速度："))
        self.stirLabel_v.setText(_translate("MainWindow", "扰动速度："))
        self.pushButton_StirCCW.setText(_translate("MainWindow", "逆时针扰动"))
        self.stirLabel_w.setText(_translate("MainWindow", "扰动角速度："))
        self.pushButton_StirCW.setText(_translate("MainWindow", "顺时针扰动"))
        self.pushButton_StirL.setText(_translate("MainWindow", "向左扰动"))
        self.pushButton_StirR.setText(_translate("MainWindow", "向右扰动"))
        self.pushButton_Pause.setText(_translate("MainWindow", "暂停"))
        self.pushButton_Start.setText(_translate("MainWindow", "启动"))
        self.pushButton_Reset.setText(_translate("MainWindow", "复位"))
        self.checkBox_autoReset.setText(_translate("MainWindow", "   自动复位"))
        self.InfoData_ang.setText(_translate("MainWindow", "0.0"))
        self.InfoData_x.setText(_translate("MainWindow", "0.0"))
        self.InfoData_w.setText(_translate("MainWindow", "0.0"))
        self.InfoData_v.setText(_translate("MainWindow", "0.0"))
        self.InfoData_A.setText(_translate("MainWindow", "0.0"))
        self.InfoData_a.setText(_translate("MainWindow", "0.0"))
        self.EnableBox_AnglePos.setText(_translate("MainWindow", "使能"))
        self.EnableBox_AngleSpd.setText(_translate("MainWindow", "使能"))
        self.EnableBox_DispPos.setText(_translate("MainWindow", "使能"))
        self.EnableBox_DispSpd.setText(_translate("MainWindow", "使能"))
        self.out_DispSpd.setText(_translate("MainWindow", "out:"))
        self.out_DispPos.setText(_translate("MainWindow", "out:"))
        self.out_AngPos.setText(_translate("MainWindow", "out："))        
        self.out_AngSpd.setText(_translate("MainWindow", "out："))
        self.outData_DispPos.setText(_translate("MainWindow", "0.00"))
        self.outData_AngPos.setText(_translate("MainWindow", "0.00"))
        self.outData_AngSpd.setText(_translate("MainWindow", "0.00"))
        self.outData_DispSpd.setText(_translate("MainWindow", "0.00"))
        self.menu_help.setTitle(_translate("MainWindow", "帮助"))
        self.menu_future.setTitle(_translate("MainWindow", "高级设置"))
        self.menu_file.setTitle(_translate("MainWindow", "文件"))
        self.action_file.setText(_translate("MainWindow", "文件选择器"))
        self.action_help.setText(_translate("MainWindow", "使用说明"))
        self.action_me.setText(_translate("MainWindow", "作者"))
        self.action_future.setText(_translate("MainWindow", "待开发"))
