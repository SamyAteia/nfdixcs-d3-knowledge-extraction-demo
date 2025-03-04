import gradio as gr
import google.generativeai as genai
import os
import json
import re
import hashlib
from pdfminer.high_level import extract_text
import traceback
import logging
import pandas as pd




logging.getLogger("pdfminer").setLevel(logging.WARNING)



extraction_questions = [
    {"column_name": "Select a question...", "question": ""},  # Placeholder
    {"column_name":"Keywords", 
     "guideline":"Summary of central concepts and research focus of a study in keywords to be found directly under the abstract", 
     "question": "Extract the keywords of the paper these can be found directly under the abstract."
     },
    {"column_name": "Research Question", 
     "guideline": "Does the paper explicitly state a research question? If yes, please insert the complete question here.", 
     "question": "What is the explicitly stated research question for the paper?" },
    {"column_name": "Goal of the paper", 
     "guideline": "Identify the general research objective that is stated in the paper (e.g., copy and paste from the introduction).", 
     "question": "What is the research goal of the paper?" },
    {"column_name": "Motivation of the Paper", 
     "guideline": "Identify what makes the paper relevant (e.g., copy and paste from the introduction/abstract).", 
     "question": "What motivates the research in the paper or makes it relevant?" },
    {"column_name": "Outcome of the Paper", 
     "guideline": "Identify how the result of the paper advances/influences the field of research (e.g., copy and paste from the introduction/abstract).", 
     "question": "What is the outcome of the research, how does the results advance or influence the field of research?" },
    {"column_name": "Type of inquiry", 
     "guideline": "Formal science: the paper aims to define concepts by the mathematical formulae; interesting properties of these concepts are shown by the help of algorithms, lemmas and logical proofs. Information systems engineering: the paper aims to specify new ways of solving socio-technical problems in the context of Information systems engineering. It formulates a means-ends relationship, for which an approach or a tool is designed. Its application is demonstrated in order to support that It achieves a certain end in a better way.  Scientific study: the paper discusses a socio-technical phenomenon and grounds It in social, psychological or cognitive theory. Hypotheses are deducted from theory and tested using forms of empirical inquiry. Inductive study: the paper aims to formulate a new theory for yet unexplained phenomena. The new theory can be rooted in empirical observations, interviews or analysis of documents and other material. Meta-analysis: the paper reviews existing literature and concepts in order to propose gaps in the research area, in order to define classification schemes, or to compare existing approaches according to certain properties. Industrial application: the paper describes an application of BPM concepts, method or artefacts in one or more industrial domains.", 
     "question": "What type of inquiry does this study employ? Choose one of the following categories, write 'none' if none apply: Formal science: the paper aims to define concepts by the mathematical formulae; interesting properties of these concepts are shown by the help of algorithms, lemmas and logical proofs. Information systems engineering: the paper aims to specify new ways of solving socio-technical problems in the context of Information systems engineering. It formulates a means-ends relationship, for which an approach or a tool is designed. Its application is demonstrated in order to support that It achieves a certain end in a better way.  Scientific study: the paper discusses a socio-technical phenomenon and grounds It in social, psychological or cognitive theory. Hypotheses are deducted from theory and tested using forms of empirical inquiry. Inductive study: the paper aims to formulate a new theory for yet unexplained phenomena. The new theory can be rooted in empirical observations, interviews or analysis of documents and other material. Meta-analysis: the paper reviews existing literature and concepts in order to propose gaps in the research area, in order to define classification schemes, or to compare existing approaches according to certain properties. Industrial application: the paper describes an application of BPM concepts, method or artefacts in one or more industrial domains." },
    {"column_name": "Type of Theory", 
     "guideline": "Specify the type of theory. Formal theory: e.g. Petri nets, mathematics or set theory; recognizable through the use of formal languages and mathematical symbols to model and analyze business processes Social science theory: e.g. individual cognition, behaviour or organizational theory; typically identified through qualitative data, case studies and theoretical discussions of human behaviour and organizational dynamics in business contexts", 
     "question": "What type of theory does the paper refer to? Choose one of the following categories, write 'none' if none apply: Formal theory: e.g. Petri nets, mathematics or set theory; recognizable through the use of formal languages and mathematical symbols to model and analyze business processes. Social science theory: e.g. individual cognition, behaviour or organizational theory; typically identified through qualitative data, case studies and theoretical discussions of human behaviour and organizational dynamics in business contexts" },
    {"column_name": "Emphasis", 
     "guideline": "Is the emphasis of the paper on theory, artefact, both or other?", 
     "question": "Is the emphasis of the paper on theory, artefact, both or other? Artefacts could be an Algorithm, Tool implementation, Prototype, Method, Technique, Approach, Language, Design Concept, Framework, Taxonomy, Model, Concept, Report." },
    {"column_name": "Formal concepts", 
     "guideline": "Are concepts defined using mathematical or logical formulae?", 
     "question": "Are concepts defined using mathematical or logical formulae in this paper?" },
    {"column_name": "Algorithms", 
     "guideline": "Does the paper formally define algorithms?", 
     "question": "Does the paper formally define algorithms?" },
    {"column_name": "Hypothesis", 
     "guideline": "Does the paper explicitly state propositions or hypotheses?", 
     "question": "Does the paper explicitly state propositions or hypotheses?" },
    {"column_name": "Independent Variables", 
     "guideline": "What are explicitly stated main independent variables included in the hypothesis? Specify the key target measures (e.g., complexity, competence, maturity, etc.).", 
     "question": "What are explicitly stated main independent variables included in the hypothesis? Specify the key target measures (e.g., complexity, competence, maturity, etc.)." },
    {"column_name": "Dependent Variables", 
     "guideline": "What are explicitly stated main dependent variables included in the hypothesis? Specify the key target measures (e.g., feasibility, usability, usefulness, adoption, efficiency, effectiveness, accuracy etc.). Specify claimed expected effect (e.g., increase in speed).", 
     "question": "What are explicitly stated main dependent variables included in the hypothesis? Specify the key target measures (e.g., feasibility, usability, usefulness, adoption, efficiency, effectiveness, accuracy etc.). Specify claimed expected effect (e.g., increase in speed)." },
    {"column_name": "Type of Artefact 1", 
     "guideline": "Algorithm: systematic procedure for solving a problem, often pseudo-code or mathematical notation, step-by-step instructions. Tool implementation: description of software or a system; screenshots, system architectures or functional overviews. Prototype: early execution of a product, for demonstrating or testing concepts; descriptive usage scenarios and evaluation results. Method: structured approach or process for carrying out research or practical tasks, clear organization of phases and their purpose. Technique: a specific procedure or approach for carrying out a particular task; detailed descriptions of the implementation steps. Approach: a general strategy or view of how to approach a problem; discussion of the underlying theory and examples of its application. Language: formal notation systems for modeling or analyzing processes; syntax and semantics, often illustrated by examples and diagrams. Design Concept: theoretical foundations and structures of a system or product; conceptual models and their discussion. Framework: structured framework for solving a class of problems, described by components, their relationships and contexts of use. Taxonomy: systematically classifies and organizes elements of a specific area; hierarchical structures and categorization criteria. Model: theoretical or conceptual tool used to describe, analyze, or predict aspects; systematic representation of components and relationships. Concept: innovative concepts or ideas that serve to advance or redefine a field of research; usually includes a discussion of the relevant literature and a description of the concept(s) being addressed. Report: Interesting observations, rules of thumb, but not sufficiently general or systematic to rise to the level of a descriptive model Inside:", 
     "question": "What type of artefact is introduced in this paper? Choose one of the following categories, write 'none' if none apply: Algorithm: systematic procedure for solving a problem, often pseudo-code or mathematical notation, step-by-step instructions. Tool implementation: description of software or a system; screenshots, system architectures or functional overviews. Prototype: early execution of a product, for demonstrating or testing concepts; descriptive usage scenarios and evaluation results. Method: structured approach or process for carrying out research or practical tasks, clear organization of phases and their purpose. Technique: a specific procedure or approach for carrying out a particular task; detailed descriptions of the implementation steps. Approach: a general strategy or view of how to approach a problem; discussion of the underlying theory and examples of its application. Language: formal notation systems for modeling or analyzing processes; syntax and semantics, often illustrated by examples and diagrams. Design Concept: theoretical foundations and structures of a system or product; conceptual models and their discussion. Framework: structured framework for solving a class of problems, described by components, their relationships and contexts of use. Taxonomy: systematically classifies and organizes elements of a specific area; hierarchical structures and categorization criteria. Model: theoretical or conceptual tool used to describe, analyze, or predict aspects; systematic representation of components and relationships. Concept: innovative concepts or ideas that serve to advance or redefine a field of research; usually includes a discussion of the relevant literature and a description of the concept(s) being addressed. Report: Interesting observations, rules of thumb, but not sufficiently general or systematic to rise to the level of a descriptive model Inside." },
     {"column_name": "Research Method 1", 
     "guideline": "(*if type of inquiry is 'industrial application', do not code this section) Formal Proof: Select if a formal proof of an artefact (e.g., algorithm) or proposition (e.g., lemma, theorem) is performed using a formal, well-defined method. Select only if predicate logic, set theory, pi calculus or similar formal methods are used. Survey: Select if the study reports on a survey (using correlational data gathering by means of questionnaires). Lab Experiment: Select if the study reports on a lab experiment (studies that take place within a designed, controlled environment and usually involve special treatments of different groups to contrast the precise relationships among variables). Field Experiment: Select if the study reports on a field experiment conducted in real- world settings. Case Study: Select if the study reports on a case study (a study of cases in single or multiple sites, typically over a period of time and using multiple sources of evidence). Interviews: Select if the study reports on interviews (collection of data from respondents using (semi-) structured protocols, often in person or via phone). Design Science/Engineering: Select if an artefact is designed and provide a brief description (the creation and evaluation of novel artefacts such as constructs, methods, models or instantiations). Simulation: Select if a simulation of an artefact or theory is provided (the examination using fabricated/simulated data). Action Research: Select if a demonstration or evaluation of an artefact or theory is provided through research involving the process of actively participating in an organization change situation whilst conducting research. Illustration: Select if a demonstration of an artefact or theory is provided (the use of an illustrative example or a use case). Literature Analysis: Select when systematically reviewing, analyzing and synthesizing scientific publications, books, articles or other available literature (Description of the search strategy, analysis process, summary of findings, discussion of gaps and trends). Other: Describe type of other method in use (e.g., focus group, expert panel, Delphi study, literature analysis) in comments.", 
     "question": """What research method was used in this paper? Select one or multiple of the following: (Formal Proof, Survey, Lab Experiment, Field Experiment, Case Study, Interviews, Design Science/Engineering, Simulation, Action Research, Illustration,  Literature Analysis, Other)
	 - Formal Proof: Select if a formal proof of an artefact (e.g., algorithm) or proposition (e.g., lemma, theorem) is performed using a formal, well-defined method. Select only if predicate logic, set theory, pi calculus or similar formal methods are used. 
	 - Survey: Select if the study reports on a survey (using correlational data gathering by means of questionnaires). 
	 - Lab Experiment: Select if the study reports on a lab experiment (studies that take place within a designed, controlled environment and usually involve special treatments of different groups to contrast the precise relationships among variables). 
	 - Field Experiment: Select if the study reports on a field experiment conducted in real- world settings. 
	 - Case Study: Select if the study reports on a case study (a study of cases in single or multiple sites, typically over a period of time and using multiple sources of evidence). 
	 - Interviews: Select if the study reports on interviews (collection of data from respondents using (semi-) structured protocols, often in person or via phone). 
	 - Design Science/Engineering: Select if an artefact is designed and provide a brief description (the creation and evaluation of novel artefacts such as constructs, methods, models or instantiations). 
	 - Simulation: Select if a simulation of an artefact or theory is provided (the examination using fabricated/simulated data). 
	 - Action Research: Select if a demonstration or evaluation of an artefact or theory is provided through research involving the process of actively participating in an organization change situation whilst conducting research. 
	 - Illustration: Select if a demonstration of an artefact or theory is provided (the use of an illustrative example or a use case). 
	 - Literature Analysis: Select when systematically reviewing, analyzing and synthesizing scientific publications, books, articles or other available literature (Description of the search strategy, analysis process, summary of findings, discussion of gaps and trends). 
	 - Other: Describe type of other method in use (e.g., focus group, expert panel, Delphi study, literature analysis)."""}, 
    {"column_name": "Type of data", 
     "guideline": "Was the underlying data recorded in a real environment or generated synthetically?", 
     "question": "Was the underlying data recorded in a real environment or generated synthetically?" },
    {"column_name": "Total participants count", 
     "guideline": "How many participants does the data set contain?(Only in Management Tracks)", 
     "question": "How many participants where in the study?" },
    {"column_name": "Students Count", 
     "guideline": "Are students used as participants? Specify sample size(s). (Only in Management Tracks) Please enter only integer values here.", 
     "question": "How many of the participants in the study if any, where students?" },
    {"column_name": "Practitioners Count", 
     "guideline": "Are practitioners used as participants? Specify sample size(s). (Only in Management Tracks) Please enter only integer values here.", 
     "question": "How many of the participants in the study if any, where practitioners?" },
    #{"column_name": "Data format 1", "guideline": "In which format is the data used available?", "question": "" }, not extractable, context information
    {"column_name": "Data accessibility", 
     "guideline": "Is the data made available? Yes, in the paper (e.g. as an appendix, or as table with questions asked/surveyed, or link to a website or technical report) Yes, via reference (e.g. contact to authors or named data set) No, not provided", 
     "question": "Is the data made available? Yes, in the paper (e.g. as an appendix, or as table with questions asked/surveyed, or link to a website or technical report) Yes, via reference (e.g. contact to authors or named data set) No, not provided." },
    {"column_name": "Material accessibility", 
     "guideline": "Are research materials (e.g. survey instrument) made available?", 
     "question": "Are research materials (e.g. survey instrument) made available?" },
    {"column_name": "Evaluation Method 1", 
     "guideline": "Verification: Checking correctness and functionality. Recognition in Paper: Identified through technical tests and validation results. Field Experiment: Experiments in real-world environments. Recognition in Paper: Described by the environment and real conditions used. Benchmark: Performance comparison under standardized conditions. Recognition in Paper: Use of performance indicators and comparative data. Grounded Theory: Qualitative theory building from data. Recognition in Paper: Iterative data collection and analysis. Argumentation: Logical arguments to support or refute hypotheses. Recognition in Paper: Structured discussion of theses. Controlled Experiment: Experiment with control groups and randomization. Recognition in Paper: Descriptions of the design and control mechanisms. Data Science: Analysis of large data sets using statistical techniques. Recognition in Paper: Use of data analysis methods and models. Focus Group: Group discussions on specific topics. Recognition in Paper: Descriptions of group composition and discussion topics. Questionnaire: Standardized questions for data collection. Recognition in Paper: Use and analysis of questionnaires. Interview: Interviews for detailed information gathering. Recognition in Paper: Descriptions of interview techniques and participants. Motivating Example: Use cases to demonstrate research relevance. Recognition in Paper: Illustrative examples in the paper. Technical Experiment: Testing technical hypotheses in a controlled environment. Recognition in Paper: Detailed description of the setup. Case Study: Detailed examination of specific cases. Recognition in Paper: Extensive case description and context analysis.",
     "question": """What evaluation method was used in this paper? Select one or multiple of the following: (Verification, Field Experiment, Benchmark, Grounded Theory, Argumentation, Controlled Experiment, Data Science, Focus Group, Questionnaire, Interview, Motivating Example, Technical Experiment, Case Study)
	 - Verification: Checking correctness and functionality. Recognition in Paper: Identified through technical tests and validation results. 
	 - Field Experiment: Experiments in real-world environments. Recognition in Paper: Described by the environment and real conditions used. 
	 - Benchmark: Performance comparison under standardized conditions. Recognition in Paper: Use of performance indicators and comparative data. 
	 - Grounded Theory: Qualitative theory building from data. Recognition in Paper: Iterative data collection and analysis. 
	 - Argumentation: Logical arguments to support or refute hypotheses. Recognition in Paper: Structured discussion of theses. 
	 - Controlled Experiment: Experiment with control groups and randomization. Recognition in Paper: Descriptions of the design and control mechanisms. 
	 - Data Science: Analysis of large data sets using statistical techniques. Recognition in Paper: Use of data analysis methods and models. 
	 - Focus Group: Group discussions on specific topics. Recognition in Paper: Descriptions of group composition and discussion topics. 
	 - Questionnaire: Standardized questions for data collection. Recognition in Paper: Use and analysis of questionnaires. 
	 - Interview: Interviews for detailed information gathering. Recognition in Paper: Descriptions of interview techniques and participants. 
	 - Motivating Example: Use cases to demonstrate research relevance. Recognition in Paper: Illustrative examples in the paper. 
	 - Technical Experiment: Testing technical hypotheses in a controlled environment. Recognition in Paper: Detailed description of the setup. 
	 - Case Study: Detailed examination of specific cases. Recognition in Paper: Extensive case description and context analysis.'""" },   
    {"column_name": "Threats to Validity 1", 
     "guideline": "External Validity: Understanding: Concerns whether the study results can be generalized to other contexts or situations beyond the study settings. Recognition in Paper: Often addressed in discussions about the generalizability of the results or through the use of diverse settings and groups in the study. Internal Validity: Understanding: Measures the reliability of the study results regarding causality; that is, whether the observed effects were actually caused by the intended causes and not by external factors. Recognition in Paper: Look for discussions about the control of confounding factors and the direct link between variables. Construct Validity: Understanding: Checks whether the study actually measures what it claims to measure. It refers to how well the theory and the measurements of the variables are connected. Recognition in Paper: Often addressed through the validation of measurement instruments used and the theoretical justification of the relationships between variables. Confirmability: Understanding: Deals with the objectivity of the research findings. The results should be shaped by the data and not by the biases of the researchers. Recognition in Paper: Check if researchers demonstrate transparency in their methods and disclose their subjective judgments. Repeatability: Understanding: Refers to whether the study can be repeated under the same conditions with the same methods and yield consistent results. Recognition in Paper: Look for detailed method descriptions that would allow other researchers to replicate the study.", 
     "question": "Can any threats to validity be found in the paper? Look for the following: External Validity: Understanding: Concerns whether the study results can be generalized to other contexts or situations beyond the study settings. Recognition in Paper: Often addressed in discussions about the generalizability of the results or through the use of diverse settings and groups in the study. Internal Validity: Understanding: Measures the reliability of the study results regarding causality; that is, whether the observed effects were actually caused by the intended causes and not by external factors. Recognition in Paper: Look for discussions about the control of confounding factors and the direct link between variables. Construct Validity: Understanding: Checks whether the study actually measures what it claims to measure. It refers to how well the theory and the measurements of the variables are connected. Recognition in Paper: Often addressed through the validation of measurement instruments used and the theoretical justification of the relationships between variables. Confirmability: Understanding: Deals with the objectivity of the research findings. The results should be shaped by the data and not by the biases of the researchers. Recognition in Paper: Check if researchers demonstrate transparency in their methods and disclose their subjective judgments. Repeatability: Understanding: Refers to whether the study can be repeated under the same conditions with the same methods and yield consistent results. Recognition in Paper: Look for detailed method descriptions that would allow other researchers to replicate the study." },
    {"column_name": "Existence", 
     "guideline": "Is there an implementation?", 
     "question": "Does an implementation of the artefact exist? Artefacts could be an Algorithm, Tool implementation, Prototype, Method, Technique, Approach, Language, Design Concept, Framework, Taxonomy, Model, Concept, Report." },
    {"column_name": "Availability", 
     "guideline": "Is the implemetation made available? Yes, in the paper (e.g. as an appendix or link to a website or technical report) or via reference (e.g. contact to authors or named implementation) No, not provided", 
     "question": "Is an implementation of the artefact made available? Yes, in the paper (e.g. as an appendix or link to a website or technical report) or via reference (e.g. contact to authors or named implementation) No, not provided. Artefacts could be an Algorithm, Tool implementation, Prototype, Method, Technique, Approach, Language, Design Concept, Framework, Taxonomy, Model, Concept, Report." }
]

