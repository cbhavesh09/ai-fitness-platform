import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { API_CONFIG } from '../config/api.config';

export interface Prediction {
  id: string;
  user_id: string;
  prediction_type: string;
  prediction: string;
  confidence: number;
  created_at: string;
}

export interface WorkoutWeightPrediction {
  exercise: string;
  recommended_weight: number | null;
  predicted_weight?: number;
  current_weight: number;
  previous_weight?: number | null;
  recent_best_weight?: number;
  recent_average_weight?: number;
  weight_trend?: number;
  historical_sessions: number;
  method: string;
  confidence: number;
  message: string;
  safety_adjustment?: string;
}

export interface WorkoutExercisesResponse {
  exercises: string[];
}

@Injectable({
  providedIn: 'root',
})
export class PredictionService {
  private readonly http = inject(HttpClient);
  private readonly predictionUrl =
    `${API_CONFIG.baseUrl}/predictions`;

  createCalorieBurnPrediction(): Observable<Prediction> {
    return this.http.post<Prediction>(
      `${this.predictionUrl}/calorie-burn`,
      {},
    );
  }

  createWorkoutWeightPrediction(
    exerciseName: string,
  ): Observable<WorkoutWeightPrediction> {
    return this.http.post<WorkoutWeightPrediction>(
      `${this.predictionUrl}/workout-weight`,
      {
        exercise_name: exerciseName,
      },
    );
  }

  getWorkoutExercises(): Observable<WorkoutExercisesResponse> {
    return this.http.get<WorkoutExercisesResponse>(
      `${this.predictionUrl}/workout-exercises`,
    );
  }

  getPredictions(): Observable<Prediction[]> {
    return this.http.get<Prediction[]>(
      this.predictionUrl,
    );
  }

  deletePrediction(
    predictionId: string,
  ): Observable<void> {
    return this.http.delete<void>(
      `${this.predictionUrl}/${predictionId}`,
    );
  }
}