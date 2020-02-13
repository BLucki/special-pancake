 #-*- coding: utf8 -*-
import arcpy
from math import degrees, atan2
from collections import OrderedDict
from operator import itemgetter
import os
arcpy.env.overwriteOutput=1
      
def czytaj2(geometria):
    try:
        list_vertex=[]
        for part in geometria:
            for pnt in part:
                if pnt:
                    list_vertex.append([pnt.X, pnt.Y])
    except Exception, err:
            arcpy.AddError("blad czytaj2")
            arcpy.AddError(sys.exc_traceback.tb_lineno)
            arcpy.AddError(err.message)
    finally:
        return list_vertex

def split_coordinates(value):
    value1 = value
    x0 = value[0]
    del value1[0]
    end_point = value1.index(x0)+2
    out_polygon_vertex = value[0:end_point-1]
    in_polygon_vertex = value[end_point-1:-1]
    in_polygon_vertex.append(in_polygon_vertex[0])
    value = [out_polygon_vertex, in_polygon_vertex]
    return value
    del value1
    
def ReadGeometry(layer,angle_tolerance): # Czytanie obiektów z pluku
    
    list_polygon = []
    list_all_vertex = []
    desc = arcpy.da.SearchCursor(layer, ['SHAPE@'])
    for row in desc:
        list_polygon.append(row) # Lista z poligonem jako budynkow
        list_one_vertex = czytaj2(row[0]) #lista ze wsolrzednymi wierzcholkow jednego poligonu
        list_all_vertex.append(list_one_vertex)  #Lista ze wszystkimi wierzcholkami        
    del desc, row, list_one_vertex
    return list_all_vertex, list_polygon
    
def delete_vertex(lista,angle_tolerance): # Uproszczenie wierzcholkow o wartosc tolerancji
    list_true_vertex = []
    list_true_vertex.append(lista[0])
    for indexs in range(1, len(lista)-1):
        angle = math.degrees(abs(math.atan2((lista[indexs-1][1]-lista[indexs][1]),(lista[indexs-1][0]-lista[indexs][0]))-math.atan2((lista[indexs+1][1]-lista[indexs][1]),(lista[indexs+1][0]-lista[indexs][0]))))
        if angle>180+angle_tolerance or angle<180-angle_tolerance:
            list_true_vertex.append(lista[indexs])    
    list_true_vertex.append(lista[-1])
    del indexs
    return list_true_vertex

def create_line(lista_pkt): # Tworzenie polilinii jako obiektu
    point = arcpy.Point()
    array = arcpy.Array()
    for wiersz in lista_pkt:
        point.X = wiersz[0]
        point.Y = wiersz[1]
        array.add(point)
    polilinia = arcpy.Polyline(array)
    array.removeAll()
    del array, point, wiersz
    return polilinia

def create_multipolygon(coord_list): # Stworzenie poligonu - pierścienia jako obiektu
    #Author: Curtis Price, USGS
    parts = arcpy.Array()
    rings = arcpy.Array()
    ring = arcpy.Array()
    for part in coord_list:
        for pnt in part:
            if pnt:
                ring.add(arcpy.Point(pnt[0], pnt[1]))
            else:
                # null point - we are at the start of a new ring
                rings.add(ring)
                ring.removeAll()
        # we have our last ring, add it
        rings.add(ring)
        ring.removeAll()
        # if we only have one ring: remove nesting
        if len(rings) == 1:
            rings = rings.getObject(0)
        parts.add(rings)
        rings.removeAll()
    # if single-part (only one part) remove nesting
    if len(parts) == 1:
        parts = parts.getObject(0)
    return arcpy.Polygon(parts)

def create_polygon(lista_pkt): # Stworzenie poligonu jako obiektu
    point = arcpy.Point()
    array = arcpy.Array()
    for wiersz in lista_pkt:
        point.X = wiersz[0]
        point.Y = wiersz[1]
        array.add(point)
    obiekt = arcpy.Polygon(array)
    array.removeAll()
    del array, point, wiersz
    return obiekt

