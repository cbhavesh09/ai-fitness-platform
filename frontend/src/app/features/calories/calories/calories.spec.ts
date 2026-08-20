import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Calories } from './calories';

describe('Calories', () => {
  let component: Calories;
  let fixture: ComponentFixture<Calories>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Calories],
    }).compileComponents();

    fixture = TestBed.createComponent(Calories);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
