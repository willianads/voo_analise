#_________________Bibliotecas_______________________
#from PyQt4.QtCore import QSettings
from PyQt4.QtCore import *
from leitura_cp_vect import *
import time
import math
import numpy as np
from matplotlib import pyplot as plt
from osgeo import gdal
from osgeo import gdal_array
from osgeo import osr

#___________________Arquivos entrada______________________
cps_arquivo='C:\\willian\\plano_voo\\correto_pack4\\dados\\cps_geo.txt'  #criar interface para chamar arquivo de CP
srtm_arquivo=  "C:\\willian\\plano_voo\\correto_pack4\\dados\\srtm_rio_geo.tif"
camera_arquivo='C:\\willian\\plano_voo\\correto_pack4\\dados\\camera.cam'

#___________________Arquivos Saida________________________________________
covermap_arquivo='C:\\willian\\plano_voo\\correto_pack4\\dados\\covermap.tif'
gsdmap_arquivo='C:\\willian\\plano_voo\\correto_pack4\\dados\\gsdmap.tif'
shape_arquivo='C:\\willian\\plano_voo\\correto_pack4\\dados\\frames.shp'

#___________________Estabelece projecoes e transforamcoes utilizadas__________________________
crsSrc = QgsCoordinateReferenceSystem(4326)    # WGS 84 Geo
crsDest = QgsCoordinateReferenceSystem(32723)  # 3395 WGS 84 Mercator Proj
GeoToMerc = QgsCoordinateTransform(crsSrc, crsDest)
MercToGeo = QgsCoordinateTransform(crsDest, crsSrc)
QSettings().setValue("/Projections/defaultBehaviour", "useGlobal")

#______________________funcao de convercao de lista de verices em poligono__________________
def poligonoOrdena(vetor):
    ponto_z=None
    
    segun_list=[]
    prima_list=[]
    
    for ponto in vetor:
        if ponto[1]!= ponto_z:
            prima_list.append(ponto)
        else:
            segun_list.append(ponto)
        ponto_z=ponto[1]
    
    segun_list.reverse()
    poligono=prima_list+segun_list
    poligono.append(vetor[0])
    
    Qpontos=[]
    for ponto in poligono:
        Qpontos.append(QgsPoint(ponto[0],ponto[1]))
        
    return Qpontos

#___________________Inicia Tempo____________________
t1_inicio_programa = time.clock()

#__________________Dados da camera_______________________

f, x_min, x_max, y_min, y_max, pixel =Ler_Cam(camera_arquivo)

#__________________Ler os CPS_______________________
cps,pontosBorda,numero_cps=Ler_Cps(cps_arquivo,'\t')

#__________________Ler Srtm______________________

raster_gdal = gdal.Open(srtm_arquivo)
raster_numpy = np.array(raster_gdal.GetRasterBand(1).ReadAsArray())
geoTransform = raster_gdal.GetGeoTransform()

xmin = geoTransform[0]
ymax = geoTransform[3]

raster_width = raster_gdal.RasterXSize
raster_height = raster_gdal.RasterYSize

xmax = xmin + geoTransform[1]*raster_width
ymin = ymax + geoTransform[5]*raster_height

raster_extent = QgsRectangle (xmin, ymin, xmax, ymax)

covermap=(np.zeros((raster_height,raster_width))) #cria imagens vazias para receber valores
gsdmap=(np.zeros((raster_height,raster_width))) #cria imagens vazias para receber valores

#________________Extrai apenas x,y,x dos cps_________
cpsCps_Geo=[]
for p in cps:
    cpsCps_Geo.append(QgsPoint(float(p[1]),float(p[2])))

#____________converte cpsCps e extent em Mercator__________
cpsCps_Merc=[]
for a in cpsCps_Geo:
    pt = GeoToMerc.transform(a)
    cpsCps_Merc.append(pt)

raster_extent_Merc=GeoToMerc.transform(raster_extent)

#_______________Extrair valores do rectangle para determinar X e Y________
srtm_xmax=raster_extent_Merc.xMaximum()
srtm_xmin=raster_extent_Merc.xMinimum()
srtm_ymax=raster_extent_Merc.yMaximum()
srtm_ymin=raster_extent_Merc.yMinimum()

pixel_xsize=(srtm_xmax-srtm_xmin)/(raster_width)
pixel_ysize=(srtm_ymax-srtm_ymin)/(raster_height)

#_________________cria estrutura para histograma de cada frames______________
histograma_frame=[]
i=0
while i<numero_cps:
    histograma_frame.append([])
    i=i+1
#_______________Percorrer Pixels__________________________

sum_elev=0
pix_cont=0
GSD_max = 0
GSD_min = 10000
Y_ini=(srtm_ymax-(pixel_ysize/2))
X_ini=(srtm_xmin+(pixel_xsize/2))

