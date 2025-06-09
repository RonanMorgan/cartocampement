// frontend/components/MapComponent.js
'use client';

import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { useEffect, useState } from 'react';
import { fetchApi } from '@/lib/api'; // Importer fetchApi

// Correction pour l'icône par défaut de Leaflet
if (typeof window !== "undefined") {
    delete L.Icon.Default.prototype._getIconUrl;
    L.Icon.Default.mergeOptions({
      iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
      iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
      shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
    });
}


export default function MapComponent() {
  const position = [46.603354, 1.888334]; // Centre de la France
  const [dataObjects, setDataObjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchDataObjects = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchApi('/data/'); // Token géré par fetchApi
        // Filtrer pour ne garder que les objets avec des coordonnées valides
        const validDataObjects = data.filter(obj => obj.latitude != null && obj.longitude != null);
        setDataObjects(validDataObjects);
      } catch (err) {
        console.error("Erreur récupération DataObjects:", err);
        setError(err.data?.detail || err.message || "Impossible de charger les données géographiques.");
      } finally {
        setLoading(false);
      }
    };
    fetchDataObjects();
  }, []); // Empty dependency array means this runs once on mount

  if (typeof window === "undefined") {
    // Should not happen due to dynamic import with ssr:false, but good practice
    return null;
  }

  if (loading) {
    return <p className="text-center p-4">Chargement des données cartographiques...</p>;
  }

  if (error) {
    return <p className="text-center text-red-500 p-4">Erreur: {error}</p>;
  }

  return (
    <MapContainer center={position} zoom={6} scrollWheelZoom={true} style={{ height: '100%', width: '100%' }}>
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {dataObjects.map(obj => (
        <Marker key={obj.id} position={[obj.latitude, obj.longitude]}>
          <Popup>
            <div className="space-y-1 max-w-xs"> {/* Added max-width for popup readability */}
              <h3 className="text-md font-semibold break-words">ID Objet: {obj.id}</h3>
              <p className="text-xs">Questionnaire ID: {obj.questionnaire_id}</p>
              <p className="text-xs">
                Soumis le: {new Date(obj.submission_date).toLocaleDateString('fr-FR', { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
              </p>
              {obj.submitter_name && <p className="text-xs break-words">Soumis par: {obj.submitter_name}</p>}

              <div className="mt-2 pt-2 border-t">
                <h4 className="text-sm font-medium mb-1">Données:</h4>
                {obj.data_values && Object.keys(obj.data_values).length > 0 ? (
                  <ul className="list-disc list-inside text-xs space-y-0.5">
                    {Object.entries(obj.data_values).map(([key, value]) => (
                      <li key={key} className="break-words"><strong>{key}:</strong> {String(value)}</li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-xs italic">Aucune donnée de valeur.</p>
                )}
              </div>

              {obj.additional_info && (
                <div className="mt-2 pt-2 border-t">
                    <h4 className="text-sm font-medium mb-1">Info additionnelle:</h4>
                    <p className="text-xs italic break-words">{obj.additional_info}</p>
                </div>
              )}
            </div>
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  );
}
