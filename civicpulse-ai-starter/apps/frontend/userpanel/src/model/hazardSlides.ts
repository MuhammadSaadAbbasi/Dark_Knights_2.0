export type HazardCategory =
  | 'open_manhole'
  | 'exposed_electrical_wire'
  | 'pothole_road_damage';

export type HazardSlide = {
  category: HazardCategory;
  image: string;
  alt: string;
  title: string;
  supportingText: string;
  fact: string;
  sourceLabel?: string;
  sourceUrl?: string;
  cta: string;
};

export const hazardSlides: HazardSlide[] = [
  {
    category: 'open_manhole',
    image: 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRzZXg42lXRKHUmed0W9DRiREma1ZcaZartNaaisRpk7Q&s=10',
    alt: 'Hazardous electrical infrastructure beside a wet urban street',
    title: 'An Open Manhole Can Change a Family Forever.',
    supportingText: 'Uncovered drains put children, pedestrians, and commuters at risk.',
    fact: '27 people died in Karachi in 2025 after falling into open manholes and drains, according to data attributed to the Edhi Foundation.',
    sourceLabel: 'Dawn, December 2025',
    sourceUrl: 'https://www.dawn.com/news/1963941',
    cta: 'Report an Open Manhole →',
  },
  {
    category: 'exposed_electrical_wire',
    image: 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRcQc-z0jAlFXlauM73Tec0tKqTOOS59dZkK8v2JtA9TPBxSsA11Xkwu0_J&s=10',
    alt: 'Damaged road surface with a deep pothole in an urban environment',
    title: 'A Fallen Wire Can Turn a Street Deadly.',
    supportingText: 'Exposed electrical infrastructure becomes especially dangerous during rain and flooding.',
    fact: 'In August 2025, two brothers died from electrocution during rain in Karachi’s Shah Faisal Colony, according to reporting by The Express Tribune.',
    sourceLabel: 'The Express Tribune, August 2025',
    sourceUrl: 'https://tribune.com.pk/story/2562482/ke-officials-booked-after-two-brothers-die-of-electrocution',
    cta: 'Report an Electrical Hazard →',
  },
  {
    category: 'pothole_road_damage',
    image: 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQPfj1O7cC6n0j_gQoNbZzsopB-9z1BrQpzYZ-4hhrDwQ&s=10',
    alt: 'Uncovered manhole on an urban street',
    title: 'Every Damaged Road Deserves Attention.',
    supportingText: 'Potholes can endanger motorcyclists, cyclists, pedestrians, and drivers.',
    fact: 'A road hazard reported today is an opportunity to prevent tomorrow’s accident.',
    cta: 'Report a Pothole →',
  },
];
