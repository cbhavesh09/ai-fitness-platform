
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { Router } from '@angular/router';
import { Component, inject, signal } from '@angular/core';

import {
  AuthService,
  RegisterRequest,
} from '../../../core/services/auth.service';

@Component({
  selector: 'app-signup',
imports: [FormsModule, RouterLink],
  templateUrl: './signup.html',
  styleUrl: './signup.css',
})
export class Signup {
  private readonly authService = inject(AuthService);
  private readonly router = inject(Router);

  name = '';
  email = '';
  password = '';

  age: number | null = null;
  gender = '';
  height_cm: number | null = null;
  weight_kg: number | null = null;

  activity_level = '';
  goal = '';

readonly isLoading = signal(false);
readonly errorMessage = signal('');

onSubmit(): void {
  this.errorMessage.set('');

  if (
    !this.name.trim() ||
    !this.email.trim() ||
    !this.password ||
    this.age === null ||
    !this.gender ||
    this.height_cm === null ||
    this.weight_kg === null ||
    !this.activity_level ||
    !this.goal
  ) {
    this.errorMessage.set(
      'Please complete all required fields.'
    );
    return;
  }

  if (this.password.length < 6) {
    this.errorMessage.set(
      'Password must be at least 6 characters.'
    );
    return;
  }

  if (this.age <= 0) {
    this.errorMessage.set(
      'Please enter a valid age.'
    );
    return;
  }

  if (this.height_cm <= 0) {
    this.errorMessage.set(
      'Please enter a valid height.'
    );
    return;
  }

  if (this.weight_kg <= 0) {
    this.errorMessage.set(
      'Please enter a valid weight.'
    );
    return;
  }

  const user: RegisterRequest = {
    name: this.name.trim(),
    email: this.email.trim(),
    password: this.password,
    age: this.age,
    gender: this.gender,
    height_cm: this.height_cm,
    weight_kg: this.weight_kg,
    activity_level: this.activity_level,
    goal: this.goal,
  };

  this.isLoading.set(true);

  this.authService.register(user).subscribe({
    next: () => {
      this.isLoading.set(false);

      this.router.navigate(['/login'], {
        queryParams: {
          registered: 'true',
        },
      });
    },

    error: (error) => {
      console.log('REGISTER ERROR:', error);

      this.isLoading.set(false);

      if (error.status === 409) {
        this.errorMessage.set(
          'An account with this email already exists.'
        );
      } else if (error.status === 400) {
        this.errorMessage.set(
          error.error?.detail ||
          'Please check your information.'
        );
      } else {
        this.errorMessage.set(
          'Unable to create your account. Please try again.'
        );
      }
    },
  });
}
}