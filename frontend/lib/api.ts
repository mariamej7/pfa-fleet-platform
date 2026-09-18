// Adresse du backend FastAPI
const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";


// ============================================================
// DASHBOARD
// ============================================================

export type DashboardSummary = {
  date_generation: string | null;

  nombre_vehicules: number | null;
  nombre_total_mesures: number | null;
  distance_totale_km: number | null;

  nb_ravitaillements_potentiels: number | null;
  nb_alertes_regles: number | null;
  nb_candidats_ia: number | null;
  nb_regle_et_ia: number | null;

  nb_alertes_finales_uniques: number | null;
  nb_alertes_p1_critiques: number | null;

  nb_incoherences_fuel: number | null;
};


export async function getDashboardSummary(): Promise<DashboardSummary> {
  const response = await fetch(
    `${API_URL}/api/dashboard/summary`,
    {
      cache: "no-store",
    }
  );

  if (!response.ok) {
    throw new Error(
      "Impossible de récupérer les données du dashboard."
    );
  }

  return response.json();
}


// ============================================================
// UPLOAD
// ============================================================

export type UploadResult = {
  status: string;
  upload_id: string;
  original_filename: string;
  stored_filename: string;
  extension: string;
  size_bytes: number;
};


export async function uploadFleetFile(
  file: File
): Promise<UploadResult> {

  const formData = new FormData();

  formData.append(
    "file",
    file
  );

  const response = await fetch(
    `${API_URL}/api/imports/upload`,
    {
      method: "POST",
      body: formData,
    }
  );

  if (!response.ok) {

    const error = await response.json();

    throw new Error(
      error.detail ||
        "Erreur pendant l'importation."
    );
  }

  return response.json();
}


// ============================================================
// VALIDATION
// ============================================================

export type DatasetValidationResult = {
  upload_id: string;
  extension: string;

  nombre_lignes: number;
  nombre_colonnes: number;
  nombre_vehicules: number | null;

  debut_periode: string | null;
  fin_periode: string | null;

  colonnes_detectees: string[];

  colonnes_requises: string[];
  colonnes_requises_manquantes: string[];

  colonnes_contexte_presentes: string[];
  colonnes_contexte_manquantes: string[];

  valeurs_manquantes_pct: Record<string, number>;

  compatible: boolean;
  niveau_analyse: string;
  message: string;
};


export async function validateFleetDataset(
  uploadId: string
): Promise<DatasetValidationResult> {

  const response = await fetch(
    `${API_URL}/api/imports/${uploadId}/validate`,
    {
      method: "POST",
    }
  );

  if (!response.ok) {

    const error = await response.json();

    throw new Error(
      error.detail ||
        "Erreur pendant la validation du dataset."
    );
  }

  return response.json();
}


// ============================================================
// ANALYSE COMPLETE
// ============================================================

export type DatasetAnalysisResult = {

  status: string;
  upload_id: string;
  filename: string;

  preparation: {
    nombre_lignes_brutes: number;
    nombre_lignes_preparees: number;
    nombre_vehicules: number;
    nombre_fuel_hors_plage: number;
  };

  rules: {
    nombre_ravitaillements: number;
    nombre_baisses_suspectes: number;
  };

  context: {
    nombre_evenements_analyses: number;
    confiance_forte: number;
    confiance_moyenne: number;
    confiance_faible: number;
  };

  ai: {
    nombre_baisses_analysees: number;
    nombre_candidats_ia: number;
    nombre_regle_et_ia: number;
    taux_recouvrement_pct: number;
  };

  kpi: {
    nombre_vehicules: number;
    nombre_total_mesures: number;
    distance_totale_km: number;
  };

  platform: {
    nombre_vehicules: number;
    nombre_kpi_journaliers: number;
    nombre_ravitaillements: number;
    nombre_alertes_finales: number;
    nombre_evenements_carburant: number;

    nombre_alertes_p1: number;
    nombre_alertes_p2: number;
    nombre_alertes_p3: number;
    nombre_alertes_p4: number;
    nombre_alertes_p5: number;

    priorites: {
      P1: number;
      P2: number;
      P3: number;
      P4: number;
      P5: number;
    };
  };

  quality_controls: Record<string, number>;
};


export async function analyzeFleetDataset(
  uploadId: string
): Promise<DatasetAnalysisResult> {

  const response = await fetch(
    `${API_URL}/api/imports/${uploadId}/analyze`,
    {
      method: "POST",
    }
  );

  if (!response.ok) {

    const error = await response.json();

    throw new Error(
      error.detail ||
        "Erreur pendant l'analyse du dataset."
    );
  }

  return response.json();
}