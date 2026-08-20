import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { API_CONFIG } from '../config/api.config';

export interface CalorieLog {
  id: string;
  user_id: string;
  calories: number;
  date: string;
}

export interface CalorieLogCreate {
  calories: number;
  date: string;
}

export interface CalorieSummary {
  latest_calories: number | null;
  total_calories: number | null;
}

@Injectable({
  providedIn: 'root',
})
export class CalorieService {
  private readonly http = inject(HttpClient);
  private readonly calorieUrl = `${API_CONFIG.baseUrl}/calories`;

  getCalorieLogs(): Observable<CalorieLog[]> {
    return this.http.get<CalorieLog[]>(this.calorieUrl);
  }

  createCalorieLog(
    calorie: CalorieLogCreate,
  ): Observable<CalorieLog> {
    return this.http.post<CalorieLog>(
      this.calorieUrl,
      calorie,
    );
  }

  deleteCalorieLog(calorieId: string): Observable<void> {
    return this.http.delete<void>(
      `${this.calorieUrl}/${calorieId}`,
    );
  }

  getSummary(): Observable<CalorieSummary> {
    return this.http.get<CalorieSummary>(
      `${this.calorieUrl}/summary`,
    );
  }
}