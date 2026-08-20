import { Routes } from '@angular/router';
import { Workouts } from './features/workouts/workouts/workouts';
import { Login } from './features/auth/login/login';
import { Dashboard } from './features/dashboard/dashboard/dashboard';
import { authGuard } from './core/guards/auth-guard';
import { Weight } from './features/weight/weight/weight';
import { Calories } from './features/calories/calories/calories';

export const routes: Routes = [
  {
    path: 'login',
    component: Login,
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
];