def  write_row(warstwa, nazwa, typ, lista): #Zapis danych do kolumny pliku
    AddField(warstwa, nazwa, typ)
    rows = arcpy.UpdateCursor(warstwa)
    for indeks, line in enumerate(rows):
        line.setValue(nazwa,lista[indeks])#[1])
        rows.updateRow(line)
    del rows
        
def AddField (warstwa, nazwa, typ):     #Dodanie pola
    arcpy.AddField_management(warstwa, nazwa, typ)

def read_column(warstwa,nazwa):     # Czytanie danych z kolumny pliku
    list_value = []
    cursor = arcpy.da.SearchCursor(warstwa, nazwa)
    for line in cursor:
        list_value.append(line)
    del line, cursor
    return list_value

def create_secant(value):           #Tworzenie siecznych
    licznik = 0
    list_secant=[]
    for j in range(0,len(value)-2):
        for k in range(j+2,len(value)-1):
            secant = create_line([value[j],value[k]])
            if not polygon.crosses(secant):
                list_secant.append([secant,secant.length])
                if j == 0:
                    licznik = licznik+1
    del (list_secant[licznik-1]),secant, k,j #Usuniecie linii laczacej pierwszy i ostatni punkt poligonu
    list_secant = sorted(list_secant, key=itemgetter(1))
    return list_secant

def cut_polygon(cut1,cut2,cutter): #Przeciecie poligonu polilinia
    value = []
    polygon = cut2
    value = czytaj2(polygon)
    value = delete_vertex(value, angle_tolerance)
    polygon = create_polygon(value)
    value = czytaj2(polygon)
    boolean = False
    i = 0
    cutter.append(cut1)
    return value, polygon, boolean, i, cutter

def point_secant(secant,x):     # Usuniecie z poligonu wierzcholkow obiektu zewnetrzenego
    start_end_secant = czytaj2(secant_shortest)
    if x =='multipart':
        start_end_secant = value[0]
    start_index = value.index(start_end_secant[0])
    end_index = value.index(start_end_secant[1])
    polygon_vertex = value[start_index:end_index+1]
    return polygon_vertex, start_index, end_index

def write_geometry(cutter, out_file): # Zapisanie geometrii do pliku
    for index in cutter:
        cursor = arcpy.da.InsertCursor(out_file, ["SHAPE@"])
        cursor.insertRow([index])
    del cursor

def secant_multipart(out_ring_value): #Tworzenie siecznych pierscienia
    list_secant = []
    licznik = 0
    for j in range(0,len(out_ring_value)-2):
        for k in range(j+2,len(out_ring_value)-1):
            secant = create_line([out_ring_value[j],out_ring_value[k]])
            if (not out_polygon.crosses(secant)) and (not in_polygon.crosses(secant)):
                list_secant.append([secant,secant.length])
                if j == 0:
                    licznik = licznik+1
    del (list_secant[licznik-1]) # Usuniecie linii laczacej pierwszy i ostatni punkt poligonu
    list_secant = sorted(list_secant, key=itemgetter(1))
    return list_secant

def cut_multipart(cut1,cut2,cutter): # Przeciecie pierscienia linia
    polygon = cut1
    value = czytaj2(polygon)
    out_ring_value = delete_vertex(value[0:-len(in_ring_value)], angle_tolerance)
    polygon = create_multipolygon([in_ring_value, out_ring_value])
    boolean = False
    i = 0
    cutter.append(cut2)
    return out_ring_value, boolean, cutter, i, polygon

