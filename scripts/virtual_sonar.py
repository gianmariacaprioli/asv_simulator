#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import NavSatFix
from std_msgs.msg import Float64
import pandas as pd
from scipy.spatial import KDTree
import numpy as np
from ament_index_python.packages import get_package_share_directory
import os


class VirtualDepthSensor(Node):
    def __init__(self):
        super().__init__('virtual_depth_sensor')
        pkg_dir = get_package_share_directory('asv_simulator')

        # --- CONFIGURAZIONE ---
        # Sostituisci con il percorso reale del tuo file
        csv_path = os.path.join(
                    pkg_dir,
                    'include',
                    'depth_table.csv'
                    )
        
        # Sostituisci con i nomi ESATTI delle colonne nel tuo CSV
        col_lon = 'X'      # Longitudine
        col_lat = 'Y'      # Latitudine
        col_depth = 'Z'    # Profondità
        # ----------------------
        
        self.get_logger().info('Caricamento batimetria in corso. Attendere...')
        try:
            # Carica il CSV usando pandas
            df = pd.read_csv(csv_path)
            
            # Pulisci eventuali righe vuote
            df = df.dropna(subset=[col_lat, col_lon, col_depth])
            
            # Crea l'albero per la ricerca spaziale iper-veloce
            self.coords = np.vstack((df[col_lat], df[col_lon])).T
            self.depths = df[col_depth].values
            self.kdtree = KDTree(self.coords)
            
            self.get_logger().info(f'Batimetria caricata con successo: {len(self.depths)} punti indicizzati.')
        except Exception as e:
            self.get_logger().error(f'Errore critico nel caricamento del CSV: {e}')
            return

        # Sottoscrizione al GPS della barca
        self.subscription = self.create_subscription(
            NavSatFix,
            '/vessel_v2/gps/fix', # Sostituisci se il topic GPS ha un nome diverso
            self.gps_callback,
            10)
            
        # Publisher della profondità trovata
        self.publisher = self.create_publisher(Float64, '/vessel_v2/virtual_depth', 10)

    def gps_callback(self, msg):
        # Estrai le coordinate correnti
        current_lat = msg.latitude
        current_lon = msg.longitude
        
        # Trova l'indice del punto più vicino nel KD-Tree
        distance, index = self.kdtree.query([current_lat, current_lon])
        
        # Recupera la profondità corrispondente
        current_depth = self.depths[index]
        
        # Pubblica il dato
        depth_msg = Float64()
        depth_msg.data = float(current_depth)
        self.publisher.publish(depth_msg)
        
        # Stampa a schermo ogni tanto per verifica
        self.get_logger().info(
        f'GPS: {current_lat:.5f}, {current_lon:.5f} | Profondita: {current_depth:.2f} m'
    )

def main(args=None):
    rclpy.init(args=args)
    node = VirtualDepthSensor()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()