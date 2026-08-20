import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { API_CONFIG } from '../config/api.config';

export interface WeightLog {
  id: string;
  user_id: string;
  weight: number;
  date: string;
}

export interface WeightLogCreate {
  weight: number;
  date: string;
}

export interface WeightSummary {
  current_weight: number | null;
  starting_weight: number | null;
  weight_change: number | null;
}

@Injectable({
  providedIn: 'root',
})
export class WeightService {
  private readonly http = inject(HttpClient);
  private readonly weightUrl = `${API_CONFIG.baseUrl}/weight`;

  getWeightLogs(): Observable<WeightLog[]> {
    return this.http.get<WeightLog[]>(this.weightUrl);
  }

  createWeightLog(weight: WeightLogCreate): Observable<WeightLog> {
    return this.http.post<WeightLog>(
      this.weightUrl,
      weight,
    );
  }

  deleteWeightLog(weightId: string): Observable<void> {
    return this.http.delete<void>(
      `${this.weightUrl}/${weightId}`,
    );
  }

  getSummary(): Observable<WeightSummary> {
    return this.http.get<WeightSummary>(
      `${this.weightUrl}/summary`,
    );
  }
}