if __name__ == "__main__":

    # Plik wyjsciowy
    print('Program może mieć problemy z multipoligonami (inne niż pierścienie')
    path = os.path.abspath(os.getcwd())
    print('Tworzenie pliku z wynikami')
    arcpy.CreateFeatureclass_management(path, 'czesci.shp', 'POLYGON')
    path = os.path.abspath(os.getcwd())+'\\'
    out_file = path + 'czesci.shp'
    arcpy.CreateFeatureclass_management(path, 'zgeneralizowane budynki.shp', 'POLYGON')
    out_file2 = path + 'zgeneralizowane budynki.shp'
    arcpy.CreateFeatureclass_management(path, 'sieczne.shp', 'POLYLINE')
    out_file3 = path + 'sieczne.shp'
    # Plik z danymi
    print(' Odczytywanie pliku')
    data_file = r"C:\Users\Błażej\Desktop\Program_PPG2\Zadanie\bud.shp"
    objectID = read_column(data_file, 'OBJECTID')

    # Wczytanie podanych parametrów
    angle_tolerance = input("Tolerancja kata (w stopniach): ")
    count_delete_vertex = input("Liczba odcietych wierzcholkow przez sieczna, np. dla czworokatow k = 2, dla trojkatow k = 1: ")
    end_count_vertex = 4

    #Definiowanie zmiennych
    Id=[]
    Id_s = []
    In_out=[]
    cutter = []
    main_part =[]
    i=0
    if arcpy.Exists(data_file):
        # Wczytywanie geometrii
        list_vertex,list_polygon = ReadGeometry(data_file,angle_tolerance)
        print('Liczba wczytanych obiektow: {}'.format(len(list_polygon)))
        for counter, value  in enumerate(list_vertex):
            obj = objectID[counter][0]
            print('Przetwarzanie obiektu: {}'.format(obj))
            if not list_polygon[counter][0].isMultipart: #Sprawdzenie czy poligon jest zwykły czy pierścieniem
                value = delete_vertex(value, 10)
                polygon = create_polygon(value)
                object_number = 0
                # Przetwarzanie calego budynku
                while polygon.pointCount > 4 + count_delete_vertex: # Warunek na liczbe wierzcholkow poligonu
                    list_secant = create_secant(value) #Tworzenie siecznych
                    boolean = True
                    print('     Iteracja: {}'.format(object_number))
                    # Tworzenie pojedycznego obiektu budynku
                    while boolean:
                        secant_shortest = list_secant[i][0] # Wybranie rozpatrywanej siecznej
                        if polygon.contains(secant_shortest): # Sprawdzenie czy sieczna jest zewnetrzna czy wewnetrzna
                            cut1,cut2 = polygon.cut(secant_shortest)
                            in_out_index = 1
                            write_geometry([secant_shortest], out_file3)
                            if cut1.area>cut2.area and cut2.pointCount == 3 + count_delete_vertex:
                                value, polygon, boolean, i,cutter = cut_polygon(cut2,cut1,cutter)
                            elif cut1.area<cut2.area and cut1.pointCount==3+count_delete_vertex:
                                value, polygon, boolean, i, cutter = cut_polygon(cut1,cut2,cutter)
                            else:
                                i=i+1
                        else:
                            #Rozpatrywanie ciecznej zewnetrznej
                            in_out_index = 0
                            polygon_vertex, start_index, end_index = point_secant(secant_shortest,'onepart') # Usuwanie punktow tworzacych uzupelnienie figury z poligonu
                            if len(polygon_vertex)==2 + count_delete_vertex:
                                for indeksy in range(end_index-1,start_index,-1):
                                    del value[indeksy]
                                boolean = False
                                poli = create_polygon(polygon_vertex) # Stworzenie poligonu jako uzupełnienia budynku
                                polygon = create_polygon(delete_vertex(value, angle_tolerance)) # Stworzenie nowego budynku
                                if poli.area>polygon.area: # Sprawdzenie ktory obiekt jest uzupelniajacy a ktory budynkiem
                                    x = polygon
                                    polygon = poli
                                    poli = x
                                    value = czytaj2(polygon)
                                    value = delete_vertex(value, angle_tolerance)
                                    del x
                                polygon = create_polygon(value)
                                cutter.append(poli)
                                i = 0
                            else:
                                i=i+1
                    # Przypisywanie utworzonych obiektow do listy 
                    Id.append(obj)
                    Id_s.append(object_number)
                    In_out.append(in_out_index)
                    object_number = object_number + 1
                out_ring_value = polygon.pointCount
                main_part.append(polygon)
                del value
            else:
             value = split_coordinates(value)
             out_ring_value = delete_vertex(value[0],angle_tolerance) # Upraszanie zewnetrznego i wewnetrznego obwodu
             in_ring_value = delete_vertex(value[1],angle_tolerance)
             polygon = create_multipolygon([in_ring_value,out_ring_value])
             object_number = 0
             # Przetwarzanie calego budynku
             while len(out_ring_value) > 4 + count_delete_vertex:
                boolean = True
                out_polygon = create_polygon(out_ring_value)
                in_polygon = create_polygon(in_ring_value)
                print('     Iteracja: {}'.format(object_number))
                # Tworzenie pojedynczego obiektu
                while boolean:
                    # Siecznie poligonu zewnetrznego
                    list_secant = secant_multipart(out_ring_value)
                    secant_shortest = list_secant[i][0]
                    
                    # Sieczna wewnetrzna
                    if polygon.contains(secant_shortest):
                        cut1,cut2 = polygon.cut(secant_shortest)
                        in_out_index = 1
                        write_geometry([secant_shortest],out_file3)
                        if cut1.area>cut2.area and cut2.pointCount == 3 + count_delete_vertex:
                            out_ring_value, boolean, cutter, i, polygon = cut_multipart(cut1,cut2,cutter)
                        elif cut1.area<cut2.area and cut1.pointCount==3+count_delete_vertex:
                            out_ring_value, boolean, cutter, i, polygon = cut_multipart(cut2,cut1,cutter)
                        else:
                            i=i+1
                    else:
                        # Sieczna zewnetrzna
                        in_out_index = 0
                        # Usuwanie punktow z punktow poligonu
                        start_end_secant = czytaj2(secant_shortest)
                        start_index = out_ring_value.index(start_end_secant[0])
                        end_index = out_ring_value.index(start_end_secant[1])
                        polygon_vertex = out_ring_value[start_index:end_index+1]
                        # Tworzenie uzupelniajacego obiektu
                        if len(polygon_vertex)==2 + count_delete_vertex:
                            for indeksy in range(end_index-1,start_index,-1):
                                del out_ring_value[indeksy]
                            poli = create_polygon(polygon_vertex)
                            out_ring_value = delete_vertex(out_ring_value, angle_tolerance)
                            polygon = create_multipolygon([in_ring_value,out_ring_value])
                            if poli.area>polygon.area:
                                x = polygon
                                polygon = poli
                                poli = x
                                value = czytaj2(polygon)
                                out_ring_value = value[0:-len(in_ring_value)]
                                out_ring_value = delete_vertex(out_ring_value, angle_tolerance)
                                del x
                            #polygon = create_multipolygon([in_ring_value,out_ring_value])
                            boolean = False
                            cutter.append(poli)
                            i = 0
                        else:
                            i=i+1
                # Przypisanie wartosci do tablicy
                Id.append(obj)
                Id_s.append(object_number)
                In_out.append(in_out_index)
                object_number = object_number + 1
             if len(out_ring_value)> 5:
                    print('Przy powyzszych parametrach nie da sie obiektu przeksztalcic do 4 wierzcholkow')
             print('___________________________')
             main_part.append(polygon)
        print('Zapisywanie danych do pliku, w folderze ze skryptem')
        print('Do pliku "czesci" zapisano dodane lub usuniete elementy, w pliku "zgeneralizowane budynki" zawarto budynki po dzialaniu algorytmu')
        # Zapis danych do pliku
        write_geometry(main_part,out_file2)
        write_geometry(cutter, out_file)
        write_row(out_file,'Id', 'Integer', Id)
        write_row(out_file,'Id_s', 'Integer', Id_s)
        write_row(out_file,'In_out', 'Integer', In_out)
    print('Ukonczono pomyslnie')
