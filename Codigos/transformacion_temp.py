import osmnx as ox
import rasterio
from pyproj import Transformer # <--- Nueva herramienta vital
import os

print("Descargando el grafo del centro de la ciudad...")
G = ox.graph_from_point((29.0892, -110.9613), dist=12000, network_type='walk')

directorio_actual = os.path.dirname(os.path.abspath(__file__))
carpeta_principal = os.path.dirname(directorio_actual)
tif_path = os.path.join(carpeta_principal, 'GEE_Datos', 'Temperatura_Hermosillo_Verano2025.tif')

print("Cargando el GeoTIFF...")
src = rasterio.open(tif_path)

transformer = Transformer.from_crs("EPSG:4326", src.crs, always_xy=True)

print("Asignando temperaturas a los nodos...")
nodos_exitosos = 0 
for node_id, data in G.nodes(data=True):
    lon, lat = data['x'], data['y']
    
    x, y = transformer.transform(lon, lat)
    
    try:
        temp_val = next(src.sample([(x, y)]))[0]
        if temp_val > 0:
            data['temperatura_celsius'] = float(temp_val)
            nodos_exitosos += 1
        else:
            data['temperatura_celsius'] = None
    except:
        data['temperatura_celsius'] = None 

print(f"¡Éxito! Se encontró temperatura real para {nodos_exitosos} esquinas.")

print("Calculando la temperatura promedio para las calles...")
for u, v, key, data in G.edges(keys=True, data=True):
    temp_u = G.nodes[u].get('temperatura_celsius')
    temp_v = G.nodes[v].get('temperatura_celsius')
    
    if temp_u is not None and temp_v is not None:
        data['temperatura_celsius'] = round((temp_u + temp_v) / 2, 2)
    elif temp_u is not None:
        data['temperatura_celsius'] = round(temp_u, 2)
    elif temp_v is not None:
        data['temperatura_celsius'] = round(temp_v, 2)
    else:
        data['temperatura_celsius'] = None

print("Exportando a GeoJSON...")
nodos, aristas = ox.graph_to_gdfs(G)

aristas_export = aristas.copy()
for col in aristas_export.columns:
    if type(aristas_export[col].iloc[0]) == list:
        aristas_export[col] = aristas_export[col].astype(str)

carpeta_web = os.path.join(carpeta_principal, 'Datos_Web')
os.makedirs(carpeta_web, exist_ok=True)
geojson_path = os.path.join(carpeta_web, 'Calles_Hermosillo_Temperaturas_2025.geojson')

aristas_export.to_file(geojson_path, driver='GeoJSON')
print(f"¡Mapa web guardado exitosamente en:\n{geojson_path}")