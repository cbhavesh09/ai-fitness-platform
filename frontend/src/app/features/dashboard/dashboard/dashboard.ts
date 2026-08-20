import { Component, inject, OnInit, signal } from '@angular/core';

import {
  DashboardService,
  DashboardSummary,
} from '../../../core/services/dashboard.service';

@Component({
  selector: 'app-dashboard',
  imports: [],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.css',
})
export class Dashboard implements OnInit {
  private readonly dashboardService = inject(DashboardService);

  readonly dashboard = signal<DashboardSummary | null>(null);
  readonly isLoading = signal(true);
  readonly errorMessage = signal('');

  ngOnInit(): void {
    this.loadDashboard();
  }

  private loadDashboard(): void {
    this.isLoading.set(true);
    this.errorMessage.set('');

    this.dashboardService.getDashboard().subscribe({
      next: (data) => {
        console.log('DASHBOARD RESPONSE:', data);

        this.dashboard.set(data);
        this.isLoading.set(false);
      },
      error: (error) => {
        console.error('DASHBOARD ERROR:', error);

        this.isLoading.set(false);

        if (error.status === 401) {
          this.errorMessage.set(
            'Your session has expired. Please log in again.',
          );
        } else {
          this.errorMessage.set(
            'Unable to load dashboard data.',
          );
        }
      },
    });
  }
}