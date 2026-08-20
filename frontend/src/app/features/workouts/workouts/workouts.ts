import { Component, inject, OnInit, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

import {
  Workout,
  WorkoutCreate,
  WorkoutService,
  WorkoutSummary,
} from '../../../core/services/workout.service';

@Component({
  selector: 'app-workouts',
  imports: [FormsModule],
  templateUrl: './workouts.html',
  styleUrl: './workouts.css',
})
export class Workouts implements OnInit {
  private readonly workoutService = inject(WorkoutService);

  readonly workouts = signal<Workout[]>([]);
  readonly summary = signal<WorkoutSummary | null>(null);
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