# Directory to save the uploaded files
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Function to generate prompt
def get_prompt(question, text):
    return f"""
Extract the information answering the following question from the text:

Question: ```{question}```

Text: ```{text}```

Return a JSON object in the following format: {{ "reasoning": "<think step by step and write down your reasoning>", "context": "<contains all relevant context from the text>", "answer": "<one concise answer to the question for example: yes/no/none, or a word or multiple words>" }}
Try to be concise and limit your reasoning, answer, and the extracted context to max 500 words.
"""

# Read the Excel file as a pandas dataframe
few_shot_examples = pd.read_excel('./Filtered_Few-Shot_Examples_Final_fulltext.xlsx')

def get_few_shot_prompt(question, text, column_name, nr_of_fewshot_examples):
    # Initial zero-shot prompt
    zero_shot_prompt = f"""
Extract the information answering the following question from the text:

Question: ```{question}```

Text: ```{text}```

Return a JSON object in the following format: {{ "reasoning": "<think step by step and write down your reasoning>", "context": "<contains all relevant context from the text>", "answer": "<one concise answer to the question for example: yes/no/none, or a word or multiple words>" }}
Try to be concise and limit your reasoning, answer, and the extracted context to max 500 words.
"""

    # Check if the dataframe 'few_shot_examples' contains the column_name
    if 'few_shot_examples' in globals() and isinstance(few_shot_examples, pd.DataFrame):
        if column_name not in few_shot_examples.columns:
            return zero_shot_prompt
        
        # Construct few-shot prompt using examples from the dataframe
        few_shot_prompt = ""
        example_count = 0

        for _, row in few_shot_examples.iterrows():
            # Stop if we have collected enough examples
            if example_count >= nr_of_fewshot_examples:
                break

            # Skip rows with empty answers
            if pd.isna(row[column_name]) or pd.isna(row['fulltext']):
                continue

            # Append the example to the few-shot prompt
            example_question = question
            example_text = row['fulltext']
            example_answer = row[column_name]

            few_shot_prompt += f"""
Extract the information answering the following question from the text:

##Question: ```{example_question}```

##Text: ```{example_text}```
##Answer:{{"answer": "{example_answer}"}}
"""
            example_count += 1

        # Add the last entry with the given question and text, stopping with ##Answer:
        few_shot_prompt += f"""
Extract the information answering the following question from the text:

##Question: ```{question}```

##Text: ```{text}```
##Answer:"""
        return few_shot_prompt
    
    # If the dataframe or column is not available, return the zero-shot prompt
    return zero_shot_prompt

