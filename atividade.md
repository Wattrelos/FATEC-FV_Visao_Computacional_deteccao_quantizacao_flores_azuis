# TASK SPEC: Blue Flower Segmentation & Quantification

## Parameters & Environment
```yaml
target_class: "blue_flower"
color_spaces: ["HSV", "LAB"]
validation_dataset:
  synthetic_samples: 3
  variations: ["scale", "shape", "hue_shift"]
metrics:
  absolute_pixels: int
  occupancy_ratio: float  # (flower_pixels / total_pixels) * 100
  percentage_error: float # (|detected - ground_truth| / ground_truth) * 100

  class FlowerSegmentationPipeline:
    def segment(image: np.ndarray) -> tuple[np.ndarray, int]:
        """
        Input: BGR image.
        Output: (binary_mask: uint8 [0, 255], flower_pixel_count: int)
        Rule: Color thresholding on Saturation/Hue to isolate blue petals from background.
        """
        ...

    def evaluate_synthetic(synthetic_img: np.ndarray, ground_truth_pixels: int) -> dict:
        """
        Calculates detected_pixels, error_pct, and occupancy_ratio.
        Constraint: Must apply the exact same segment() method used on real images.
        """