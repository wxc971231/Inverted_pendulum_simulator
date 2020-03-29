# PID类，主要用于处理pid计算
class PID:
    def __init__(self,p,i,d,t):
        self.__KP = p
        self.__KI = i
        self.__KD = d

        self.__enabled = False  #是否使能此级闭环

        self.__ref = 0.0        #调节量的期望值（初始偏差）,初始化OFFSET
        self.__fdb = 0.0        #调节量的反馈值（调节后的偏差） ，初始化0 
        self.__Ek = 0.0         #当前的偏差
        self.__Sk = 0.0         #历史偏差（积分） 
        self.__Dk = 0.0         #最近两次偏差值之差 
        self.__Ek_1 = 0.0       #上次偏差
        self.__Ek_2 = 0.0       #本次偏差 
        self.__out = 0.0        #输出控制量 
        self.__outMax = 100.0   #最大100 
        self.__outMin = 100.0   #最小-100 
        self.__T = t            #采样周期（单片机系统中这个值应该用单片机定时器测，每轮计算时更新）

    def isEnable(self):
        return self.__enabled

    def setEnable(self,flag):
        self.__enabled = flag

    def setRef(self,ref):
        self.__ref = ref
    
    def setFdb(self,fdb):
        self.__fdb = fdb
    
    def setKP(self,kp):
        self.__KP = kp
    def getKP(self):
        return self.__KP

    def setKI(self,ki):
        self.__KI = ki
    def getKI(self):
        return self.__KI

    def setKD(self,kd):
        self.__KD = kd
    def getKD(self):
        return self.__KD

    def setT(self,t):
        self.__T = t
    def getT(self):
        return self.__T

    def getPIDPara(self):
        para = [self.__enabled,self.__KP,self.__KI,self.__KD]
        return para
    
    def setPIDPara(self,para):
        #print(para)
        if para[0] == 'True':
            self.setEnable(True)
        else:
            self.setEnable(False)
        
        for i in range(3):
            if para[i] == '': 
                para[i] = 0.0

        self.setKP(float(para[1]))
        self.setKI(float(para[2]))
        self.setKD(float(para[3]))

    def clear(self):
        self.__ref = 0.0        #调节量的期望值（初始偏差）,初始化OFFSET
        self.__fdb = 0.0        #调节量的反馈值（调节后的偏差） ，初始化0 
        self.__Ek = 0.0         #当前的偏差
        self.__Sk = 0.0         #历史偏差（积分） 
        self.__Dk = 0.0         #最近两次偏差值之差 
        self.__Ek_1 = 0.0       #上次偏差
        self.__Ek_2 = 0.0       #本次偏差 
        self.__out = 0.0        #输出控制量 

    def calculate(self):
        self.__Ek = self.__ref - self.__fdb
        self.__Sk += self.__Ek * self.__T
        
        self.__out = 1.0 * (self.__KP * self.__Ek + self.__KI * self.__Sk + self.__KD * self.__Dk)
#        if self.__out > self.__outMax:
#            self.__out = self.__outMax
#        if self.__out < self.__outMin:
#            self.__out = self.__outMin

        self.__Ek_1 = self.__Ek_2
        self.__Ek_2 = self.__Ek

        self.__Dk = (self.__Ek_2 - self.__Ek_1)/self.__T
        return self.__out

