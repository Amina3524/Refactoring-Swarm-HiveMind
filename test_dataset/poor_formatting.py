import os,sys,json,math

def   add  (x,y):
  return   x+y

def multiply   (a,b):
    result= a*b
    if result>100:
        print("Large result")
    else:print("Small result")
    return result

class Calculator:
    def __init__(self):
        self.history=[]
    
    def calculate(self,operation,x,y):
        if operation=="add":
            result=add(x,y)
        elif operation=="multiply":
            result=multiply(x,y)
        else:
            result=None
        self.history.append(result)
        return result

# Problèmes:
# - Espacement incohérent
# - Imports sur une ligne
# - Indentation incorrecte
# - Pas de lignes vides entre fonctions