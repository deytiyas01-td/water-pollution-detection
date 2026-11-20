import os
import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Check if running in a Gradio-specific environment
try:
    import gradio as gr
    from backend.detector import WaterPollutionDetector
    from backend.config import TARGET_CLASSES, CATEGORY_GROUPS, DEFAULT_BOX_THRESHOLD
    from PIL import Image

    HAS_GRADIO = True
except ImportError:
    HAS_GRADIO = False

import uvicorn
from backend.main import app as fastapi_app
from backend.config import HOST, PORT

if HAS_GRADIO:
    # Wrap FastAPI with Gradio so it runs seamlessly on Hugging Face Gradio Spaces (100% Free)
    detector = None

    def get_detector():
        global detector
        if detector is None:
            detector = WaterPollutionDetector.get_instance()
        return detector

    def detect_image_gradio(image, threshold, selected_classes):
        if image is None:
            return None, "Please upload an image."
        det = get_detector()
        pil_img = Image.fromarray(image)
        prompt, _ = det.format_prompt(selected_classes)
        detections = det.detect_on_pil_image(
            image=pil_img,
            prompt=prompt,
            threshold=threshold,
            text_threshold=threshold,
        )
        annotated = det.draw_detections(pil_img, detections)
        
        counts = {}
        for d in detections:
            lbl = d["label"]
            counts[lbl] = counts.get(lbl, 0) + 1
            
        summary = f"Total Detections: {len(detections)}\n"
        for k, v in counts.items():
            summary += f"- {k.title()}: {v}\n"
        if not detections:
            summary = "No pollution objects detected above the threshold."
            
        return annotated, summary

    def detect_video_gradio(video_path, threshold, speed_mode, selected_classes):
        if not video_path:
            return None, "Please upload a video."
        det = get_detector()
        result = det.process_video(
            video_path=Path(video_path),
            selected_classes=selected_classes,
            threshold=threshold,
            text_threshold=threshold,
            speed_mode=speed_mode.lower(),
        )
        out_video = Path(result["annotated_url"].lstrip("/"))
        
        timeline_text = f"Sampled {result['sampled_frames']} keyframes in {result['processing_time_sec']}s\n"
        timeline_text += f"Total Detections: {result['total_detections']}\n\n"
        for ev in result.get("timeline", []):
            labels_str = ", ".join([f"{k} ({v})" for k, v in ev["labels"].items()])
            timeline_text += f"[{ev['time_formatted']}] {labels_str}\n"
            
        return str(out_video) if out_video.exists() else None, timeline_text

    # Build Gradio UI with clean professional styling
    with gr.Blocks(title="AquaGuard | Water Surface Pollution Detection", theme=gr.themes.Soft()) as demo:
        gr.Markdown(
            """
            # 🌊 AquaGuard: Water Surface Pollution Detection
            ### Automated AI Detection for Floating Plastics, Oil Spills, Organic Weeds & Marine Debris
            *Powered by Grounding DINO Zero-Shot Object Detection*
            """
        )

        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### ⚙️ Detection Settings")
                threshold_slider = gr.Slider(
                    minimum=0.10, maximum=0.80, value=0.25, step=0.05, label="Confidence Threshold"
                )
                classes_select = gr.CheckboxGroup(
                    choices=TARGET_CLASSES,
                    value=TARGET_CLASSES,
                    label="Target Pollutants to Detect",
                )

            with gr.Column(scale=2):
                with gr.Tabs():
                    with gr.TabItem("🖼️ Image Detection (PNG, JPG)"):
                        image_input = gr.Image(type="numpy", label="Upload Water Surface Image")
                        image_button = gr.Button("Analyze Image", variant="primary")
                        image_output = gr.Image(label="Annotated Detections")
                        image_summary = gr.Textbox(label="Detected Contaminants Summary", lines=4)

                        image_button.click(
                            fn=detect_image_gradio,
                            inputs=[image_input, threshold_slider, classes_select],
                            outputs=[image_output, image_summary],
                        )

                    with gr.TabItem("🎥 Video Footage (MP4, MKV)"):
                        video_speed = gr.Radio(
                            choices=["Turbo", "Balanced", "Detailed"],
                            value="Turbo",
                            label="⚡ Video Processing Speed Preset",
                            info="Turbo processes keyframes in ~15-25 seconds",
                        )
                        video_input = gr.Video(label="Upload Surveillance or Drone Video")
                        video_button = gr.Button("Analyze Video", variant="primary")
                        video_output = gr.Video(label="Annotated Video Output")
                        video_timeline = gr.Textbox(label="Pollution Timeline Events", lines=6)

                        video_button.click(
                            fn=detect_video_gradio,
                            inputs=[video_input, threshold_slider, video_speed, classes_select],
                            outputs=[video_output, video_timeline],
                        )

        gr.Markdown("---")
        gr.Markdown("💡 *You can also access the full custom web portal served directly by FastAPI.*")

    # Mount our FastAPI app into Gradio so BOTH are available!
    hf_app = gr.mount_gradio_app(fastapi_app, demo, path="/gradio")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 7860))
    host = os.getenv("HOST", "0.0.0.0")
    debug = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")

    print("=" * 60)
    print("Starting AquaGuard Water Pollution Detection Server")
    print(f"Server URL: http://{host}:{port}")
    if HAS_GRADIO:
        print(f"Gradio UI: http://{host}:{port}/gradio")
    print("=" * 60)

    target_app = "app:hf_app" if HAS_GRADIO else "backend.main:app"
    uvicorn.run(target_app, host=host, port=port, reload=debug)
