import angledTrayUrl from "../assets/reference-images/angled-tray.svg";
import foldedStandUrl from "../assets/reference-images/folded-stand.svg";
import wallRackUrl from "../assets/reference-images/wall-rack.svg";

export interface ReferenceImageSample {
  imageId: string;
  title: string;
  description: string;
  alt: string;
  thumbnailUrl: string;
}

export const referenceImageSamples: readonly ReferenceImageSample[] = [
  {
    imageId: "angled-tray",
    title: "Angled drill index tray",
    description: "Folded tray with graduated bit openings and mounting flange.",
    alt: "Schematic of an angled sheet-metal drill index tray",
    thumbnailUrl: angledTrayUrl,
  },
  {
    imageId: "wall-rack",
    title: "Wall-mounted bit rack",
    description:
      "Compact vertical rack with labeled rows and rear mounting holes.",
    alt: "Schematic of a wall-mounted drill-bit rack",
    thumbnailUrl: wallRackUrl,
  },
  {
    imageId: "folded-stand",
    title: "Folded bench stand",
    description: "Free-standing folded plate concept with a wide stable base.",
    alt: "Schematic of a folded sheet-metal bench stand for drill bits",
    thumbnailUrl: foldedStandUrl,
  },
] as const;

export const referenceImageSampleIds = referenceImageSamples.map(
  ({ imageId }) => imageId,
);
