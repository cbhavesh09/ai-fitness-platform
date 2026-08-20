import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { API_CONFIG } from '../config/api.config';

export interface Workout {
  id: string;
  user_id: string;
  exercise: string;
  muscle_group: string;
  sets: number;
  reps: number;
  weight: number;
  duration: number;
  date: string;
}

export interface WorkoutCreate {
  exercise: string;
  muscle_group: string;
  sets: number;
  reps: number;
  weight: number;
  duration: number;
  date: string;
}

export interface WorkoutSummary {
  total_workouts: number;
  today_workouts: number;
}

@Injectable({
  providedIn: 'root',
})
export class WorkoutService {
  private readonly http = inject(HttpClient);
  private readonly workoutsUrl = `${API_CONFIG.baseUrl}/workouts`;

  getWorkouts(): Observable<Workout[]> {
    return this.http.get<Workout[]>(this.workoutsUrl);
  }

  createWorkout(workout: WorkoutCreate): Observable<Workout> {
    return this.http.post<Workout>(this.workoutsUrl, workout);
  }

  deleteWorkout(workoutId: string): Observable<void> {
    return this.http.delete<void>(
      `${this.workoutsUrl}/${workoutId}`,
    );
  }

  getSummary(): Observable<WorkoutSummary> {
    return this.http.get<WorkoutSummary>(
      `${this.workoutsUrl}/summary`,
    );
  }
}