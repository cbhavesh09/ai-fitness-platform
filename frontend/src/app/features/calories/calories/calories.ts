import { Component, inject, OnInit, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

import {
  CalorieLog,
  CalorieLogCreate,
  CalorieService,
  CalorieSummary,
} from '../../../core/services/calorie.service';

@Component({
  selector: 'app-calories',
  imports: [FormsModule],
  templateUrl: './calories.html',
  styleUrl: './calories.css',
})
export class Calories implements OnInit {
  private readonly calorieService = inject(CalorieService);

  readonly calorieLogs = signal<CalorieLog[]>([]);
  readonly summary = signal<CalorieSummary | null>(null);
  readonly isLoading = signal(true);
  readonly errorMessage = signal('');

  calories = 2000;
  date = new Date().toISOString().split('T')[0];

  isSaving = false;

  ngOnInit(): void {
    this.loadCalorieData();
  }

  loadCalorieData(): void {
    this.isLoading.set(true);
    this.errorMessage.set('');

    this.calorieService.getCalorieLogs().subscribe({
      next: (data) => {
        this.calorieLogs.set(data);
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
            'Unable to load calorie data.',
          );
        }
      },
    });
  }

  private loadSummary(): void {
    this.calorieService.getSummary().subscribe({
      next: (data) => {
        this.summary.set(data);
      },
      error: () => {
        this.errorMessage.set(
          'Unable to load calorie summary.',
        );
      },
    });
  }

  addCalories(): void {
    this.errorMessage.set('');

    if (this.calories <= 0) {
      this.errorMessage.set(
        'Calories must be greater than zero.',
      );
      return;
    }

    const calorieData: CalorieLogCreate = {
      calories: this.calories,
      date: this.date,
    };

    this.isSaving = true;

    this.calorieService.createCalorieLog(calorieData).subscribe({
      next: () => {
        this.isSaving = false;

        this.loadCalorieData();
      },
      error: () => {
        this.isSaving = false;
        this.errorMessage.set(
          'Unable to save calorie entry.',
        );
      },
    });
  }

  deleteCalories(calorieId: string): void {
    this.calorieService.deleteCalorieLog(calorieId).subscribe({
      next: () => {
        this.loadCalorieData();
      },
      error: () => {
        this.errorMessage.set(
          'Unable to delete calorie entry.',
        );
      },
    });
  }
}