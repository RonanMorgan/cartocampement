// frontend/app/visualisation/page.js
'use client';

import { useAuth } from '@/context/AuthContext';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';
import dynamic from 'next/dynamic'; // Pour importer dynamiquement le composant de carte

// Importer dynamiquement le composant de carte car Leaflet accède à l'objet `window`
const MapComponentWithNoSSR = dynamic(() => import('@/components/MapComponent'), {
  ssr: false, // Désactiver le rendu côté serveur pour ce composant
  loading: () => <p>Chargement de la carte...</p> // Optional loading component
});

export default function VisualisationPage() {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) {
      router.push('/connexion');
    }
  }, [user, loading, router]);

  if (loading) { // Combined loading and initial user check
    return <div className="container mx-auto p-4 text-center">Chargement de la session...</div>;
  }

  if (!user) {
    // This state might be briefly visible before redirection, or if redirection fails.
    return <div className="container mx-auto p-4 text-center">Vous devez être connecté pour voir cette page. Redirection...</div>;
  }

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Visualisation des Données</h1>
      <div style={{ height: '600px', width: '100%' }} className="rounded-lg shadow-md">
        <MapComponentWithNoSSR />
      </div>
      {/* Plus tard: ajouter des filtres et des listes de données ici */}
    </div>
  );
}
