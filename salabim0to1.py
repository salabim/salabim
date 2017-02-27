import os
import re

data=[]
#data.append(('from Salabim import \*','import salabim as sim'))
data.append(('SalabimComponent','sim.Component'))
data.append(('SalabimResource','sim.Resource'))
data.append(('SalabimQueue','sim.Queue'))
data.append(('SalabimEnvironment','sim.Environment'))
data.append(('Animation','sim.Animation'))
data.append(('salabim_random','sim.random'))
data.append(('main','sim.main'))
data.append(('\.sim.main','.main'))
data.append(('inf','sim.inf'))
data.append(('\.sim.inf','.inf'))
data.append(('nan','sim.nan'))
data.append(('\.sim.nan','.nan'))
data.append(('trace','sim.trace'))
data.append(('\.sim.trace','.trace'))
data.append(('now','sim.now'))
data.append(('\.sim.now','.now'))
data.append(('run','sim.run'))
data.append(('\.sim.run','.run'))
data.append(('default_env','sim.default_env'))
data.append(('.reset_env','.reset'))
data.append(('reset_env','sim.default_env.reset'))
data.append(('Uniform','sim.Uniform'))
data.append(('Constant','sim.Constant'))
data.append(('Exponential','sim.Exponential'))
data.append(('Normal','sim.Normal'))
data.append(('Triangular','sim.Triangular'))
data.append(('Cdf','sim.Cdf'))
data.append(('Pdf','sim.Pdf'))
data.append(('Distribution_from_string','sim.Distribution'))

for filename0 in os.listdir():
    if filename0.endswith('.py'):
        f = open(filename0,'r')
        filedata = f.read()
        f.close()
        
        if ('from Salabim import *' in filedata) and not ('salabim0to1' in filedata):

            filedata=filedata.replace('from Salabim import *','import salabim as sim')
            filedata=filedata.replace('.status==','.is_')
            filedata=filedata.replace('def action(','def process(')
            filedata=filedata.replace('proc=','process=')            
            filedata=filedata.replace('=','\1')
            for d in data:
                filedata=re.sub(r'\b'+d[0]+r'\b',d[1],filedata)
            filename1=filename0.replace('.py','1.py')
            filedata=filedata.replace('\1','=')
                           
            f = open(filename1,'w')
            f.write(filedata)
            f.close()
            
            print ('converted',filename0,'to',filename1)
            