# Function to clean JSON if the model response is not properly formatted
def find_extract_json(text):
    json_match = re.search(r"\{(?:[^{}]|(?R))*\}", text)
    return json_match.group(0) if json_match else '{}'


def save_file_with_hash(file_bytes):
    file_hash = hashlib.sha256(file_bytes).hexdigest()
    file_path = os.path.join(UPLOAD_DIR, f"{file_hash}.pdf")

    # Only write if file does not exist
    if not os.path.exists(file_path):
        with open(file_path, "wb") as f:
            f.write(file_bytes)

    return file_path

def extract_information(file_path, question, column_name, few_shot_enabled, few_shot_num, model):
    try:
        # Extract the text from the PDF file path
        text = extract_text(file_path)
        
        if len(text.strip()) == 0:
            raise ValueError("Empty PDF content")
        
        # Print the extracted text for debugging
        print("Extracted Text (first 500 chars):", text[:500])  # Printing the first 500 characters for clarity
        
        # Generate the prompt
        if few_shot_enabled:
            prompt = get_few_shot_prompt(question, text, column_name, few_shot_num)
        else:
            prompt = get_prompt(question, text)
        
        # Generate the response from the model
        response = model.generate_content(prompt)
        
        
        try:
            response_data = json.loads(response.text)
        except json.JSONDecodeError as json_error:
            # Attempt to clean and parse the JSON
            cleaned_string = find_extract_json(response.text)
            
            # Print the cleaned JSON string for debugging
            print("Cleaned JSON String:", cleaned_string)
            
            try:
                response_data = json.loads(cleaned_string)
            except Exception as final_json_error:
                print("Final JSON Parsing Error:", final_json_error)
                raise final_json_error  # Re-raise the error to be caught by the outer exception
        if(few_shot_enabled):
            return response_data["answer"], "reasoning not available with few-shot learning yet", "context not available with few-shot learning yet"
        else:
            return response_data["answer"], response_data["reasoning"], response_data["context"]

    except Exception as e:
        # Print detailed error info for debugging
        print("An error occurred. Here’s the full traceback:")
        print(traceback.format_exc())  # Full traceback of the exception
        
        # Print the variables' values for further inspection
        print("File Path:", file_path)
        print("Question:", question)
        print("Extracted Text Length:", len(text) if 'text' in locals() else "No text extracted")
        print("Prompt:", prompt if 'prompt' in locals() else "Prompt not generated")
        print("Response Text:", response.text if 'response' in locals() else "No response generated")
        
        return "ERROR", str(e), "ERROR"




