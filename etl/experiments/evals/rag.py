import fire
from langsmith import Client
from datetime import datetime, timedelta
from tqdm import tqdm
from deepeval.test_case import LLMTestCase
from deepeval.dataset import EvaluationDataset
from deepeval.metrics.ragas import RAGASAnswerRelevancyMetric, RAGASFaithfulnessMetric
# from deepeval.metrics import ContextualRelevancyMetric, FaithfulnessMetric, AnswerRelevancyMetric
import datasets
from ragas import evaluate
from ragas.metrics import answer_relevancy, faithfulness, context_relevancy, context_utilization
import json
import csv


class EvaluationProcessor:
    def __init__(self):
        self.client = Client()

    def _get_prompt(self, original_text, content_to_remove):
        """
        Supprime chaque ligne de content_to_remove dans le texte original.

        Paramètres:
        original_text (str): Le texte original contenant les lignes à supprimer.
        content_to_remove (str): Le contenu contenant les lignes à supprimer.

        Retourne:
        str: Le texte original avec les lignes spécifiées supprimées.
        """
        original_lines = original_text.splitlines()
        lines_to_remove = set(content_to_remove.splitlines())

        filtered_lines = [line for line in original_lines if line not in lines_to_remove]
        return '\n'.join(filtered_lines)

    def _format_documents(self, docs):
        formatted_output = ""
        for item in docs:
            formatted_output += item["page_content"] + "\n\n"
        return formatted_output

    def _save_results(self, results, output_format):
        if output_format == 'json':
            with open('results.json', 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=4)
        elif output_format == 'csv':
            keys = results[0].keys()
            with open('results.csv', 'w', newline='', encoding='utf-8') as f:
                dict_writer = csv.DictWriter(f, fieldnames=keys)
                dict_writer.writeheader()
                dict_writer.writerows(results)
        else:
            raise ValueError("Unsupported output format. Please use 'csv' or 'json'.")

    def _process_runs(self, project_name, days=None, run_ids_file=None, output_format='csv'):
        if days:
            start_time = datetime.utcnow() - timedelta(days=days)
            runs = self.client.list_runs(project_name=project_name, start_time=start_time, is_root=True)
        elif run_ids_file:
            with open(run_ids_file, 'r') as file:
                run_ids = [line.strip() for line in file.readlines()]
            runs = self.client.list_runs(project_name=project_name, run_ids=run_ids)
        else:
            raise ValueError("Either 'days' or 'run_ids_file' must be specified.")

        results = []
        for run in tqdm(runs, desc="Processing runs"):
            child_runs = self.client.list_runs(trace_id=run.trace_id)
            for child_run in child_runs:
                if child_run.name == "Retriever":
                    docs = [doc['page_content'] for doc in child_run.outputs['documents']]
                    format_docs = self._format_documents(child_run.outputs['documents'])
                if child_run.name == "ChatOpenAI":
                    if "SystemMessage" in child_run.inputs['messages'][0]['id']:
                        sys_message = child_run.inputs['messages'][0]['kwargs']['content']
            prompt = self._get_prompt(sys_message, format_docs)
            results.append({
                'run_id': run.id,
                'prompt': prompt,
                'question': run.inputs['question'],
                'answer': run.outputs['answer'] if run.outputs is not None else "",
                'formatted_docs': format_docs,
                'chat_history': run.inputs['chat_history'],
                'docs': docs
            })
        return results

    def save_runs(self, project_name, days=None, run_ids_file=None, output_format="csv"):
        results = self._process_runs(project_name, days, run_ids_file)
        self._save_results(results, output_format)

    def ragas_eval(self, project_name, days=None, run_ids_file=None, output_format='csv'):
        results = self._process_runs(project_name, days, run_ids_file)
        ragas_dataset = {"question": [], "answer": [], "ground_truths": [], "contexts": []}

        for result in results:
            ragas_dataset["question"].append(result['question'])
            ragas_dataset["answer"].append(result['answer'])
            ragas_dataset["ground_truths"].append([])
            ragas_dataset["contexts"].append(result['docs'])

        hf_ragas_dataset = datasets.Dataset.from_dict(ragas_dataset)
        evaluation_result = evaluate(
            hf_ragas_dataset,
            raise_exceptions=False,
            metrics=[
                context_relevancy,
                faithfulness,
                answer_relevancy,
                context_utilization
            ]
        )
        df = evaluation_result.to_pandas()
        if output_format == "csv":
            df.to_csv("ragas_evaluation_results.csv", index=False)
        elif output_format == "json":
            df.to_json("ragas_evaluation_results.json", index=False)

    def deepeval(self, project_name, days=None, run_ids_file=None):
        results = self._process_runs(project_name, days, run_ids_file)
        dataset = EvaluationDataset()
        for result in results:
            test_case = LLMTestCase(input=result['question'],
                            actual_output=result['answer'],
                            retrieval_context=result['docs'],
                            )
            dataset.add_test_case(test_case)
        faithfulness =  RAGASFaithfulnessMetric(threshold=0.5)
        relevancy = RAGASAnswerRelevancyMetric()
        dataset.evaluate([faithfulness, relevancy])

if __name__ == '__main__':
    fire.Fire(EvaluationProcessor)
