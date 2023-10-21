import openai
import re
import logging
import json
import PyPDF2

class ResumeParser():
    def __init__(self, OPENAI_API_KEY):
        # set GPT-3 API key from the environment variable
        openai.api_key = OPENAI_API_KEY
        # GPT-3 completion questions
        self.prompt_questions = \
"""Summarize the text below into a JSON with exactly the following structure {basic_info: {first_name, last_name, full_name, email, phone_number, location, portfolio_website_url, linkedin_url, github_main_page_url, university, education_level (BS, MS, or PhD), graduation_year, graduation_month, majors, GPA}, work_experience: [{job_title, company, location, duration, job_summary}], project_experience:[{project_name, project_discription}]}
"""
        # set up this parser's logger
        logging.basicConfig(filename='logs/parser.log', level=logging.DEBUG)
        self.logger = logging.getLogger()

    def pdf2string(self, pdf_path: str) -> str:
        """
        Extract the content of a pdf file to string.
        :param pdf_path: Path to the PDF file.
        :return: PDF content string.
        """
        with open(pdf_path, "rb") as f:
            pdfreader = PyPDF2.PdfReader(f)
            pdf = ''
            for page in pdfreader.pages:
                pdf += page.extract_text()

        # Replace whitespace followed by a comma or period with just a comma.
        pdf_str = re.sub(r'\s[,.]', ',', pdf)

        # Replace multiple consecutive newline characters with a single newline.
        pdf_str = re.sub('[\n]+', '\n', pdf_str)

        # Replace one or more whitespace characters with a single space.
        pdf_str = re.sub(r'[\s]+', ' ', pdf_str)

        # Remove 'http', 'https', and possible '://' from the text.
        pdf_str = re.sub('http[s]?(://)?', '', pdf_str)

        return pdf_str

    def query_completion(self,
                        prompt: str,
                        engine: str = 'text-curie-001',
                        temperature: float = 0.0,
                        max_tokens: int = 100,
                        top_p: int = 1,
                        frequency_penalty: int = 0,
                        presence_penalty: int = 0) -> object:
        """
        Base function for querying GPT-3. 
        Send a request to GPT-3 with the passed-in function parameters and return the response object.
        :param prompt: GPT-3 completion prompt.
        :param engine: The engine, or model, to generate completion.
        :param temperature: Controls the randomnesss. Lower means more deterministic.
        :param max_tokens: Maximum number of tokens to be used for prompt and completion combined.
        :param top_p: Controls diversity via nucleus sampling.
        :param frequency_penalty: How much to penalize new tokens based on their existence in text so far.
        :param presence_penalty: How much to penalize new tokens based on whether they appear in text so far.
        :return: GPT-3 response object
        """
        self.logger.info(f'query_completion: using {engine}')
        estimated_prompt_tokens = int(len(prompt.split()) * 1.6)
        self.logger.info(f'estimated prompt tokens: {estimated_prompt_tokens}')
        estimated_answer_tokens = 2049 - estimated_prompt_tokens
        if estimated_answer_tokens < max_tokens:
            self.logger.warning('estimated_answer_tokens lower than max_tokens, changing max_tokens to %s', estimated_answer_tokens)
        response = openai.completions.create(
            model=engine,
            prompt=prompt,
            temperature=temperature,
            max_tokens=min(4096-estimated_prompt_tokens, max_tokens),
            top_p=top_p,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty
        )
        return response
    
    def query_resume(self, pdf_path: str) -> dict:
        """
        Query GPT-3 for the work experience and / or basic information from the resume at the PDF file path.
        :param pdf_path: Path to the PDF file.
        :return dictionary of resume with keys (basic_info, work_experience).
        """
        resume = {}
        pdf_str = self.pdf2string(pdf_path)
        prompt = self.prompt_questions + '\n' + pdf_str
        max_tokens = 1500
        engine = 'gpt-3.5-turbo-instruct'
        response = self.query_completion(prompt,engine=engine,max_tokens=max_tokens)
        response_text = response.choices[0].text.strip()
        print(response_text)
        try:
            resume = json.loads(response_text)
        except json.JSONDecodeError as e:
            print("Error decoding JSON:", e)
            print("Received response:", response_text)
            return {}
        return resume


