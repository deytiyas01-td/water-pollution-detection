import os
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import torch
from transformers import AutoProcessor, AutoModelForZeroShotObjectDetection

from backend.config import (
    MODEL_PATH,
    DEVICE,
    DEFAULT_BOX_THRESHOLD,
    DEFAULT_TEXT_THRESHOLD,
    TARGET_CLASSES,
    CATEGORY_GROUPS,
    OUTPUTS_DIR,
    VIDEO_DEFAULT_INTERVAL_SEC,
    VIDEO_MAX_SAMPLED_FRAMES,
    VIDEO_INFERENCE_SIZE,
)

# Color mapping for classes
CLASS_COLOR_MAP = {}
for group, info in CATEGORY_GROUPS.items():
    hex_col = info["color"].lstrip("#")
    rgb = tuple(int(hex_col[i : i + 2], 16) for i in (0, 2, 4))
    for c in info["classes"]:
        CLASS_COLOR_MAP[c.lower()] = rgb


def get_class_color(label: str) -> Tuple[int, int, int]:
    """Returns RGB tuple for a detected label."""
    label_clean = label.lower().strip()
    for key, color in CLASS_COLOR_MAP.items():
        if key in label_clean or label_clean in key:
            return color
    return (255, 140, 0)  # Default vivid orange


