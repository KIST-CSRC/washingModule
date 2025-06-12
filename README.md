# Washing Module

This repository provides an integrated system for automating nanoparticle washing, including real-time object detection, recipe generation, and uncertainty reasoning.

You can download this repository using:

```bash
git clone https://github.com/KIST-CSRC/washingModule.git
```

Or set up the environment using the provided YAML file:

```bash
conda env create -f environment.yml
conda activate washing-env
```

---

## 📂 Folder Structure

```
yolact_vision/           # Real-time detection and angle estimation with YOLACT
LLMforwashing/           # Recipe generation with LLM and LangChain
DETECTRON/               # Latent Mask R-CNN model and uncertainty-based detection
DemoExampleImg/          # Example images for demo and documentation
```
****


# 🧪 YolactCentrifugeTask: Centrifuge-Based Detection & Angle Estimation

This project uses a customized version of **YOLACT** for real-time instance segmentation and object localization in a centrifuge setup. It extends the original model to include angle estimation relative to a reference color (blue or yellow), making it suitable for automation systems in chemical or nanoparticle labs.

---

## 📦 Main Features

* Real-time object detection with YOLACT
* HSV-based color localization (`blue`, `yellow`, etc.)
* Angular positioning of detected objects with respect to `rotor`
* Coordinates conversion for robot-arm pick-and-place
* Live camera demo

---

## 🔧 Setup

### Dependencies

```bash
pip install opencv-python numpy torch matplotlib chardet pycocotools
```

Ensure `detectron2`, `yolact`, and other submodules (like `yolact_Centri_origin`) are correctly cloned and importable.

---

## 📁 Project Structure (Required)

```
yolact_vision/
├── weights/
│   └── yolact_base_34_3000.pth
├── data/
│   ├── config_centri.py
│   ├── ...
├── YolactCentrifugeTask.py
└── capture/
```

---

## 🚀 Usage

### Run angle-based detection

```bash
python YolactCentrifugeTask.py
```

### Inside `__main__` (example)

```python
if __name__ == '__main__':
    detector = YolactCentrifugeTask()
    named_classes_locations, color_box = detector.color_location()
    detector.run_test_angle()  # Visualize holes and falcons with angle values
```

---

## 📸 Functional Highlights

### Color Detection

* HSV color-based filtering using `detect_color_hsv()`
* Contour extraction and bounding box drawing in `draw_top_contours()`

### Object-Angle Processing

* Compute relative angles from `rotor` center to color-marked references
* Sort `hole`, `falcon` objects based on angular positions
* Convert to robot coordinates with `convert_robot_coordinates()`

---

## 💡 Example Use Cases

* Automatic alignment of sample holders in a centrifuge rotor
* Real-time feedback for robotics integration
* Safety validation in chemical process automation

---

## 📚 Acknowledgements

This project builds on:

* [YOLACT](https://github.com/dbolya/yolact)
* Custom modifications by internal lab team
---

# 🧪 Latent R-CNN Object Detection with Uncertainty Visualization
This project demonstrates how to use **Detectron2** with a **Latent R-CNN** architecture to detect objects in chemical lab images and visualize uncertainty.
## 📌 Features
- Custom COCO-format dataset support
- Latent R-CNN with uncertainty estimation
- Filtering specific classes (`liquid`, `precipitate`)
- Visualizing predictions with bounding boxes and masks
--

## 📁 Project Structure
project/
├── detectron2/ # detectron2 codebase with latent modules
├── configs/
│ └── latent_mrcnn_coco.yaml # config file
├── output/
│ └── model_final.pth # trained model
├── script.py # main code (see below)
└── dataset/
├── train/
│ ├── train.json
│ └── *.jpg
└── val/
├── val.json
└── *.jpg

## 🧪 Demo & Script
You can run the full object detection and uncertainty visualization pipeline using:
 **[ImageEval] ImageEval.py**  
This script contains the complete workflow for loading the model, running inference, filtering classes (e.g., `liquid`, `precipitate`), and displaying the prediction with uncertainty.
### ▶️ Run the demo:
Based On This implementation builds upon the official Latent Mask R-CNN repository:
🔗 https://github.com/wyndwarrior/latent-maskrcnn
Please refer to the original repo for architecture details, training instructions, and baseline performance.

# Washing Recipe Generator with RAG and GPT-4o-mini

This project implements a **Recipe Generation Pipeline** for nanoparticle washing using a combination of:

* Assistant-based document retrieval via OpenAI Assistants API
* Contextual retrieval and reranking using LangChain
* Prompt-based reasoning for centrifuge recipe generation (RPM, time, solvents)

It supports:

* Prompt A: With RAG
* Prompt B: Without RAG
* Prompt C: Retry logic with failure history

---

## 🌱 Environment Variables

Environment variables needed:

```bash
OPENAI_API_KEY=your_key
VECTOR_STORE_ID=your_vector_store_id
```

---

## 📂 Folder Structure

```
LLM_Groundtruth/
  ├─ Paper/                  # PDF documents for RAG
Instructor/txt/MultiPrompt/
  ├─ WashingPrompt_RAG.txt         # Prompt A
  ├─ WashingPrompt_Non.txt         # Prompt B
  └─ WashingPrompt_failureloop.txt # Prompt C
results/YYYYMMDD/
  └─ recipe_QD_failed.json        # Output result example
```

---

## 🚀 How to Run

You can run the generator by providing reagent list, synthesis description, and optionally a previous failed recipe:

```python
retriever = WashingMethodRetrival()
generator = RecipeGenerator(retriever)

synthesized_reagents = [
    {"name": "cadmium oxide", "concentration_mol": 2.1, "concentration_unit": "mM"},
    {"name": "oleic acid", "concentration_mol": 25, "concentration_unit": "mM"},
    ...
]

previous_recipe = json.load(open("results/YYYYMMDD/recipe_QD_failed.json"))

recipe = generator.generate_recipe(
    synthesis_description="The material was synthesized using precursors:",
    synthesized_reagents=synthesized_reagents,
    previous_recipe=previous_recipe,
    fail_reason_text="Residual PL signal observed at 535 nm",
    use_rag=True
)
```

> 🧪 This example simply demonstrates how to trigger the **failed case retry logic** (Prompt C).

---

## 🧠 Prompt Logic

* **Prompt A (RAG)**: If document is found and `use_rag=True`
* **Prompt B (LLM-only)**: If no document is found or `use_rag=False`
* **Prompt C (Retry)**: If `previous_recipe` is provided, attempts improved recipe

Prompt variables:

* `synthesized_reagents`
* `reference_text` / `cited_text`
* `previous_failures_text`
* `fail_reason_text`

---

## 🗃️ Output Format

Returns a JSON like:

```json
{
  "process": {
    "Solvents": ["Ethanol", "Water"],
    "Solvents_Volume": [5, 5],
    "CentrifugationRPM": 8000,
    "CentrifugationTime": 120
  },
  "ReasonofAnswer": {"text": "Based on literature..."},
  "FailHistory": [...]
}
```

---

## 📌 Citation Retrieval via Assistant API

The Assistant uses the `file_search` tool to:

* Search vector store by reagent input
* Return cited document filename + quote

Fallback: If citation fails, prompts use only synthesis info.

---


## 🙋‍♂️ Contact

For help or questions, contact [Heeseung Lee](mailto:092508@kist.re.kr).
