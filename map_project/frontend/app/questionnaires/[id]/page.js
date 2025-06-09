// frontend/app/questionnaires/[id]/page.js
'use client';

import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import { fetchApi } from '@/lib/api'; // Importer fetchApi
// Importer useAuth si on veut vérifier si l'utilisateur est le propriétaire pour bypasser le mdp
// import { useAuth } from '@/context/AuthContext';

export default function RemplirQuestionnairePage() {
  const params = useParams();
  const { id } = params || {}; // Ensure params is not null
  // const { user } = useAuth(); // Pourrait être utilisé pour vérifier la propriété

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
      setSubmitMessage(''); // Clear previous submit messages
      try {
        // Pour l'instant, on ne passe pas de X-Questionnaire-Password pour la lecture.
        // Le backend gère si le propriétaire y accède ou s'il est public sans mdp.
        // Si un mdp est requis pour la lecture par un anonyme, l'API lèvera une erreur.
        const data = await fetchApi(`/questionnaires/${id}`);
        setQuestionnaire(data);
      } catch (err) {
        console.error("Erreur chargement questionnaire:", err);
        if (err.status === 401 || err.status === 403) {
            setError(`Ce questionnaire est protégé par mot de passe ou n'est pas accessible. Si un mot de passe est requis, veuillez le fournir ci-dessous pour la soumission.`);
            // On met un questionnaire partiel pour que le champ mdp s'affiche si le questionnaire existe mais est protégé.
            // Le backend ne renvoie pas le titre si l'accès est refusé par mot de passe, donc on met un titre générique.
            // On se fie au fait que `questionnaire.password` sera présent dans la réponse (même si null) si le questionnaire existe.
            // Si le questionnaire n'existe pas (404), `err.data` pourrait ne pas avoir `password`.
            // Le backend, pour un GET sur un questionnaire protégé SANS token owner ET SANS X-Questionnaire-Password,
            // va retourner 401 ou 403 (selon le cas exact de la protection).
            // Il ne renverra PAS le questionnaire. Donc, si on arrive ici avec 401/403,
            // on sait qu'il est protégé. On va simuler un questionnaire avec un champ password pour que l'UI s'affiche.
            setQuestionnaire({
                id,
                title: "Questionnaire Protégé",
                description: "Ce questionnaire nécessite un mot de passe. Veuillez le fournir pour soumettre vos réponses.",
                elements: [], // Pas d'éléments affichés tant que le mot de passe n'est pas validé (pour la soumission)
                password: "protected" // Indicateur pour l'UI que le champ mdp est nécessaire pour la soumission
                                     // Note: le backend renvoie le hash du mot de passe s'il existe, ou null.
                                     // Si on a 401/403, on ne reçoit pas le questionnaire.
                                     // On met "protected" juste pour que `questionnaire.password` soit truthy.
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

  const handleInputChange = (elementId, value) => {
    setFormData(prev => ({ ...prev, [elementId]: value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError(null);
    setSubmitMessage('');

    if (!questionnaire || !questionnaire.elements) { // Check if questionnaire or elements are loaded
        setError("Le questionnaire n'est pas complètement chargé ou n'a pas de questions.");
        return;
    }

    const dataValuesPayload = {};
    let latitude = null;
    let longitude = null;

    questionnaire.elements.forEach(el => {
        const value = formData[el.id];
        if (value !== undefined && value !== null && value !== '') { // Only include answered questions
            if (el.field_type === 'coordinates_lat') {
                const parsedLat = parseFloat(value);
                if (!isNaN(parsedLat)) latitude = parsedLat;
            } else if (el.field_type === 'coordinates_lon') {
                const parsedLon = parseFloat(value);
                if (!isNaN(parsedLon)) longitude = parsedLon;
            } else {
                // Backend expects keys to be element labels for data_values
                dataValuesPayload[el.label] = value;
            }
        }
    });

    const submissionData = {
      data_values: dataValuesPayload,
      latitude: latitude,
      longitude: longitude,
      // submitter_name: "Un bénévole", // This could be a separate field in the form
    };

    const headers = {};
    // `questionnaire.password` ici est le vrai champ password du backend (hash ou null)
    // ou la valeur "protected" qu'on a mis si le GET initial a échoué par 401/403
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

  // Si une erreur de chargement s'est produite et qu'aucun questionnaire (même partiel) n'a été défini
  if (error && (!questionnaire || (questionnaire.title === "Questionnaire Protégé" && questionnaire.elements.length === 0) )) {
      // Afficher l'erreur et le formulaire de mot de passe si c'est une erreur de protection
      if (questionnaire && questionnaire.password === "protected") {
          // Continue to render form below, error is already set
      } else {
        return <div className="container mx-auto p-4 text-red-500 text-center">Erreur: {error}</div>;
      }
  }

  if (!questionnaire) return <div className="container mx-auto p-4 text-center">Questionnaire introuvable ou ID non fourni.</div>;


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
              required={(questionnaire.elements && questionnaire.elements.length > 0)} // Only truly required if there's a form to submit
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
            />
          </div>
        )}

        {questionnaire.elements && questionnaire.elements.map(element => (
          <div key={element.id}>
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
        ))}

        {/* Show submit button only if there are elements or if it's a protected questionnaire just to enter password */}
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
