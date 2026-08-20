import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Weight } from './weight';

describe('Weight', () => {
  let component: Weight;
  let fixture: ComponentFixture<Weight>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Weight],
    }).compileComponents();

    fixture = TestBed.createComponent(Weight);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
