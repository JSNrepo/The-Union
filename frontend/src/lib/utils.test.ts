import { describe, it, expect } from 'vitest';
import { cn } from './utils';

describe('cn utility', () => {
  it('merges multiple standard classes', () => {
    expect(cn('class1', 'class2')).toBe('class1 class2');
  });

  it('handles conditional classes', () => {
    expect(cn('class1', undefined, 'class2', null, false && 'class3', 'class4')).toBe('class1 class2 class4');
  });

  it('resolves Tailwind class conflicts correctly', () => {
    // px-2 and px-4 conflict, the last one should win
    expect(cn('px-2', 'px-4')).toBe('px-4');
    expect(cn('bg-red-500', 'bg-blue-500')).toBe('bg-blue-500');
  });

  it('handles arrays and objects correctly via clsx', () => {
    expect(cn(['class1', 'class2'], { class3: true, class4: false })).toBe('class1 class2 class3');
  });
});
