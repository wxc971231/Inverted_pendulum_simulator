# 摆杆Rod类，主要用于摆杆运动模拟和显示
import numpy as np
import math


class Rod:
    __angle = 0.0           #转角(摆杆坐标系正方向（右,上）；屏幕坐标系正方形（右,下）)
    __pos = np.mat([0,0])   #下端点相对显示区的坐标
    __x = 0.0               #下端点水平位移

    __w = 0.0               #角速度
    __v = 0.0               #下端点水平速度

    __A = 0.0               #摆杆角加速度
    __a = 0.0               #下端点水平加速度
    
    __J = 0.0               #转动惯量
    __m = 0.0               #摆杆质量
    __M = 0.0               #滑车质量
    __l = 0.0               #杆长
    __F = 0.0               #下端点受到的水平力
    __t = 0.0               #计算周期

    def __init__(self,m,l,T):
        self.__m = m                
        self.__l = l        
        self.__J = m*l*l/3
        self.__t = T
        self.__M = 1000*m    #滑车质量设为摆杆的100倍
        
    def setm(self,M):
        self.__m = M 
    def getm(self):
        return self.__m
    def setM(self,m):
        self.__M = m 
    def getM(self):
        return self.__M   
    def setL(self,L):
        self.__l = L
    def getL(self):
        return self.__l
    def setT(self,T):
        self.__t = T
    def getT(self):
        return self.__t
    def setF(self,f):
        self.__F = f

    def setX(self,X):
        self.__x = X 
    def getX(self):
        return  self.__x
    def setPos(self,pos):
        self.__pos = pos 
    def getPos(self):
        return  self.__pos
    def setV(self,V):
        self.__v = V
    def getV(self):
        return self.__v
    def seta(self,a):
        self.__a = a
    def geta(self):
        return self.__a
        
    def setA(self,a):
        self.__A = a
    def getA(self):
        return self.__A  
    def setW(self,W):
        self.__w = W
    def getW(self):
        return self.__w     
    def setAngle(self,ang):
        self.__angle = ang %  360    
    def getAngle(self):
        return self.__angle

    def reset(self):
        self.__A = 0
        self.__w = 0
        self.__angle = 0
        self.__pos = np.mat([0,0])
        self.__a = 0
        self.__v = 0
        self.__x = 0
        
    # 返回摆杆在控件上绘制时对应直线的相对坐标
    def returnAsLine(self):
        COS = math.cos(math.radians(-90-self.__angle))  #转角(摆杆坐标系正方向（右,上）；屏幕坐标系正方向（右,下），把运动学分析中的夹角转换为旋转矩阵中的夹角)
        SIN = math.sin(math.radians(-90-self.__angle))
        R = np.mat([[COS,SIN],[-SIN,COS]])              #二维旋转矩阵（屏幕坐标系中的逆时针旋转）
        P0 = np.mat([[self.__l*100],[0]])               #画的时候杆伸长100倍画
        P1 = (R*P0).T                                   #摆杆方向向量                      
        return np.c_[self.__pos,self.__pos-P1]          #返回[[x0,y0,x1,y1]]形式的线段坐标 （方向向量加上杆下端点坐标得杆上端点坐标(注意正方向)）
    
    # 运动学分析
    def update(self):
        # 简化书写
        J = self.__J    
        m = self.__m
        M = self.__M          
        l = self.__l
        g = 9.8
        F = self.__F
        t = self.__t
         
        # 更新位移 & 角度
        self.__x += (self.__v*t + 0.5*self.__a*t*t)
        self.__angle += (self.__w*t + 0.5*self.__A*t*t)
        
        # 更新速度 & 角速度
        self.__v += self.__a * t
        self.__w += self.__A * t

        temp1 =J+m*l*l
        temp2 = m*m*l*l
        COS = math.cos(math.radians(self.__angle))
        SIN = math.sin(math.radians(self.__angle))
        W = self.__w

        # 更新加速度 & 角加速度
        self.__a = (temp1*F + m*l*temp1*SIN*W*W - temp2*SIN*COS) / (temp1*(M+m) - temp2*COS*COS)
        self.__A = (m*l*COS*F + temp2*SIN*COS*W*W - (M+m)*m*l*g*SIN) / (temp2*COS*COS - (M+m)*temp1)

     