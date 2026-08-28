import { Routes } from '@angular/router';
import { Workouts } from './features/workouts/workouts/workouts';
import { Login } from './features/auth/login/login';
import { Dashboard } from './features/dashboard/dashboard/dashboard';
import { authGuard } from './core/guards/auth-guard';
import { Weight } from './features/weight/weight/weight';
import { Calories } from './features/calories/calories/calories';
import { Predictions } from './features/predictions/predictions/predictions';
import { guestGuard } from './core/guards/guest-guard';
import { Signup } from './features/auth/signup/signup';

export const routes: Routes = [
  {
  path: 'login',
  component: Login,
  canActivate: [guestGuard],
},
{
  path: 'signup',
  component: Signup,
  canActivate: [guestGuard],
},
  {
    path: 'dashboard',
    component: Dashboard,
    canActivate: [authGuard],
  },

  {
    path: '',
    redirectTo: 'login',
    pathMatch: 'full',
  },
{
  path: 'workouts',
  component: Workouts,
  canActivate: [authGuard],
},
{
  path: 'weight',
  component: Weight,
  canActivate: [authGuard],
},
{
  path: 'calories',
  component: Calories,
  canActivate: [authGuard],
},
{
  path: 'predictions',
  component: Predictions,
  canActivate: [authGuard],
},
];