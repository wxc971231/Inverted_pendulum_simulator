# 主程序文件，处理主窗口UI数据交互
import sys
import os
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QPainter,QColor,QFont,QPen
from PyQt5.QtGui import QIntValidator,QDoubleValidator,QRegExpValidator
from PyQt5.QtCore import *
import numpy as np
import math

from MainUi import Ui_MainWindow
from FileWidgetUi import FileUi,fileWiget
from RodClass import Rod
from PIDClass import PID
from MenuUi import Help

class Simulator(Ui_MainWindow):
    def __init__(self,mainwindow,rod,ctrl):
        super().__init__()
        self.setupUi(mainWindow,rod,ctrl)           #在mainWindow上建立UI,传入rod参数
        
        self.fileWidget = FileUi(fileWiget(),rod,ctrl)
        self.helpWidget = Help(QWidget())

        fileDir = os.getcwd()
        fileDir += '/setting'                       #默认的配置文件夹路径
        self.fileWidget.setFileDir(fileDir)

        self.__controller = ctrl
        self.__rod = rod
        self.__MW = mainwindow 

        self.__currentAngle = 0.0                   #点击推子瞬间摆杆的角度
        self.__reSetAngle = 0.0                     #复位推子时的摆杆角度

        self.angleSetter.setMinimum(0)              #设置推子的取值和步长和初始值
        self.angleSetter.setMaximum(360)
        self.angleSetter.setSingleStep(1)	
        self.angleSetter.setValue(180)

        self.in_Stir_v.setText('2')                 #扰动的缺省值
        self.in_Stir_w.setText('2')

        self.pushButton_StirCCW.setEnabled(False)
        self.pushButton_StirCW.setEnabled(False)
        self.pushButton_StirL.setEnabled(False)
        self.pushButton_StirR.setEnabled(False)

        self.checkBox_autoReset.setChecked(True)

        self.in_Stir_v.setValidator(QIntValidator(0,99))                    #拨动速度输入检测器（只能输入0~99的整数）
        self.in_Stir_w.setValidator(QIntValidator(0,99))

        regx = QRegExp("^[-+]?\d+(\.[0-9][0-9][0-9][0-9][0-9])?$ ")         #PID参数输入检测器（输入小数精度最多5位）
        validator_PID = QRegExpValidator(regx)

        self.pidInputUI = [ [self.in_KP_AngPos, self.in_KI_AngPos , self.in_KD_AngPos],         #pid参数的缺省值
                            [self.in_KP_AngSpd, self.in_KI_AngSpd , self.in_KD_AngSpd],
                            [self.in_KP_DispPos, self.in_KI_DispPos , self.in_KD_DispPos],                                                               
                            [self.in_KP_DispSpd, self.in_KI_DispSpd , self.in_KD_DispSpd]  ]
        
        for i in range(4):
            for j in range(3):
                self.pidInputUI[i][j].setText('0') 
                self.pidInputUI[i][j].setValidator(validator_PID)

        self.initUi()

    def initUi(self):
        self.widget.setKinematicsEnable(False)  #失能运动学分析

        self.pushButton_StirCW.clicked.connect(self.push_CW)
        self.pushButton_StirCCW.clicked.connect(self.push_CCW)
        self.pushButton_StirL.clicked.connect(self.push_L)
        self.pushButton_StirR.clicked.connect(self.push_R)

        self.pushButton_Pause.clicked.connect(self.stopPaintRod)
        self.pushButton_Start.clicked.connect(self.startPaintRod)
        self.pushButton_Reset.clicked.connect(self.resetRod)

        self.angleSetter.sliderPressed.connect(self.startSetAngle)
        self.angleSetter.valueChanged.connect(self.settingAngle)
        self.angleSetter.sliderReleased.connect(self.angleSetted)
    
        self.widget.rodRepaintSignal.connect(self.rodDataUpdate)
        self.widget.PIDCalSignal.connect(self.pidOutUpdate)
        self.widget.failSignal.connect(self.resetRod)
        self.fileWidget.fileLoadedSignal.connect(self.loaded)

        self.EnableBox_AnglePos.toggled.connect(self.enable_AP)
        self.EnableBox_AngleSpd.toggled.connect(self.enable_AS)
        self.EnableBox_DispPos.toggled.connect(self.enable_DP)
        self.EnableBox_DispSpd.toggled.connect(self.enable_DS)
        self.checkBox_autoReset.toggled.connect(self.enable_AutoReset)
        
        self.fileWidget.setupUi()
        self.fileWidget.initUi()
        self.helpWidget.setupUi()

        self.action_file.triggered.connect(self.fileWidget.showWidget)
        self.action_help.triggered.connect(self.showHelp)
        self.action_me.triggered.connect(self.showMe)
    
    # 使能自动重置
    def enable_AutoReset(self):
        flag = self.checkBox_autoReset.isChecked()
        self.widget.setAuotReset(flag)
    
    # 显示HoeToUse.txt
    def showHelp(self):
        path = os.getcwd() + '/ReadMe/HowToUse.txt'
        self.helpWidget.showWidget(path)

    # 显示AboutMe.txt
    def showMe(self):
        path = os.getcwd() + '/ReadMe/AboutMe.txt'
        self.helpWidget.showWidget(path)

    # 发生配置文件加载，刷新主窗口界面
    def loaded(self,flag):      
        if flag:
            self.EnableBox_AnglePos.setChecked(self.__controller['AngPos'].isEnable())
            self.EnableBox_AngleSpd.setChecked(self.__controller['AngSpd'].isEnable())
            self.EnableBox_DispPos.setChecked(self.__controller['DispPos'].isEnable())
            self.EnableBox_DispSpd.setChecked(self.__controller['DispSpd'].isEnable())

            self.pidInputUI[0][0].setText(str(self.__controller['AngPos'].getKP()))
            self.pidInputUI[0][1].setText(str(self.__controller['AngPos'].getKI()))
            self.pidInputUI[0][2].setText(str(self.__controller['AngPos'].getKD()))

            self.pidInputUI[1][0].setText(str(self.__controller['AngSpd'].getKP()))
            self.pidInputUI[1][1].setText(str(self.__controller['AngSpd'].getKI()))
            self.pidInputUI[1][2].setText(str(self.__controller['AngSpd'].getKD()))

            self.pidInputUI[2][0].setText(str(self.__controller['DispPos'].getKP()))
            self.pidInputUI[2][1].setText(str(self.__controller['DispPos'].getKI()))
            self.pidInputUI[2][2].setText(str(self.__controller['DispPos'].getKD()))

            self.pidInputUI[3][0].setText(str(self.__controller['DispSpd'].getKP()))
            self.pidInputUI[3][1].setText(str(self.__controller['DispSpd'].getKI()))
            self.pidInputUI[3][2].setText(str(self.__controller['DispSpd'].getKD()))

    #使能角度位置环输入 
    def enable_AP(self):        
        flag = self.EnableBox_AnglePos.isChecked()
        self.__controller['AngPos'].setEnable(flag)
        for i in range(3):
            self.pidInputUI[0][i].setEnabled(flag)
            if self.pidInputUI[0][i].text() == '':
                self.pidInputUI[0][i].setText('0')
    
    #使能角度速度环输入
    def enable_AS(self):       
        flag = self.EnableBox_AngleSpd.isChecked()
        self.__controller['AngSpd'].setEnable(flag)
        for i in range(3):
            self.pidInputUI[1][i].setEnabled(flag)
            if self.pidInputUI[1][i].text() == '':
                self.pidInputUI[1][i].setText('0')

    #使能位移位置环输入
    def enable_DP(self):        
        flag = self.EnableBox_DispPos.isChecked()
        self.__controller['DispPos'].setEnable(flag)
        for i in range(3):
            self.pidInputUI[2][i].setEnabled(flag)
            if self.pidInputUI[2][i].text() == '':
                self.pidInputUI[2][i].setText('0')

    #使能位移速度环输入
    def enable_DS(self):        
        flag = self.EnableBox_DispSpd.isChecked()
        self.__controller['DispSpd'].setEnable(flag)
        for i in range(3):
            self.pidInputUI[3][i].setEnabled(flag)
            if self.pidInputUI[3][i].text() == '':
                self.pidInputUI[3][i].setText('0')

    #更新每一环pid输出
    def pidOutUpdate(self,res): 
        self.outData_AngPos.setText('{:.2f}'.format(res[0]))
        self.outData_AngSpd.setText('{:.2f}'.format(res[1]))
        self.outData_DispPos.setText('{:.2f}'.format(res[2]))
        self.outData_DispSpd.setText('{:.2f}'.format(res[3]))

    #更新信息
    def rodDataUpdate(self):    
        self.InfoData_A.setText('{:.2f}'.format(self.__rod.getA()))
        self.InfoData_w.setText('{:.2f}'.format(self.__rod.getW()))
        currentAng = self.__rod.getAngle()
        currentAng %= 360
        if currentAng > 180:
            currentAng -= 360
        self.InfoData_ang.setText('{:.2f}'.format(currentAng))
        self.InfoData_a.setText('{:.2f}'.format(self.__rod.geta()))
        self.InfoData_v.setText('{:.2f}'.format(self.__rod.getV()))
        self.InfoData_x.setText('{:.2f}'.format(self.__rod.getX()))

    #逆时针拨动
    def push_CCW(self):        
        str = self.in_Stir_w.text()
        if str != '':
            stir_W = int(str)
        else:
            stir_W = 0

        self.__rod.setW(self.__rod.getW() - stir_W)
    
    #顺时针拨动
    def push_CW(self):          
        str = self.in_Stir_w.text()
        if str != '':
            stir_W = int(str)
        else:
            stir_W = 0

        self.__rod.setW(self.__rod.getW() + stir_W)
   
    #向左拨动
    def push_L(self):           
        str = self.in_Stir_v.text()
        if str != '':
            stir_v = int(str)
        else:
            stir_v = 0

        self.__rod.setV(self.__rod.getV() - stir_v)

    #向右拨动
    def push_R(self):           
        str = self.in_Stir_v.text()
        if str != '':
            stir_v = int(str)
        else:
            stir_v = 0

        self.__rod.setV(self.__rod.getV() + stir_v)

    #暂停模拟
    def stopPaintRod(self):     
        self.widget.setKinematicsEnable(False)  #失能运动学分析
        self.widget.stopPaintRod()
        self.__currentAngle = self.__rod.getAngle() #记录当前角度
        
        self.angleSetter.setValue(180)
        self.angleSetter.setEnabled(True)

        self.pushButton_StirCCW.setEnabled(False)
        self.pushButton_StirCW.setEnabled(False)
        self.pushButton_StirL.setEnabled(False)
        self.pushButton_StirR.setEnabled(False)

        for i in range(4):
            for j in range(3):
                self.pidInputUI[i][j].setEnabled(True)
    
        self.EnableBox_AnglePos.setEnabled(True)
        self.EnableBox_AngleSpd.setEnabled(True)
        self.EnableBox_DispPos.setEnabled(True)
        self.EnableBox_DispSpd.setEnabled(True)
        
        self.enable_AP()
        self.enable_AS()        
        self.enable_DP()        
        self.enable_DS()

    #开始模拟
    def startPaintRod(self):    
        self.widget.startPaintRod()
        self.widget.setKinematicsEnable(True)  #使能运动学分析

        self.angleSetter.setEnabled(False)
        if self.in_Stir_w.text() == '':
            self.in_Stir_w.setText('0')
        if self.in_Stir_v.text() == '':
            self.in_Stir_v.setText('0')

        self.pushButton_StirCCW.setEnabled(True)
        self.pushButton_StirCW.setEnabled(True)
        self.pushButton_StirL.setEnabled(True)
        self.pushButton_StirR.setEnabled(True)

        for i in range(4):
            for j in range(3):
                self.pidInputUI[i][j].setEnabled(False)
                if self.pidInputUI[i][j].text() == '':
                    self.pidInputUI[i][j].setText('0')

        self.EnableBox_AnglePos.setEnabled(False)
        self.EnableBox_AngleSpd.setEnabled(False)
        self.EnableBox_DispPos.setEnabled(False)
        self.EnableBox_DispSpd.setEnabled(False)


        if self.EnableBox_AnglePos.isChecked():
            self.__controller['AngPos'].setKP(float(self.in_KP_AngPos.text())) 
            self.__controller['AngPos'].setKI(float(self.in_KI_AngPos.text())) 
            self.__controller['AngPos'].setKD(float(self.in_KD_AngPos.text())) 
            

        if self.EnableBox_AngleSpd.isChecked():
            self.__controller['AngSpd'].setKP(float(self.in_KP_AngSpd.text()))
            self.__controller['AngSpd'].setKI(float(self.in_KI_AngSpd.text()))
            self.__controller['AngSpd'].setKD(float(self.in_KD_AngSpd.text()))
            

        if self.EnableBox_DispPos.isChecked():
            self.__controller['DispPos'].setKP(float(self.in_KP_DispPos.text())) 
            self.__controller['DispPos'].setKI(float(self.in_KI_DispPos.text()))
            self.__controller['DispPos'].setKD(float(self.in_KD_DispPos.text()))
            


        if self.EnableBox_DispSpd.isChecked():
            self.__controller['DispSpd'].setKP(float(self.in_KP_DispSpd.text()))
            self.__controller['DispSpd'].setKI(float(self.in_KI_DispSpd.text()))
            self.__controller['DispSpd'].setKD(float(self.in_KD_DispSpd.text()))   
            
    #复位摆杆
    def resetRod(self):         
        #self.widget.stopPaintRod()             #停止paintEvent绘制
        self.__rod.reset()                      
        self.widget.setKinematicsEnable(False)  #失能运动学分析
        self.__controller['AngPos'].clear()     #重置pid控制器
        self.__controller['AngSpd'].clear()     #重置pid控制器
        self.__controller['DispPos'].clear()    #重置pid控制器
        self.__controller['DispSpd'].clear()    #重置pid控制器
        
        self.pidOutUpdate([0,0,0,0])            #清空pid输出

        self.__rod.setAngle(self.__reSetAngle)  #复位角度              
        self.widget.update()                    #调用update绘制摆杆
        self.widget.setKinematicsEnable(True)   #恢复运动学分析

    #点击了摆杆角度推子
    def startSetAngle(self):   
        self.widget.setKinematicsEnable(False)
        self.__currentAngle = self.__rod.getAngle() #记录当前角度

    #摆杆角度推子值发生变化
    def settingAngle(self):     
        self.__rod.setF(0.0)
        self.__rod.seta(0.0)
        self.__rod.setA(0.0)
        self.__rod.setW(0.0)
        self.__rod.setV(0.0)

        self.__rod.setAngle(self.__currentAngle + self.angleSetter.value() - 180)
        self.widget.update()
    
    #松开了摆杆角度推子
    def angleSetted(self):     
        self.widget.setKinematicsEnable(True)
        self.__reSetAngle = self.__rod.getAngle()
        #self.widget.setKinematicsEnable(True)  #恢复运动学分析


if __name__ == '__main__':
    app = QApplication(sys.argv)                #创建应用程序对象

    t = 0.0005                                  #计算周期
    PID_angPos = PID(0,0,0,t)                   #PID计算对象
    PID_angSpd = PID(0,0,0,t)
    PID_dispPos = PID(0,0,0,t)
    PID_dispSpd = PID(0,0,0,t)
    rod = Rod(0.3,1,t)                          #创建一个摆杆对象
    controller = {'AngPos':PID_angPos , 'AngSpd':PID_angSpd , 'DispPos':PID_dispPos , 'DispSpd':PID_dispSpd}
    
    mainWindow = QMainWindow()                  #创建主窗口
    S = Simulator(mainWindow,rod,controller)    #开始模拟
    
    mainWindow.show()                           #显示主窗口
    sys.exit(app.exec_())     