# 文件File类，主要用来处理FileWidget的数据
from RodClass import Rod
from PIDClass import PID
import os

class File():
    def __init__(self,rod,ctrl):
        self.__head = 'Inverted pendulum simulator setting data'    # 验证这个txt文件存储的是模拟器设定数据
        self.__UiVersion = 'v1.0'                                   # Ui版本，如果Ui界面不同了解码会有数据错误
        self.__rod = rod
        self.__ctrl = ctrl

    def setUiVersion(self,ver):     
        self.__UiVersion = ver

    def setFileName(self,name):
        self.__name = name

    def setDir(self,dir):
        self.__dir = dir
    
    def getDir(self):
        return self.__dir

    def collecData(self):
        #rod = Rod(1,1,1)
        self.__rodData = [self.__rod.getm() , self.__rod.getM() , self.__rod.getL()]
        self.__pidData = [  self.__ctrl['AngPos'].getPIDPara(),
                            self.__ctrl['AngSpd'].getPIDPara(),
                            self.__ctrl['DispPos'].getPIDPara(),
                            self.__ctrl['DispSpd'].getPIDPara()  ]

    #在dir目录下存储一个叫fileName的.txt配置文件              
    def saveData(self,dir,fileName):
        path = dir + '/' + fileName
        coveredFlag = False #是否发生覆盖

        self.collecData()
        #print(self.__rodData)

        #如果有同名文件，删除原来的
        if os.access(path, os.F_OK):
            os.remove(path)
            coveredFlag = True    

        fp = open(path,'w') 
    
        #开始写入文件
        fp.write(self.__head+'\n\n')

        fp.write('UI version:\n')
        fp.write(self.__UiVersion+'\n\n')
        
        fp.write('Rod data:\n')
        fp.write('{0};{1};{2};\n\n'.format(*self.__rodData))
        
        fp.write('PID para:\n')
        fp.write('{0};{1};{2};{3};\n'.format(*(self.__pidData[0])))
        fp.write('{0};{1};{2};{3};\n'.format(*(self.__pidData[1])))
        fp.write('{0};{1};{2};{3};\n'.format(*(self.__pidData[2])))
        fp.write('{0};{1};{2};{3};\n\n'.format(*(self.__pidData[3])))

        fp.write('end')

        #写入完成
        fp.close()

        return coveredFlag

    # 加载配置文件
    def loadData(self,lines):
        PIDName = ['AngPos','AngSpd','DispPos','DispSpd']

        for i in range(9,13):
            paras = lines[i].split(';')
            self.__ctrl[PIDName[i-9]].setPIDPara(paras)





