// frontend/components/CoordinateInputMap.js
'use client';

import { MapContainer, TileLayer, Marker, useMapEvents } from 'react-leaflet'; // Removed Popup as it's not used for input
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { useState, useEffect } from 'react';

// Correction pour l'icône par défaut de Leaflet (comme dans MapComponent.js)
if (typeof window !== "undefined") {
    delete L.Icon.Default.prototype._getIconUrl;
    L.Icon.Default.mergeOptions({
      iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
      iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
      shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
    });
}

// Composant interne pour gérer les événements de clic sur la carte
function MapClickHandler({ onMapClick, selectedPosition }) {
  useMapEvents({
    click(e) {
      onMapClick(e.latlng); // e.latlng contient { lat, lng }
    },
  });

  // Affiche un marqueur à la position sélectionnée
  return selectedPosition ? <Marker position={[selectedPosition.lat, selectedPosition.lng]}></Marker> : null;
}

export default function CoordinateInputMap({ value, onChange }) {
  // `value` est un objet { lat, lng } ou null
  // `onChange` est une fonction qui sera appelée avec { lat, lng }

  const [selectedPosition, setSelectedPosition] = useState(value || null);
  const defaultCenter = [46.603354, 1.888334]; // Centre de la France
  const defaultZoom = 5;

  // Mettre à jour la position si la prop `value` change de l'extérieur
  useEffect(() => {
    if (value && typeof value.lat === 'number' && typeof value.lng === 'number') {
        setSelectedPosition(value);
    } else {
        setSelectedPosition(null);
    }
  }, [value]);

  const handleMapClick = (latlng) => {
    // latlng from Leaflet is { lat, lng }. Ensure this is what's passed up.
    const newPos = { lat: latlng.lat, lng: latlng.lng };
    setSelectedPosition(newPos);
    if (onChange) {
      onChange(newPos); // Notifier le parent des nouvelles coordonnées
    }
  };

  // Determine center and zoom for the map
  // If a position is selected, center on it with a closer zoom.
  // Otherwise, use default center and zoom.
  const mapCenter = selectedPosition ? [selectedPosition.lat, selectedPosition.lng] : defaultCenter;
  const mapZoom = selectedPosition ? 13 : defaultZoom;

  if (typeof window === "undefined") {
    return <div style={{ height: '300px', width: '100%', border: '1px solid #ccc', borderRadius: '4px', display:'flex', alignItems:'center', justifyContent:'center', backgroundColor:'#f0f0f0' }}>Chargement de la carte...</div>;
  }

  return (
    <div className="space-y-2">
      <div style={{ height: '300px', width: '100%', border: '1px solid #ccc', borderRadius: '4px' }}>
        <MapContainer
            center={mapCenter}
            zoom={mapZoom}
            scrollWheelZoom={true}
            style={{ height: '100%', width: '100%' }}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <MapClickHandler onMapClick={handleMapClick} selectedPosition={selectedPosition} />
        </MapContainer>
      </div>
      {selectedPosition && (
        <div className="text-sm text-gray-700">
          Position sélectionnée : <br/>
          Latitude: {selectedPosition.lat.toFixed(6)}, Longitude: {selectedPosition.lng.toFixed(6)}
        </div>
      )}
      {!selectedPosition && (
        <div className="text-sm text-gray-500">
          Cliquez sur la carte pour sélectionner une position.
        </div>
      )}
    </div>
  );
}
