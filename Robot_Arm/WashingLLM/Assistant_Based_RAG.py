import json
import logging
from pathlib import Path
import os
import re
from typing import List, Dict, Any, Union, Optional, Tuple, Set
from openai import OpenAI

from dotenv import load_dotenv
from chromadb import PersistentClient
from langchain.schema import Document
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma as ChromaVectorStore
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain.prompts import PromptTemplate
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_community.document_compressors.rankllm_rerank import RankLLMRerank
from langchain.retrievers.document_compressors import LLMChainExtractor
from langchain.retrievers import ContextualCompressionRetriever

from langchain.prompts import (
    SystemMessagePromptTemplate,
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.chains import LLMChain

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

PDF_FOLDER = Path("./InputYourPaperPath")
PROMPT_RAG = Path("./Instructor/txt/MultiPrompt/WashingPrompt_RAG.txt")
PROMPT_NON = Path("./Instructor/txt/MultiPrompt/WashingPrompt_Non.txt")
PROMPT_FAILURE = Path("./Instructor/txt/MultiPrompt/WashingPrompt_failureloop.txt")
DEFAULT_WASHING_QUERY = "how to washing the nanoparticle using by centrifugation?"


class WashingMethodRetrival:
    def __init__(self):
        
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
        self.llm = ChatOpenAI(temperature=0, model="gpt-4o-mini")
        self.compressor = LLMChainExtractor.from_llm(self.llm)
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.vector_store_id = os.getenv("VECTOR_STORE_ID")


    def retrieve_reference_via_assistant(
        self,
        synthesized_reagents: List[Dict[str, Any]],
        model: str = "gpt-4o-mini",
        max_num_results: int = 5
    ) -> Tuple[str, str, str]:
        """
        Use the Assistant API to return the most relevant document filename, the cited text, and the query.
        """
        
        if isinstance(synthesized_reagents, list):
            reagent_names = ", ".join([r["name"] for r in synthesized_reagents])
        elif isinstance(synthesized_reagents, str):
            reagent_names = synthesized_reagents
        else:
            raise ValueError("synthesized_reagents must be either a string or a list.")

        query = f"The material was synthesized using precursors: {reagent_names}"
        logging.info(f"[Assistant-based literature search query]: {query}")
        response = self.client.responses.create(
            input=query,
            model=model,
            tools=[{
                "type": "file_search",
                "vector_store_ids": [self.vector_store_id],
            }]
        )

        annotations = response.output[1].content[0].annotations
        cited_file_paths = []
        cited_text = None
        for ann in annotations:
            if ann.type == "file_citation":
                file_info = self.client.files.retrieve(ann.file_id)
                filename = file_info.filename
                cited_file_paths.append(file_info.filename)
                cited_text = getattr(ann, "quote", "No quoted text available").strip()
                return filename, cited_file_paths, cited_text

        logging.warning("❗ No citations found in Assistant response. Returning default answer.")
        
        return "No relevant document found", "No cited text available"
    
    def retrieve_washing_method(self, file_path: str, query_text: str = DEFAULT_WASHING_QUERY) -> Optional[str]:
        """ Search for a specific washing method in the PDF file."""
        file_name = Path(file_path).name
        full_path = (PDF_FOLDER / file_name).resolve(strict=False)
        if not full_path.exists():
            logging.error(f" File does not exist:{full_path}")
            return None

        logging.info(f"Searching for washing method:{full_path}")
        pdf_loader = PyMuPDFLoader(str(full_path))
        documents = pdf_loader.load()
        combined_text = " ".join([doc.page_content for doc in documents])
        if not combined_text:
            logging.error("Could not find the content in the PDF document.")
            return None

        document_to_search = [Document(page_content=combined_text, metadata={"file_path": str(full_path)})]
        filtered_retriever = ContextualCompressionRetriever(
            base_compressor=self.compressor,
            base_retriever=ChromaVectorStore.from_documents(document_to_search, self.embeddings).as_retriever()
        )
        results = filtered_retriever.invoke(query_text)
        if not results:
            logging.error("No results found for the washing method search.")
            return None

        washing_text = results[0].page_content.strip().replace("\n", " ").strip()
        logging.info(f"Washing method extraction completed:{washing_text[:120]}...")
        return washing_text    


class RecipeGenerator:
    def __init__(self, retriever: WashingMethodRetrival, llm_model: str = "gpt-4o-mini"):
        """
        LLM을 이용해 레시피를 생성하는 클래스입니다.
        """
        self.retriever = retriever
        self.llm = ChatOpenAI(temperature=0, model=llm_model)

    @staticmethod
    def clean_json_string(json_string: str) -> str: 
        """Remove unnecessary control characters and JSON error elements from the LLM response."""
        json_string = json_string.replace("```json", "").replace("```", "").strip()
        json_string = json_string.replace("\\", "/")
        json_string = re.sub(r"//.*", "", json_string)
        json_string = re.sub(r"\\x[0-9A-Fa-f]{2}", "", json_string)
        json_string = re.sub(r"[\x00-\x1F\x7F]", "", json_string)
        json_string = re.sub(r"(?<!\\)\'", '"', json_string)
        if not json_string.endswith("}"):
            json_string += '"}'
        return json_string

    @staticmethod
    def clean_text(text: str) -> str:
        """Clean up the text by removing unnecessary control characters and comments."""
        text = text.replace("```json", "").replace("```", "").strip()
        text = re.sub(r"[^\x20-\x7E]", "", text)
        text = re.sub(r"//.*", "", text)
        return text
    def generate_recipe(
        self,
        synthesis_description: str,
        synthesized_reagents: List[Dict[str, Any]],
        previous_recipe: Optional[Dict[str, Any]] = None,
        fail_reason_text: Optional[str] = None,
        use_rag: bool = True,
    ) -> Dict[str, Any]:
        logging.info("Searching for relevant papers...")

        filename, _, cited_text = self.retriever.retrieve_reference_via_assistant(synthesized_reagents)
        reference_text = "No relevant document found"
        top_paper = None
        if use_rag and filename != "No relevant document found":
            file_path = (PDF_FOLDER / filename).resolve(strict=False)
            washing_text = self.retriever.retrieve_washing_method(str(file_path))

            if washing_text:
                reference_text = str(file_path)
                cited_text = self.clean_text(washing_text)
                logging.info(f"Selected paper containing the washing method: {reference_text}")
            else:
                logging.warning("❗ Failed to extract washing information from the PDF. Using only the Assistant's Knowledge.")
        else:
            logging.info("❗use_rag=False is set → Ignoring paper information and proceeding with internal reasoning.")
            reference_text = "No relevant document found"

        fail_reason_text = fail_reason_text or "Unknown failure reason."
        previous_failures_text = "Unknown previous failure."
        previous_conditions = "No previous recipe available."
        failed_solutions: Set[Tuple[Any, ...]] = set()
        fail_history = []

        if previous_recipe:
            fail_entry = {
                "Solvents": previous_recipe.get("process", {}).get("Solvents", []),
                "Solvents_Volume": previous_recipe.get("process", {}).get("Solvents_Volume", []),
                "CentrifugationRPM": previous_recipe.get("process", {}).get("CentrifugationRPM", None),
                "CentrifugationTime": previous_recipe.get("process", {}).get("CentrifugationTime", None),
                "FailReason": fail_reason_text,
            }
            fail_history = previous_recipe.get("FailHistory", [])
            fail_history.append(fail_entry)

            previous_failures_text = "\n".join([
                f"- Failure {i+1}: {f.get('FailReason', 'Unknown reason')} "
                f"(Solvents: {f['Solvents']}, RPM: {f['CentrifugationRPM']}, Time: {f['CentrifugationTime']}s)"
                for i, f in enumerate(fail_history)
            ])
            failed_solutions = {tuple(f["Solvents"]) for f in fail_history}
            previous_conditions = (
                f"Previous Recipe:\n- Solvents: {fail_entry['Solvents']}\n"
                f"- Solvents_Volume: {fail_entry['Solvents_Volume']}\n"
                f"- CentrifugationRPM: {fail_entry['CentrifugationRPM']}\n"
                f"- CentrifugationTime: {fail_entry['CentrifugationTime']}"
            )

        if previous_recipe:
            prompt_path = PROMPT_FAILURE
            prompt_case = "Prompt C (Retry)"
        elif use_rag and reference_text != "No relevant document found":
            prompt_path = PROMPT_RAG
            prompt_case = "Prompt A (RAG)"
        else:
            prompt_path = PROMPT_NON
            prompt_case = "Prompt B (Only LLM)"
        logging.info(f"Used Prompt : {prompt_path} ← {prompt_case}")

        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                raw = f.read()
                if raw.strip().startswith("{" + "\n"):
                    template_data = json.loads(raw)
                    query_template = template_data["template"]
                else:
                    query_template = raw
        except Exception as e:
            logging.error(f"Failed to load prompt file: {e}")
            return {"error": "Failed to load the prompt file."}

        system_prompt = SystemMessagePromptTemplate.from_template(query_template)
        chat_prompt = ChatPromptTemplate.from_messages([system_prompt])
        chain: LLMChain = LLMChain(llm=self.llm, prompt=chat_prompt)

        chain_inputs = {
            "synthesis_description": synthesis_description,
            "synthesized_reagents": json.dumps(synthesized_reagents, indent=4),
            "reference_text": reference_text,
            "cited_text": cited_text,
            "fail_reason_text": fail_reason_text,
            "previous_conditions": previous_conditions,
            "previous_failures_text": previous_failures_text,
            "failed_solutions": str(failed_solutions),
        }

        logging.info("Step 6: Calling LLMChain...")
        result = chain.invoke(chain_inputs)

        if isinstance(result, dict):
            raw_response = result.get("text", str(result)).strip()
        else:
            raw_response = str(result).strip()

        try:
            safe_response = self.clean_text(raw_response)
            parsed_response = json.loads(safe_response)

            if previous_recipe:
                parsed_response["FailHistory"] = fail_history
                parsed_response.setdefault("ReasonofAnswer", {})["FailReason"] = fail_reason_text

            return parsed_response

        except json.JSONDecodeError as e:
            logging.error(f"JSON parsing error occurred: {e}")
            with open("failed_response.json", "w", encoding="utf-8") as f:
                f.write(raw_response)
            return {"error": "Failed to parse LLM response. Check failed_response.json."}


    # Test code
if __name__ == "__main__":

    def print_pretty_docs(docs, max_chars: int = 200):
        """Pretty-print a list of documents."""
        if not docs:
            print("❗ No documents found.")
            return

        for i, doc in enumerate(docs, 1):
            file_path = doc.metadata.get("file_path", "")
            filename = Path(file_path).name
            content = doc.page_content.strip().replace("\n", " ")
            content_summary = content[:max_chars] + "..." if len(content) > max_chars else content

            print(f"📄 [{i}] {filename}")
            print(f"    ┓ 🔢 Length: {len(content)} chars")
            print(f"    ┓ 📜 Preview: {content_summary}\n")    

    retriever = WashingMethodRetrival()
    recipe_generator = RecipeGenerator(retriever)    

    previous_recipe_1 = "./recipe_QD_failed.json"
    with open(previous_recipe_1, "r", encoding="utf-8") as f:
        previous_recipe_data = json.load(f)

    synthesized_reagents = [
        {
            "name": "cadmium oxide",
            "concentration_mol": 2.1,
            "concentration_unit": "mM"
        },
        {
            "name": "oleic acid",
            "concentration_mol": 25,
            "concentration_unit": "mM"
        },
        {
            "name": "1-octanethiol ",
            "concentration_mol": 2.4,
            "concentration_unit": "mM"
        },
        {
            "name": "octadecene",
            "concentration_mol": 6,
            "concentration_unit": "mM"
        },
        {
            "name": "Cd-oleate",
            "volume_mL": 3
        }
    ]

    synthesis_description = (
    'Find the material was synthesized using precursors:'
    )
    failure_reason = "Although effective sedimentation was observed at 3000 RPM for 180 s, a minor residual signal at 535 nm persisted in the PL spectrum."

    recipe = recipe_generator.generate_recipe(
        synthesis_description=synthesis_description,
        synthesized_reagents=synthesized_reagents,
        previous_recipe=previous_recipe_data,
        fail_reason_text=failure_reason,
        use_rag=False
    )

    def save_recipe_to_file(recipe, base_path="generated_recipe_Iridium.json"):
        """🚀 Save the generated recipe to a JSON file."""
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"generated_recipe_{timestamp}.json"
        save_path = os.path.join(os.path.dirname(base_path), file_name)

        try:
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(recipe, f, indent=4, ensure_ascii=False)
            print(f"✅ Recipe saved: {save_path}")
        except Exception as e:
            print(f"❌ Failed to save recipe: {e}")

    OUTPUT_DIR = Path("./results/20250602")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)            
    output_path = OUTPUT_DIR / "recipe_QD_failed.json"
    with open(output_path, "w", encoding="utf-8") as out_f:
        json.dump(recipe, out_f, indent=4, ensure_ascii=False)