# Convert the question list to a format suitable for dropdown
questions_dropdown = [q["column_name"] for q in extraction_questions]


def handle_file_upload(file):
    if file is not None:
        print("File received, saving...")
        file_path = save_file_with_hash(file)
        print(f"File saved at path: {file_path}")
        return file_path, gr.update(interactive=True)
    else:
        return None, gr.update(interactive=False)


from gradio.themes.utils import colors


# Create a custom color object
my_custom_color = colors.Color(
    c50="#d0d4e0",   # lightest shade
    c100="#a1a9c2",  # lighter shade
    c200="#717fa4",  # slightly darker
    c300="#425485",  # medium-light
    c400="#243a6b",  # darker shade
    c500="#0e2050",  # primary color
    c600="#0c1c47",  # slightly darker
    c700="#0a183e",  # darker
    c800="#081335",  # very dark
    c900="#060e2c",  # almost black
    c950="#040a22"   # extra dark
)
 

# Apply the custom color to the Soft theme
my_theme = gr.themes.Soft(primary_hue=my_custom_color)


with gr.Blocks(theme=my_theme) as demo:
    with gr.Row():
        with gr.Column(scale=0):
            gr.Markdown("![](https://nfdixcs.org/fileadmin/PR/NFDIxCS/NFDIxCS_Logo2024_deepblue_crop.png)")
    gr.Markdown(
    """
# Taskarea D3 - Scientific Text Extraction Demo  
### **Please help us with your feedback by filling out this form: https://forms.gle/fUHhSAhRETqwhitk7**  
    """)

    file_path_state = gr.State()

    with gr.Row():
        file_input = gr.File(label="Upload PDF Document", type="binary")
        
    with gr.Row():
        gr.Markdown("### Select Predefined Question")
        question_dropdown = gr.Dropdown(label="Predefined Questions", choices=questions_dropdown, value="Select a question...")
        displayed_question = gr.Textbox(label="Selected/Editable Question", value="", interactive=True)
        
    
    # Update displayed question based on dropdown
    def update_displayed_question(question_choice):
        # Find the matching question based on column_name
        matching_question = next((q for q in extraction_questions if q["column_name"] == question_choice), None)
        if matching_question:
            return matching_question["question"]
        return ""

    question_dropdown.change(update_displayed_question, inputs=question_dropdown, outputs=[displayed_question])

    # Few-shot learning components
    with gr.Row():
        few_shot_checkbox = gr.Checkbox(label="Enable Few-Shot Learning", value=False)
        few_shot_examples_number = gr.Number(label="Number of Few-Shot Examples", value=0, interactive=False, precision=0, minimum=0, maximum=10)

    # Function to toggle few-shot examples number field
    def toggle_few_shot(interactive):
        return gr.update(interactive=interactive), gr.update(value=0 if not interactive else 3)

    few_shot_checkbox.change(toggle_few_shot, inputs=few_shot_checkbox, outputs=[few_shot_examples_number, few_shot_examples_number])

    # Extract Button, initially disabled
    extract_button = gr.Button("Extract Information", interactive=False, variant="primary")

    # Hint when hovering over disabled button
    hint_html = gr.HTML("<span id='extract-hint'>Please upload a file to enable extraction.</span>")
    
    # Display Area for Results
    with gr.Accordion("Extraction Results", open=True):
        answer_output = gr.Textbox(label="Answer")
        reasoning_output = gr.Textbox(label="Reasoning", interactive=False)
        context_output = gr.Textbox(label="Context", interactive=False)

    def handle_extraction(file_path, displayed_question, few_shot_enabled, few_shot_num, column_name):
        try:
            # Model configuration (instantiate per session)
            genai.configure(api_key=os.environ["API_KEY"])

            generation_config = {
            "temperature": 0,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192,
            "response_mime_type": "application/json",
            }

            model = genai.GenerativeModel(
                model_name='gemini-1.5-flash-002',
                generation_config=generation_config,
                safety_settings={
                    'HATE': 'BLOCK_NONE',
                    'HARASSMENT': 'BLOCK_NONE',
                    'SEXUAL' : 'BLOCK_NONE',
                    'DANGEROUS' : 'BLOCK_NONE'
                },
            )

            # Log the current file path and question
            print(f"Current file path: {file_path}")
            print(f"Displayed question: {displayed_question}")
            print(f"Few-shot learning enabled: {few_shot_enabled}, Number of examples: {few_shot_num}")
            
            actual_question = displayed_question  # Use the content in the editable text box
            
            # Extract information and log result step-by-step
            print("Extracting information from file...")
            answer, reasoning, context = extract_information(
                file_path, actual_question, column_name, few_shot_enabled, few_shot_num, model
            )
            
            # Log extracted details
            print("Extraction complete.")
            print(f"Answer: {answer}")
            print(f"Reasoning: {reasoning}")
            print(f"Context: {context}")
            
            return answer, reasoning, context

        except Exception as e:
            # Log the full traceback for detailed error inspection
            print("Error during the extraction process:")
            print(traceback.format_exc())
            
            # Return error messages in the output fields
            return "ERROR", f"An error occurred: {str(e)}", "ERROR"
        
    # Connect file upload to handle_file_upload and store file path in state
    file_input.change(
        handle_file_upload,
        inputs=file_input,
        outputs=[file_path_state, extract_button],
        concurrency_limit=1,
    )

        
    # Update the button click action to include file_path_state as input
    extract_button.click(
        handle_extraction,
        inputs=[file_path_state, displayed_question, few_shot_checkbox, few_shot_examples_number, question_dropdown],
        outputs=[answer_output, reasoning_output, context_output],
        concurrency_limit=10,
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)