import { Component, inject, OnInit, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DatePipe } from '@angular/common';
import {
  Workout,
  WorkoutCreate,
  WorkoutRecommendation,
  WorkoutService,
  WorkoutSummary,
} from '../../../core/services/workout.service';

@Component({
  selector: 'app-workouts',
  imports: [FormsModule, DatePipe],
  templateUrl: './workouts.html',
  styleUrl: './workouts.css',
})
export class Workouts implements OnInit {
  private readonly workoutService = inject(WorkoutService);

  readonly workouts = signal<Workout[]>([]);
readonly selectedDate = signal<string | null>(null);

get workoutDates(): string[] {
  return [
    ...new Set(
      this.workouts().map((workout) => workout.date)
    ),
  ].sort((a, b) => b.localeCompare(a));
}

getWorkoutsForDate(date: string): Workout[] {
  return this.workouts().filter(
    (workout) => workout.date === date
  );
}

selectDate(date: string): void {
  this.selectedDate.set(date);
}
  readonly summary = signal<WorkoutSummary | null>(null);

  readonly recommendation =
    signal<WorkoutRecommendation | null>(null);

  readonly recommendationLoading = signal(false);
  readonly recommendationError = signal('');

  readonly isLoading = signal(true);
  readonly errorMessage = signal('');

  exercise = '';
  muscleGroup = '';
  sets = 3;
  reps = 10;
  weight = 0;
  duration = 30;
  date = new Date().toISOString().split('T')[0];

  isSaving = false;

  ngOnInit(): void {
    this.loadWorkouts();
  }

  loadWorkouts(): void {
    this.isLoading.set(true);
    this.errorMessage.set('');

    this.workoutService.getWorkouts().subscribe({
next: (data) => {
  this.workouts.set(data);

  if (data.length > 0) {
    this.selectedDate.set(data[0].date);
  } else {
    this.selectedDate.set(null);
  }

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
            'Unable to load workouts.',
          );
        }
      },
    });
  }

  private loadSummary(): void {
    this.workoutService.getSummary().subscribe({
      next: (data) => {
        this.summary.set(data);
      },
    });
  }

  loadRecommendation(): void {
    const exerciseName = this.exercise.trim();

    this.recommendation.set(null);
    this.recommendationError.set('');

    if (!exerciseName) {
      return;
    }

    this.recommendationLoading.set(true);

    this.workoutService
      .getRecommendation(exerciseName)
      .subscribe({
        next: (data) => {
          this.recommendation.set(data);
          this.recommendationLoading.set(false);
        },
        error: (error) => {
          this.recommendationLoading.set(false);

          if (error.status === 404) {
            this.recommendationError.set(
              'AI recommendation is not available for this exercise.',
            );
          } else if (error.status === 401) {
            this.recommendationError.set(
              'Your session has expired. Please log in again.',
            );
          } else {
            this.recommendationError.set(
              'Unable to generate an AI recommendation.',
            );
          }
        },
      });
  }

  addWorkout(): void {
    this.errorMessage.set('');

    if (!this.exercise.trim() || !this.muscleGroup.trim()) {
      this.errorMessage.set(
        'Exercise and muscle group are required.',
      );
      return;
    }

    const workout: WorkoutCreate = {
      exercise: this.exercise.trim(),
      muscle_group: this.muscleGroup.trim(),
      sets: this.sets,
      reps: this.reps,
      weight: this.weight,
      duration: this.duration,
      date: this.date,
    };

    this.isSaving = true;

    this.workoutService.createWorkout(workout).subscribe({
      next: () => {
        this.isSaving = false;

        this.exercise = '';
        this.muscleGroup = '';
        this.sets = 3;
        this.reps = 10;
        this.weight = 0;
        this.duration = 30;

        this.recommendation.set(null);
        this.recommendationError.set('');

        this.loadWorkouts();
      },
      error: () => {
        this.isSaving = false;
        this.errorMessage.set(
          'Unable to save workout.',
        );
      },
    });
  }

  deleteWorkout(workoutId: string): void {
    this.workoutService.deleteWorkout(workoutId).subscribe({
      next: () => {
        this.loadWorkouts();
      },
      error: () => {
        this.errorMessage.set(
          'Unable to delete workout.',
        );
      },
    });
  }
}