for y in range(raster_height):
    
    Y= Y_ini - (pixel_ysize*y)
    
    for x in range(raster_width):
        X= X_ini + (pixel_xsize*x)
        Z = raster_numpy[y,x]
        i=0
        if Z != 'nan' and Z > -9000 and Z < 9000:
            pix_cont +=1
            sum_elev += Z
            i=0
            pixel_valor=0
            while i<numero_cps: #!!!LEMBRAR so pontos sobre o extent
                coberto=Ponto_visivel(cpsCps_Merc[i][0],cpsCps_Merc[i][1],cps[i][3],cps[i][4],cps[i][5],cps[i][6],X,Y,Z,f,x_min,x_max,y_min,y_max)
                
                if coberto != cps[i][8]: #entrando
                    pontosBorda[i].append([X,Y])
                    if cps[i][8]==0:
                        cps[i][8] = 1
                    else:
                        cps[i][8] = 0
                    
                GSD=GDS_Calc(cpsCps_Merc[i][0],cpsCps_Merc[i][1],cps[i][3],cps[i][4],cps[i][5],cps[i][6],X,Y,Z,f,pixel)
                if coberto==1:
                    pixel_valor=pixel_valor+1
                    if GSD<GSD_min:
                        GSD_min=GSD
                    if GSD>GSD_max:
                        GSD_max=GSD
                    
                    histograma_frame[i].append((GSD))
                i=i+1
            covermap[y,x]=pixel_valor
            gsdmap[y,x]=GSD_min  
            
mean=sum_elev/pix_cont

#______________________Salva imagem resultante_____________________________
xmin,ymin,xmax,ymax = [raster_extent.xMinimum(),raster_extent.yMinimum(),raster_extent.xMaximum(),raster_extent.yMaximum()]
nrows,ncols = covermap.shape
xres = (xmax-xmin)/float(ncols)
yres = (ymax-ymin)/float(nrows)
geotransform=(xmin,xres,0,ymax,0, -yres)

output_raster = gdal.GetDriverByName('GTiff').Create(covermap_arquivo,ncols, nrows, 1 ,gdal.GDT_Float32)  # Open the file
output_raster.SetGeoTransform(geotransform)  # Specify its coordinates
srs = osr.SpatialReference()                 # Establish its coordinate encoding
srs.ImportFromEPSG(4326)                     # This one specifies WGS84 lat long.
output_raster.SetProjection( srs.ExportToWkt() )   # Exports the coordinate system 
output_raster.GetRasterBand(1).WriteArray(covermap)   # Writes my array to the raster

output_raster = gdal.GetDriverByName('GTiff').Create(gsdmap_arquivo,ncols, nrows, 1 ,gdal.GDT_Float32)  # Open the file
output_raster.SetGeoTransform(geotransform)  # Specify its coordinates
srs = osr.SpatialReference()                 # Establish its coordinate encoding
srs.ImportFromEPSG(4326)                     # This one specifies WGS84 lat long.
output_raster.SetProjection( srs.ExportToWkt() )   # Exports the coordinate system 
output_raster.GetRasterBand(1).WriteArray(gsdmap)   # Writes my array to the raster

#________________Ordena e ajusta os pontoBorda em Poligonos_________________________
poligonosBorda=[]
i=0
while i<numero_cps:
    poligonoBorda=poligonoOrdena(pontosBorda[i])
    poligonosBorda.append(poligonoBorda)
    i=i+1

#__________________Devolve o poligonosBorda para Wgs Geo__________________________
i=0
j=0
poligonosBorda_Geo=poligonosBorda
for a in poligonosBorda:
    for b in a:
        pt = MercToGeo.transform(b)
        poligonosBorda_Geo[i][j] = pt
        j=j+1
    i=i+1
    j=0

#________________Lancar todos os poligonos Borda na Tela__________________________

layer =  QgsVectorLayer('Polygon', 'voo2' , "memory")  #cria layer, tipo e nome
provedor = layer.dataProvider()  #estabelece o layer como fonte de intformacao
layer.startEditing() #Inicia a edicao
provedor.addAttributes([QgsField("NOME", QVariant.String), QgsField("X", QVariant.Double),QgsField("Y", QVariant.Double),QgsField("Z", QVariant.Double),QgsField("GSDMax", QVariant.Double),QgsField("GSDMin", QVariant.Double),QgsField("GSDMed", QVariant.Double)])

i=0
while i<numero_cps:
    
    estat=np.array(histograma_frame[i])
    estatmax=estat.max()
    estatmin=estat.min()
    estatmean=estat.mean()
    
    poly = QgsFeature()  #cria a feicao vazia
    poly.setGeometry(QgsGeometry.fromPolygon([poligonosBorda_Geo[i]])) #atribui a geometria
    poly.setAttributes([cps[i][0],cps[i][1],cps[i][2],cps[i][3],estatmax.item(),estatmin.item(),estatmean.item()]) #atribui os atributos
    provedor.addFeatures([poly]) #adiciona feicao no provedor
    i=i+1

layer.commitChanges() #finaliza edicao
layer.updateExtents()
QgsMapLayerRegistry.instance().addMapLayers([layer])# atualiza a tela

error = QgsVectorFileWriter.writeAsVectorFormat(layer, shape_arquivo, "utf-8", None, "ESRI Shapefile")
if error == QgsVectorFileWriter.NoError:
    print "SHP foi salvo!"


#________________Finaliza contagem do Tempo________________________________________________
t2_inicio_programa = time.clock()
tempototal=t2_inicio_programa-t1_inicio_programa
tempo_txt="Hora de fim do programa: %s\n" % (str(tempototal))
print tempo_txt

'''

#http://pyqt.sourceforge.net/Docs/PyQt4/qimage.html biblioteca QT
#http://gis.stackexchange.com/questions/37238/writing-numpy-array-to-raster-file
#http://gis.stackexchange.com/questions/86812/how-to-draw-polygons-from-the-python-console
#https://www.siafoo.net/snippet/69/rev/1


'''