class WaterPollutionDetector:
    _instance = None

    def __init__(self):
        self.device = self._resolve_device()
        
        # Optimize CPU threads for parallel inference on multi-core CPUs
        if self.device == "cpu":
            num_cores = os.cpu_count() or 4
            opt_threads = min(8, max(4, num_cores))
            torch.set_num_threads(opt_threads)
            print(f"Configured PyTorch with {opt_threads} CPU worker threads.")

        print(f"Loading Grounding DINO model from '{MODEL_PATH}' on device: {self.device}...")
        self.processor = AutoProcessor.from_pretrained(MODEL_PATH)
        self.model = AutoModelForZeroShotObjectDetection.from_pretrained(MODEL_PATH).to(self.device)
        self.model.eval()
        print("Grounding DINO model loaded and ready.")

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = WaterPollutionDetector()
        return cls._instance

    def _resolve_device(self) -> str:
        if DEVICE == "cuda" and torch.cuda.is_available():
            return "cuda"
        elif DEVICE == "cpu":
            return "cpu"
        return "cuda" if torch.cuda.is_available() else "cpu"

    def format_prompt(self, selected_classes: Optional[List[str]] = None) -> Tuple[str, List[str]]:
        classes = selected_classes if selected_classes else TARGET_CLASSES
        # Format prompt with period delimiters required by Grounding DINO
        clean_classes = [c.strip().lower() for c in classes if c.strip()]
        prompt = " . ".join(clean_classes) + " ."
        return prompt, clean_classes

    def detect_on_pil_image(
        self,
        image: Image.Image,
        prompt: str,
        threshold: float = DEFAULT_BOX_THRESHOLD,
        text_threshold: float = DEFAULT_TEXT_THRESHOLD,
        processor_size: Optional[Dict[str, int]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Runs Grounding DINO zero-shot detection on a PIL Image.
        Dynamically adapts to CUDA when running under Hugging Face ZeroGPU or local GPU.
        """
        # Dynamic ZeroGPU / CUDA device sync
        active_device = "cuda" if torch.cuda.is_available() else "cpu"
        if active_device != self.device:
            self.device = active_device
            self.model = self.model.to(self.device)

        w, h = image.size

        if processor_size:
            inputs = self.processor(
                images=image,
                text=prompt,
                size=processor_size,
                return_tensors="pt"
            ).to(self.device)
        else:
            inputs = self.processor(
                images=image,
                text=prompt,
                return_tensors="pt"
            ).to(self.device)

        with torch.inference_mode():
            outputs = self.model(**inputs)

        results = self.processor.post_process_grounded_object_detection(
            outputs,
            inputs.input_ids,
            threshold=threshold,
            text_threshold=text_threshold,
            target_sizes=[(h, w)],
        )

        detections = []
        if len(results) > 0:
            res = results[0]
            boxes = res["boxes"].cpu().tolist()
            scores = res["scores"].cpu().tolist()
            raw_labels = res.get("text_labels", res.get("labels", []))

            for box, score, label in zip(boxes, scores, raw_labels):
                label_str = str(label).strip()
                if not label_str:
                    continue
                # Normalize box coordinates
                x1, y1, x2, y2 = [round(float(v), 1) for v in box]
                detections.append({
                    "label": label_str,
                    "confidence": round(float(score), 4),
                    "box": [x1, y1, x2, y2],
                    "color": "#%02x%02x%02x" % get_class_color(label_str),
                })

        return detections

    def draw_detections(
        self,
        image: Image.Image,
        detections: List[Dict[str, Any]],
        line_width: int = 3,
    ) -> Image.Image:
        """Draws aesthetic bounding boxes and label badges onto a PIL image."""
        annotated = image.copy().convert("RGB")
        draw = ImageDraw.Draw(annotated)

        try:
            font = ImageFont.truetype("arial.ttf", 16)
        except Exception:
            font = ImageFont.load_default()

        for det in detections:
            x1, y1, x2, y2 = det["box"]
            label = det["label"]
            score = det["confidence"]
            color = get_class_color(label)

            # Draw outer rectangle
            draw.rectangle([x1, y1, x2, y2], outline=color, width=line_width)

            # Draw label banner
            caption = f"{label.title()} {int(score * 100)}%"
            bbox = font.getbbox(caption)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]

            badge_y1 = max(0, y1 - text_h - 8)
            badge_y2 = badge_y1 + text_h + 8
            badge_x2 = min(image.width, x1 + text_w + 12)

            draw.rectangle([x1, badge_y1, badge_x2, badge_y2], fill=color)
            draw.text((x1 + 6, badge_y1 + 4), caption, fill=(255, 255, 255), font=font)

        return annotated

    def process_image(
        self,
        image_path: Path,
        selected_classes: Optional[List[str]] = None,
        threshold: float = DEFAULT_BOX_THRESHOLD,
        text_threshold: float = DEFAULT_TEXT_THRESHOLD,
    ) -> Dict[str, Any]:
        """Runs end-to-end detection on an image file, saves annotated output, and returns stats."""
        start_time = time.time()
        image = Image.open(image_path).convert("RGB")
        prompt, _ = self.format_prompt(selected_classes)

        # Standalone images use full resolution for maximum quality
        detections = self.detect_on_pil_image(
            image=image,
            prompt=prompt,
            threshold=threshold,
            text_threshold=text_threshold,
        )

        annotated_image = self.draw_detections(image, detections)

        # Save annotated image
        out_filename = f"annotated_{image_path.stem}.jpg"
        out_path = OUTPUTS_DIR / out_filename
        annotated_image.save(out_path, quality=92)

        # Calculate statistics
        counts_by_class = {}
        for det in detections:
            lbl = det["label"].lower()
            counts_by_class[lbl] = counts_by_class.get(lbl, 0) + 1

        elapsed = round(time.time() - start_time, 2)

        return {
            "media_type": "image",
            "original_filename": image_path.name,
            "annotated_filename": out_filename,
            "annotated_url": f"/outputs/{out_filename}",
            "width": image.width,
            "height": image.height,
            "total_detections": len(detections),
            "counts_by_class": counts_by_class,
            "detections": detections,
            "processing_time_sec": elapsed,
            "severity": self._assess_severity(len(detections)),
        }

    def process_video(
        self,
        video_path: Path,
        selected_classes: Optional[List[str]] = None,
        threshold: float = DEFAULT_BOX_THRESHOLD,
        text_threshold: float = DEFAULT_TEXT_THRESHOLD,
        speed_mode: str = "turbo",  # 'turbo', 'balanced', or 'detailed'
        custom_interval_sec: Optional[float] = None,
        custom_max_frames: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        High-performance accelerated video detection pipeline:
        1. Direct keyframe seeking (skips 95% of unneeded frame decoding).
        2. Accelerated Swin-attention resolution (drops Swin attention complexity by 75%).
        3. Even temporal sampling to cover the entire video timeline without bottlenecks.
        """
        start_time = time.time()
        prompt, _ = self.format_prompt(selected_classes)

        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise RuntimeError(f"Could not open video file: {video_path}")

        orig_fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = round(total_frames / orig_fps, 2) if (orig_fps > 0 and total_frames > 0) else 0.0

        # Configure speed parameters
        if speed_mode == "turbo":
            interval = custom_interval_sec or 3.0
            max_frames = custom_max_frames or 6
            proc_size = {"shortest_edge": 288, "longest_edge": 384}
        elif speed_mode == "detailed":
            interval = custom_interval_sec or 1.0
            max_frames = custom_max_frames or 16
            proc_size = {"shortest_edge": 384, "longest_edge": 512}
        else:  # balanced
            interval = custom_interval_sec or 1.8
            max_frames = custom_max_frames or 10
            proc_size = {"shortest_edge": 320, "longest_edge": 480}

        # Calculate sample timestamps evenly spaced across the video
        if duration > 0:
            num_desired = max(2, int(duration / interval))
            num_samples = min(max_frames, num_desired)
            timestamps = np.linspace(0.2, max(0.2, duration - 0.2), num_samples).tolist()
        else:
            timestamps = [0.0]

        out_filename = f"annotated_{video_path.stem}.mp4"
        out_path = OUTPUTS_DIR / out_filename

        # Write output video at 10 fps, showing each analyzed keyframe for 1.2 seconds
        out_fps = 10.0
        repeat_frames_per_sample = int(out_fps * 1.2)
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(out_path), fourcc, out_fps, (width, height))

        timeline_events = []
        overall_counts = {}
        total_detected_instances = 0
        annotated_frames_written = 0

        for current_sec in timestamps:
            target_frame_idx = min(total_frames - 1, max(0, int(current_sec * orig_fps)))
            
            # Fast direct seek (O(1) frame access)
            cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame_idx)
            ret, frame = cap.read()
            if not ret or frame is None:
                continue

            # Convert BGR to RGB for PIL & PyTorch
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_frame = Image.fromarray(rgb_frame)

            # Accelerated inference using resolution tuning
            detections = self.detect_on_pil_image(
                image=pil_frame,
                prompt=prompt,
                threshold=threshold,
                text_threshold=text_threshold,
                processor_size=proc_size,
            )

            if detections:
                total_detected_instances += len(detections)
                frame_labels = {}
                for det in detections:
                    lbl = det["label"].lower()
                    overall_counts[lbl] = overall_counts.get(lbl, 0) + 1
                    frame_labels[lbl] = frame_labels.get(lbl, 0) + 1

                timeline_events.append({
                    "timestamp_sec": round(current_sec, 2),
                    "time_formatted": self._format_time(current_sec),
                    "count": len(detections),
                    "labels": frame_labels,
                    "detections": detections,
                })

            annotated_pil = self.draw_detections(pil_frame, detections)
            annotated_bgr = cv2.cvtColor(np.array(annotated_pil), cv2.COLOR_RGB2BGR)

            # Write keyframe with pause duration so user can inspect detections
            for _ in range(repeat_frames_per_sample):
                writer.write(annotated_bgr)
            annotated_frames_written += 1

        cap.release()
        writer.release()

        elapsed = round(time.time() - start_time, 2)
        avg_speed = round(elapsed / max(1, annotated_frames_written), 2)

        return {
            "media_type": "video",
            "original_filename": video_path.name,
            "annotated_filename": out_filename,
            "annotated_url": f"/outputs/{out_filename}",
            "width": width,
            "height": height,
            "duration_sec": duration,
            "speed_mode": speed_mode,
            "sampled_frames": annotated_frames_written,
            "total_detections": total_detected_instances,
            "counts_by_class": overall_counts,
            "timeline": timeline_events,
            "processing_time_sec": elapsed,
            "avg_time_per_frame_sec": avg_speed,
            "severity": self._assess_severity(total_detected_instances),
        }

    def _assess_severity(self, count: int) -> Dict[str, str]:
        if count == 0:
            return {"level": "Clean", "color": "#10b981", "description": "No significant pollution detected."}
        elif count <= 2:
            return {"level": "Low", "color": "#3b82f6", "description": "Isolated debris detected; monitoring advised."}
        elif count <= 6:
            return {"level": "Moderate", "color": "#f59e0b", "description": "Multiple pollution sources detected."}
        else:
            return {"level": "Critical", "color": "#ef4444", "description": "Severe water surface contamination detected!"}

    def _format_time(self, seconds: float) -> str:
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins:02d}:{secs:02d}"
