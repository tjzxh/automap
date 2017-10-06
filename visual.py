import plotly.plotly as py
import plotly
from plotly.graph_objs import *
import os
import numpy as np


mapbox_access_token = 'pk.eyJ1IjoidGp6eGgiLCJhIjoiY2o2cTUxN2hlMDZ6eTMycWpmNGJ6bTVrcSJ9.7nt0siqLHX2uaHsOVNF-fA'
plotly.tools.set_credentials_file(username='tjzxh', api_key='Faxs8vPpdsiAqtoMO2Zt')

#os.rename('vlog_solid_line.log.pcmap','0830.txt')
#all_data=np.loadtxt('pcmap.txt')
all_data=[]
with open('test.txt','r') as f:
    for line in f:
        every_line=list(map(float,line.split(',')))
        if np.size(every_line)==1:
            pass
        else:
            all_data.append(every_line)
    all_data=np.array(all_data)
    longi=all_data[:,0]
    lati=all_data[:,1]
    longi_str=[str(l) for l in longi]
    lati_str=[str(t) for t in lati]

data = Data([
    Scattermapbox(
        lat=lati_str,
        lon=longi_str,
        mode='markers',
        marker=Marker(
            size=9
        ),
        text=[],
    )
])
layout = Layout(
    autosize=True,
    hovermode='closest',
    mapbox=dict(
        accesstoken=mapbox_access_token,
        bearing=0,
        center=dict(
            lat=lati[10],
            lon=longi[10]
        ),
        pitch=0,
        zoom=50
    ),
)

fig = dict(data=data, layout=layout)
py.plot(fig, filename='Multiple Mapbox')