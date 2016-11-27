from PyQt4.QtGui import QColor
from random import randint

#__________________________________________________________________________
#http://stackoverflow.com/questions/214359/converting-hex-color-to-rgb-and-vice-versa
def hex_to_rgb(value):
    value = value.lstrip('#')
    lv = len(value)
    return tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))

def rgb_to_hex(rgb):
    return "#%02x%02x%02x" % rgb
#___________________________________________________________________________

layer=None

layer= qgis.utils.iface.activeLayer()

if layer:
    try:
        features = layer.getFeatures()
        
        test="off"
        
        for feature in features:
            atributos = feature.attributes()
            if test=="off":
                value = int(atributos[0])
                test = "on"
    except:
        iface.messageBar().pushMessage("A camada selecionada nao possui atributo ID")
    
    label="cor randomica"
    categories = []
   
    
    for feicao in layer.getFeatures():
        
        R,G,B=0,0,0
        
        while (R+G+B)<60 or (R+G+B)>730:
    
            R=randint(0,255)
            G=randint(0,255)
            B=randint(0,255)
        
        rgb=(R,G,B)
        hexcor=rgb_to_hex(rgb)
        symbol = QgsSymbolV2.defaultSymbol(layer.geometryType())
        symbol.setColor(QColor(hexcor))
        categories.append(QgsRendererCategoryV2(value,symbol, label))
        value=value+1
    
    renderer = QgsCategorizedSymbolRendererV2("ID", categories)
    layer.setRendererV2(renderer)
    layer.triggerRepaint()

else:

    iface.messageBar().pushMessage("Por favor, selecione um layer valido")