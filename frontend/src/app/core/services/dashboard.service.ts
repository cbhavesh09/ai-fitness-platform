import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { API_CONFIG } from '../config/api.config';

export interface DashboardSummary {
  current_weight: number | null;
  latest_calories: number | null;
  total_workouts: number;
  today_workouts: number;
  latest_prediction: string | null;
  prediction_confidence: number | null;
  date: string;
}

@Injectable({
  providedIn: 'root',
})
export class DashboardService {
  private readonly http = inject(HttpClient);
  private readonly dashboardUrl = `${API_CONFIG.baseUrl}/dashboard`;

  getDashboard(): Observable<DashboardSummary> {
    return this.http.get<DashboardSummary>(this.dashboardUrl);
  }
}