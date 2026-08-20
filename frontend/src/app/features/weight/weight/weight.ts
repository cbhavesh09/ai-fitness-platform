import { Component, inject, OnInit, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

import {
  WeightLog,
  WeightLogCreate,
  WeightService,
  WeightSummary,
} from '../../../core/services/weight.service';

@Component({
  selector: 'app-weight',
  imports: [FormsModule],
  templateUrl: './weight.html',
  styleUrl: './weight.css',
})
export class Weight implements OnInit {
  private readonly weightService = inject(WeightService);

  readonly weightLogs = signal<WeightLog[]>([]);
  readonly summary = signal<WeightSummary | null>(null);
  readonly isLoading = signal(true);
  readonly errorMessage = signal('');

  weight = 70;
  date = new Date().toISOString().split('T')[0];

  isSaving = false;

  ngOnInit(): void {
    this.loadWeightData();
  }

  loadWeightData(): void {
    this.isLoading.set(true);
    this.errorMessage.set('');

    this.weightService.getWeightLogs().subscribe({
      next: (data) => {
        this.weightLogs.set(data);
        this.isLoading.set(false);
        this.loadSummary();
      },
      error: (error) => {
        this.isLoading.set(false);

        if (error.status === 401) {
          this.errorMessage.set(
            'Your session has expired. Please log in again.',
          );
        } else {
          this.errorMessage.set(
            'Unable to load weight data.',
          );
        }
      },
    });
  }

  private loadSummary(): void {
    this.weightService.getSummary().subscribe({
      next: (data) => {
        this.summary.set(data);
      },
      error: () => {
        this.errorMessage.set(
          'Unable to load weight summary.',
        );
      },
    });
  }

  addWeight(): void {
    this.errorMessage.set('');

    if (this.weight <= 0) {
      this.errorMessage.set(
        'Weight must be greater than zero.',
      );
      return;
    }

    const weightData: WeightLogCreate = {
      weight: this.weight,
      date: this.date,
    };

    this.isSaving = true;

    this.weightService.createWeightLog(weightData).subscribe({
      next: () => {
        this.isSaving = false;

        this.loadWeightData();
      },
      error: () => {
        this.isSaving = false;
        this.errorMessage.set(
          'Unable to save weight entry.',
        );
      },
    });
  }

  deleteWeight(weightId: string): void {
    this.weightService.deleteWeightLog(weightId).subscribe({
      next: () => {
        this.loadWeightData();
      },
      error: () => {
        this.errorMessage.set(
          'Unable to delete weight entry.',
        );
      },
    });
  }
}