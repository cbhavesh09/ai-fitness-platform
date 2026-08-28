import {
Component,
inject,
OnInit,
signal,
} from '@angular/core';

import {
DatePipe,
DecimalPipe,
} from '@angular/common';

import {
Prediction,
PredictionService,
WorkoutWeightPrediction,
} from '../../../core/services/prediction.service';

@Component({
selector: 'app-predictions',
imports: [DatePipe, DecimalPipe],
templateUrl: './predictions.html',
styleUrl: './predictions.css',
})
export class Predictions implements OnInit {
private readonly predictionService = inject(PredictionService);

readonly predictions = signal<Prediction[]>([]);
readonly latestPrediction = signal<Prediction | null>(null);

readonly exercises = signal<string[]>([]);
readonly selectedExercise = signal('');

readonly workoutRecommendation =
signal<WorkoutWeightPrediction | null>(null);

readonly isLoading = signal(true);
readonly isPredicting = signal(false);
readonly isWorkoutPredicting = signal(false);
readonly errorMessage = signal('');

ngOnInit(): void {
this.loadPredictions();
this.loadExercises();
}

loadExercises(): void {
this.predictionService.getWorkoutExercises().subscribe({
next: (response) => {
const exercises = response.exercises;


    this.exercises.set(exercises);

    if (exercises.length > 0) {
      this.selectedExercise.set(exercises[0]);
    }
  },

  error: (error) => {
    if (error.status === 401) {
      this.errorMessage.set(
        'Your session has expired. Please log in again.',
      );
    } else {
      this.errorMessage.set(
        'Unable to load available exercises.',
      );
    }
  },
});


}

loadPredictions(): void {
this.isLoading.set(true);
this.errorMessage.set('');


this.predictionService.getPredictions().subscribe({
  next: (data) => {
    this.predictions.set(data);

    this.latestPrediction.set(
      data.length > 0 ? data[0] : null,
    );

    this.isLoading.set(false);
  },

  error: (error) => {
    this.isLoading.set(false);

    if (error.status === 401) {
      this.errorMessage.set(
        'Your session has expired. Please log in again.',
      );
    } else {
      this.errorMessage.set(
        'Unable to load prediction history.',
      );
    }
  },
});


}

generatePrediction(): void {
this.errorMessage.set('');
this.isPredicting.set(true);


this.predictionService
  .createCalorieBurnPrediction()
  .subscribe({
    next: (prediction) => {
      this.latestPrediction.set(prediction);
      this.isPredicting.set(false);

      this.loadPredictions();
    },

    error: (error) => {
      this.isPredicting.set(false);

      if (error.status === 401) {
        this.errorMessage.set(
          'Your session has expired. Please log in again.',
        );
      } else if (error.status === 400) {
        this.errorMessage.set(
          'Not enough fitness data. Log a workout, weight, or calorie entry before generating a prediction.',
        );
      } else {
        this.errorMessage.set(
          'Unable to generate calorie-burn prediction.',
        );
      }
    },
  });


}

generateWorkoutRecommendation(): void {
const exercise = this.selectedExercise();


if (!exercise) {
  this.errorMessage.set(
    'Please select an exercise first.',
  );
  return;
}

this.errorMessage.set('');
this.isWorkoutPredicting.set(true);
this.workoutRecommendation.set(null);

this.predictionService
  .createWorkoutWeightPrediction(exercise)
  .subscribe({
    next: (result) => {
      this.workoutRecommendation.set(result);
      this.isWorkoutPredicting.set(false);
    },

    error: (error) => {
      this.isWorkoutPredicting.set(false);

      if (error.status === 401) {
        this.errorMessage.set(
          'Your session has expired. Please log in again.',
        );
      } else if (error.status === 404) {
        this.errorMessage.set(
          'No workout history was found for this exercise.',
        );
      } else {
        this.errorMessage.set(
          'Unable to generate workout recommendation.',
        );
      }
    },
  });


}

onExerciseChange(event: Event): void {
const select =
event.target as HTMLSelectElement;


this.selectedExercise.set(select.value);
this.workoutRecommendation.set(null);


}

deletePrediction(predictionId: string): void {
this.predictionService
.deletePrediction(predictionId)
.subscribe({
next: () => {
this.loadPredictions();
},


    error: () => {
      this.errorMessage.set(
        'Unable to delete prediction.',
      );
    },
  });


}
}
