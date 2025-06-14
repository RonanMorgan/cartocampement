// frontend/app/questionnaires/[id]/page.js
'use client';

import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import { fetchApi } from '@/lib/api';
import dynamic from 'next/dynamic'; // Import pour dynamic

const CoordinateInputMapWithNoSSR = dynamic(
  () => import('@/components/CoordinateInputMap'),
  { ssr: false, loading: () => <p>Chargement de la carte...</p> }
);

export default function RemplirQuestionnairePage() {
  const params = useParams();
  const { id } = params || {};

  const [questionnaire, setQuestionnaire] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [formData, setFormData] = useState({});
  const [questionnairePassword, setQuestionnairePassword] = useState('');
  const [submitMessage, setSubmitMessage] = useState('');

  useEffect(() => {
    const loadQuestionnaire = async () => {
      setLoading(true);
      setError(null);
      setSubmitMessage('');
      try {
        const data = await fetchApi(`/questionnaires/${id}`);
        setQuestionnaire(data);
      } catch (err) {
        console.error("Erreur chargement questionnaire:", err);
        if (err.status === 401 || err.status === 403) {
            setError(`Ce questionnaire est protégé par mot de passe ou n'est pas accessible. Si un mot de passe est requis, veuillez le fournir ci-dessous pour la soumission.`);
            setQuestionnaire({
                id,
                title: "Questionnaire Protégé",
                description: "Ce questionnaire nécessite un mot de passe. Veuillez le fournir pour soumettre vos réponses.",
                elements: [],
                password: "protected"
            });
        } else {
            setError(err.data?.detail || err.message || "Impossible de charger le questionnaire.");
        }
      } finally {
        setLoading(false);
      }
    };
    if (id) {
      loadQuestionnaire();
    } else {
      setError("ID du questionnaire non spécifié dans l'URL.");
      setLoading(false);
    }
  }, [id]);

  const handleInputChange = (elementId, value, isCoordinates = false) => {
    if (isCoordinates) { // value sera un objet { lat, lng }
      setFormData(prev => ({
        ...prev,
        [elementId]: value // Stocker l'objet {lat, lng} directement
      }));
    } else { // Pour les inputs classiques, value est une string
      setFormData(prev => ({ ...prev, [elementId]: value }));
    }
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError(null);
    setSubmitMessage('');

    if (!questionnaire || (!questionnaire.elements && questionnaire.title !== "Questionnaire Protégé")) {
        setError("Le questionnaire n'est pas complètement chargé ou n'a pas de questions.");
        return;
    }

    const dataValuesPayload = {};
    let latitude = null;
    let longitude = null;

    // Itérer sur les éléments DÉFINIS dans le questionnaire pour construire le payload
    // et non sur les clés de formData qui pourraient contenir d'anciennes données si la structure du Q change.
    questionnaire.elements?.forEach(el => {
        const value = formData[el.id];
        if (value !== undefined && value !== null && value !== '') {
            if (el.field_type === 'map_coordinates') {
                // formData[el.id] should be an object like { lat: ..., lng: ... }
                if (value && typeof value.lat === 'number' && typeof value.lng === 'number') {
                    latitude = value.lat;
                    longitude = value.lng;
                }
                // Do not add map_coordinates to dataValuesPayload as it's handled at root
            } else {
                dataValuesPayload[el.label] = value; // Use label as key for backend
            }
        }
    });

    const submissionData = {
      data_values: dataValuesPayload,
      latitude: latitude,
      longitude: longitude,
      // submitter_name: "Un bénévole", // Placeholder, can be added as a form field
    };

    const headers = {};
    if (questionnaire.password) {
      if (!questionnairePassword) {
        setError('Ce questionnaire nécessite un mot de passe pour la soumission.');
        return;
      }
      headers['X-Questionnaire-Password'] = questionnairePassword;
    }

    try {
      await fetchApi(`/questionnaires/${id}/submit`, {
        method: 'POST',
        headers,
        body: submissionData,
      });
      setSubmitMessage('Vos réponses ont été soumises avec succès !');
      setFormData({});
      setQuestionnairePassword('');
    } catch (err) {
      console.error("Erreur de soumission:", err);
      setError(err.data?.detail || err.message || "Une erreur est survenue lors de la soumission.");
    }
  };

  if (loading && !error && !questionnaire) return <div className="container mx-auto p-4 text-center">Chargement du questionnaire...</div>;

  if (error && (!questionnaire || (questionnaire.title === "Questionnaire Protégé" && questionnaire.elements.length === 0) )) {
      if (questionnaire && questionnaire.password === "protected") {
        // Continue to render form below for password input, error is already set and will be displayed
      } else {
        return <div className="container mx-auto p-4 text-red-500 text-center">Erreur: {error}</div>;
      }
  }

  if (!questionnaire) return <div className="container mx-auto p-4 text-center">Questionnaire introuvable ou problème de chargement.</div>;

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-3xl font-bold mb-2">{questionnaire.title}</h1>
      <p className="text-gray-700 mb-6">{questionnaire.description}</p>

      {error && <p className="text-red-500 text-sm my-3 bg-red-100 p-3 rounded text-center">{error}</p>}
      {submitMessage && <p className="text-green-500 text-sm my-3 bg-green-100 p-3 rounded text-center">{submitMessage}</p>}

      <form onSubmit={handleSubmit} className="space-y-6 bg-white shadow-md rounded-lg p-6">
        {questionnaire.password && (
          <div>
            <label htmlFor="questionnairePassword" className="block text-sm font-medium text-gray-700">
              Mot de passe du questionnaire (requis pour soumettre)
            </label>
            <input
              type="password" name="questionnairePassword" id="questionnairePassword"
              value={questionnairePassword} onChange={(e) => setQuestionnairePassword(e.target.value)}
              required={questionnaire.elements && questionnaire.elements.length > 0 || questionnaire.password === "protected"}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
            />
          </div>
        )}

        {questionnaire.elements && questionnaire.elements.map(element => {
          if (element.field_type === 'map_coordinates') {
            return (
              <div key={element.id} className="mb-4 p-3 border rounded-md shadow-sm">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {element.label}
                </label>
                <CoordinateInputMapWithNoSSR
                  value={formData[element.id] || null}
                  onChange={(coords) => handleInputChange(element.id, coords, true)}
                />
                {formData[element.id] && formData[element.id].lat && formData[element.id].lng && (
                  <p className="text-xs text-gray-600 mt-2">
                    Sélectionné : Latitude: {formData[element.id].lat.toFixed(5)}, Longitude: {formData[element.id].lng.toFixed(5)}
                  </p>
                )}
              </div>
            );
          } else {
            return (
              <div key={element.id} className="mb-4">
                <label htmlFor={element.id.toString()} className="block text-sm font-medium text-gray-700">
                  {element.label}
                </label>
                <input
                  type={element.field_type === 'number' ? 'number' : (element.field_type === 'date' ? 'date' : (element.field_type === 'email' ? 'email' : 'text'))}
                  name={element.id.toString()}
                  id={element.id.toString()}
                  value={formData[element.id] || ''}
                  onChange={(e) => handleInputChange(element.id, e.target.value)}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                />
              </div>
            );
          }
        })}

        {(questionnaire.elements && questionnaire.elements.length > 0) || questionnaire.password === "protected" ? (
            <button
              type="submit"
              className="w-full inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
            >
              Soumettre les réponses
            </button>
        ) : (
            !loading && <p className="text-gray-600">Ce questionnaire ne contient actuellement aucune question.</p>
        )}
      </form>
    </div>
  );
}
